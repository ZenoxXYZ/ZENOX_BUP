"""LLM-backed, deliberately untrusted operator-note interpretation.

This module translates provider-shaped JSON into the raw envelope consumed by
WS-03.  It deliberately does not perform semantic validation or repair.
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import os
import threading
import time
from collections import OrderedDict
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Any, Literal, Protocol

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, ValidationError

from backend.services.interpreter_prompt import PROMPT_VERSION, build_interpretation_prompt

# Ensure local environment variables are loaded if present.
load_dotenv()

logger = logging.getLogger(__name__)

DirectiveType = Literal[
    "solar_reduction",
    "minimum_battery_reserve",
    "no_charge_window",
    "no_discharge_window",
    "max_grid_window",
    "no_op",
]


class ProviderInterpretation(BaseModel):
    """Closed provider DTO, intentionally separate from trusted C-2 Directive."""

    model_config = ConfigDict(extra="forbid")

    note_index: int
    applies: bool
    directive_type: DirectiveType
    hours: list[int]
    factor: float | None
    minimum_energy_kwh: float | None
    max_grid_kwh: float | None
    explanation: str


class ProviderBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interpretations: list[ProviderInterpretation]


class ProviderError(Exception):
    """Sanitized provider failure classification; never expose provider text."""

    def __init__(self, failure_class: str, *, retryable: bool) -> None:
        super().__init__(failure_class)
        self.failure_class = failure_class
        self.retryable = retryable


class ProviderCallable(Protocol):
    def __call__(
        self, prompt: str, schema: type[ProviderBatch], timeout_seconds: float
    ) -> Mapping[str, Any] | ProviderBatch:
        """Return a provider response compatible with ``ProviderBatch``."""


class InterpreterCache:
    """Small, process-local LRU cache with TTL and copy-on-read isolation."""

    def __init__(self, *, max_entries: int = 256, ttl_seconds: float = 600.0) -> None:
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._entries: OrderedDict[str, tuple[float, dict[str, Any]]] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: str) -> dict[str, Any] | None:
        now = time.monotonic()
        with self._lock:
            item = self._entries.get(key)
            if item is None:
                return None
            created_at, value = item
            if now - created_at >= self._ttl_seconds:
                del self._entries[key]
                return None
            self._entries.move_to_end(key)
            return copy.deepcopy(value)

    def set(self, key: str, value: dict[str, Any]) -> None:
        with self._lock:
            self._entries[key] = (time.monotonic(), copy.deepcopy(value))
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)


DEFAULT_CACHE = InterpreterCache()


def _call_with_deadline(call: Callable[[], Any], timeout_seconds: float) -> Any:
    """Return within a real wall-clock deadline even if an SDK stalls."""
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="llm-provider")
    future = executor.submit(call)
    try:
        return future.result(timeout=timeout_seconds)
    except FuturesTimeout as error:
        future.cancel()
        raise ProviderError("timeout", retryable=True) from error
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _classify_provider_exception(error: Exception) -> ProviderError:
    status_code = getattr(error, "status_code", None)
    if status_code is None:
        status_code = getattr(error, "code", None)
    if status_code in {400, 401, 403}:
        return ProviderError("provider_configuration", retryable=False)
    if status_code == 429:
        return ProviderError("rate_limited", retryable=True)
    if isinstance(status_code, int) and status_code >= 500:
        return ProviderError("provider_5xx", retryable=True)
    return ProviderError("provider_network", retryable=True)


def _gemini_response_schema(schema: type[ProviderBatch]) -> dict[str, Any]:
    """Return a Gemini-compatible copy without weakening local DTO validation."""
    response_schema = copy.deepcopy(schema.model_json_schema())

    def remove_unsupported_keys(value: Any) -> None:
        if isinstance(value, dict):
            value.pop("additionalProperties", None)
            for nested_value in value.values():
                remove_unsupported_keys(nested_value)
        elif isinstance(value, list):
            for nested_value in value:
                remove_unsupported_keys(nested_value)

    remove_unsupported_keys(response_schema)
    return response_schema


def _parse_provider_batch(result: Mapping[str, Any] | ProviderBatch) -> ProviderBatch:
    try:
        if isinstance(result, ProviderBatch):
            return result
        return ProviderBatch.model_validate(result)
    except (TypeError, ValidationError) as error:
        raise ProviderError("structured_output_invalid", retryable=True) from error


def _package_interpretations(batch: ProviderBatch) -> dict[str, Any]:
    """Mechanically package DTO fields; WS-03 owns every semantic decision."""
    interpretations: list[dict[str, Any]] = []
    for item in batch.interpretations:
        adjustment: dict[str, Any] | None
        if item.directive_type == "solar_reduction":
            adjustment = {"hours": item.hours, "factor": item.factor}
        elif item.directive_type == "minimum_battery_reserve":
            adjustment = {
                "hours": item.hours,
                "minimum_energy_kwh": item.minimum_energy_kwh,
            }
        elif item.directive_type == "max_grid_window":
            adjustment = {"hours": item.hours, "max_grid_kwh": item.max_grid_kwh}
        elif item.directive_type in {"no_charge_window", "no_discharge_window"}:
            adjustment = {"hours": item.hours}
        else:
            adjustment = None
        interpretations.append(
            {
                "note_index": item.note_index,
                "applies": item.applies,
                "directive_type": item.directive_type,
                "structured_adjustment": adjustment,
                "explanation": item.explanation,
            }
        )
    return {"interpretations": interpretations}


def _degraded_no_ops(notes: Sequence[str]) -> dict[str, Any]:
    return {
        "interpretations": [
            {
                "note_index": index,
                "applies": False,
                "directive_type": "no_op",
                "structured_adjustment": None,
                "explanation": "No operational directive applied.",
            }
            for index, _ in enumerate(notes)
        ]
    }


class Interpreter:
    """Provider ladder and cache for one batched untrusted interpretation call."""

    def __init__(
        self,
        *,
        gemini_provider: ProviderCallable | None = None,
        groq_provider: ProviderCallable | None = None,
        cache: InterpreterCache | None = None,
    ) -> None:
        self._gemini_provider = gemini_provider or self._call_gemini
        self._groq_provider = groq_provider or self._call_groq
        self._cache = cache or DEFAULT_CACHE

    def interpret(
        self,
        notes: Sequence[str],
        *,
        capacity_kwh: float,
        minimum_energy_kwh: float,
    ) -> dict[str, Any]:
        normalized_notes = tuple(note.strip() for note in notes)
        key = self._cache_key(normalized_notes, capacity_kwh, minimum_energy_kwh)
        cached = self._cache.get(key)
        if cached is not None:
            logger.info("interpreter_cache outcome=hit")
            return cached
        logger.info("interpreter_cache outcome=miss")

        normal_prompt = build_interpretation_prompt(
            normalized_notes,
            capacity_kwh=capacity_kwh,
            minimum_energy_kwh=minimum_energy_kwh,
        )
        strict_prompt = build_interpretation_prompt(
            normalized_notes,
            capacity_kwh=capacity_kwh,
            minimum_energy_kwh=minimum_energy_kwh,
            strict=True,
        )

        # F20: Widened timeouts (8.0s / 8.0s / 6.0s)
        result, primary_failure = self._attempt(
            "gemini", "normal", self._gemini_provider, normal_prompt, 8.0
        )
        if primary_failure is not None and primary_failure.retryable:
            result, primary_failure = self._attempt(
                "gemini", "strict_retry", self._gemini_provider, strict_prompt, 8.0
            )
        if result is not None:
            self._cache.set(key, result)
            return copy.deepcopy(result)

        result, secondary_failure = self._attempt(
            "groq", "secondary", self._groq_provider, normal_prompt, 6.0
        )
        if result is not None:
            self._cache.set(key, result)
            return copy.deepcopy(result)

        logger.warning("interpreter_degraded provider_ladder=exhausted")
        return _degraded_no_ops(normalized_notes)

    def _attempt(
        self,
        provider_name: str,
        attempt: str,
        provider: ProviderCallable,
        prompt: str,
        timeout_seconds: float,
    ) -> tuple[dict[str, Any] | None, ProviderError | None]:
        started = time.monotonic()
        try:
            packaged = _package_interpretations(
                _parse_provider_batch(provider(prompt, ProviderBatch, timeout_seconds))
            )
        except ProviderError as error:
            self._log_attempt(provider_name, attempt, error.failure_class, started)
            return None, error
        except Exception as error:  # SDK exceptions must not escape the service.
            classified = _classify_provider_exception(error)
            self._log_attempt(provider_name, attempt, classified.failure_class, started)
            return None, classified
        self._log_attempt(provider_name, attempt, "success", started)
        return packaged, None

    @staticmethod
    def _log_attempt(provider: str, attempt: str, outcome: str, started: float) -> None:
        elapsed_ms = round((time.monotonic() - started) * 1000)
        logger.info(
            "interpreter_attempt provider=%s attempt=%s outcome=%s elapsed_ms=%s",
            provider,
            attempt,
            outcome,
            elapsed_ms,
        )

    @staticmethod
    def _cache_key(
        notes: Sequence[str], capacity_kwh: float, minimum_energy_kwh: float
    ) -> str:
        normalized = json.dumps(
            {
                "prompt_version": PROMPT_VERSION,
                "notes": list(notes),
                "capacity_kwh": capacity_kwh,
                "minimum_energy_kwh": minimum_energy_kwh,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _call_gemini(
        prompt: str, schema: type[ProviderBatch], timeout_seconds: float
    ) -> Mapping[str, Any]:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ProviderError("missing_gemini_key", retryable=False)
        try:
            from google import genai
            from google.genai import types
        except ImportError as error:
            raise ProviderError("gemini_sdk_unavailable", retryable=False) from error
        # F19: Default to gemini-3.1-flash-lite
        model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

        def request() -> Any:
            client = genai.Client(api_key=api_key)
            return client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=_gemini_response_schema(schema),
                    temperature=0,
                    max_output_tokens=700,
                ),
            )

        try:
            response = _call_with_deadline(request, timeout_seconds)
            text = getattr(response, "text", None)
            if not text:
                raise ProviderError("empty_provider_result", retryable=True)
            return json.loads(text)
        except ProviderError:
            raise
        except (json.JSONDecodeError, ValueError) as error:
            raise ProviderError("structured_output_invalid", retryable=True) from error
        except Exception as error:
            raise _classify_provider_exception(error) from error

    @staticmethod
    def _call_groq(
        prompt: str, schema: type[ProviderBatch], timeout_seconds: float
    ) -> Mapping[str, Any]:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ProviderError("missing_groq_key", retryable=False)
        try:
            from groq import Groq
        except ImportError as error:
            raise ProviderError("groq_sdk_unavailable", retryable=False) from error
        # Fix c: Default to openai/gpt-oss-120b
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

        def request() -> Any:
            client = Groq(api_key=api_key, timeout=timeout_seconds)
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "gridwise_provider_batch",
                        "strict": True,
                        "schema": schema.model_json_schema(),
                    },
                },
            )

        try:
            response = _call_with_deadline(request, timeout_seconds)
            text = response.choices[0].message.content
            if not text:
                raise ProviderError("empty_provider_result", retryable=True)
            return json.loads(text)
        except ProviderError:
            raise
        except (AttributeError, IndexError, json.JSONDecodeError, TypeError, ValueError) as error:
            raise ProviderError("structured_output_invalid", retryable=True) from error
        except Exception as error:
            raise _classify_provider_exception(error) from error


def interpret_notes(
    notes_or_request: Any,
    *,
    capacity_kwh: float | None = None,
    minimum_energy_kwh: float | None = None,
) -> dict[str, Any]:
    """Entry point for WS-01 orchestration after rendezvous.

    Accepts either:
    - a ScenarioRequest object (as invoked by backend/routes/optimize.py)
    - a sequence of note strings with keyword arguments capacity_kwh and minimum_energy_kwh
    """
    if hasattr(notes_or_request, "operator_notes") and hasattr(notes_or_request, "battery"):
        notes = notes_or_request.operator_notes
        capacity = float(notes_or_request.battery.capacity_kwh)
        min_energy = float(notes_or_request.battery.minimum_energy_kwh)
    elif isinstance(notes_or_request, dict) and "operator_notes" in notes_or_request and "battery" in notes_or_request:
        notes = notes_or_request["operator_notes"]
        capacity = float(notes_or_request["battery"]["capacity_kwh"])
        min_energy = float(notes_or_request["battery"]["minimum_energy_kwh"])
    else:
        notes = notes_or_request
        capacity = float(capacity_kwh) if capacity_kwh is not None else 0.0
        min_energy = float(minimum_energy_kwh) if minimum_energy_kwh is not None else 0.0

    return Interpreter().interpret(
        notes,
        capacity_kwh=capacity,
        minimum_energy_kwh=min_energy,
    )
