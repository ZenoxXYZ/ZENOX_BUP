from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest
from pydantic import ValidationError

from backend.services.interpreter import (
    Interpreter,
    InterpreterCache,
    ProviderBatch,
    ProviderError,
    _classify_provider_exception,
    _gemini_response_schema,
)
from backend.services.interpreter_prompt import build_interpretation_prompt


def _batch(directive_type: str = "solar_reduction") -> dict[str, Any]:
    return {
        "interpretations": [
            {
                "note_index": 0,
                "applies": directive_type != "no_op",
                "directive_type": directive_type,
                "hours": [11, 12, 13] if directive_type != "no_op" else [],
                "factor": 0.2 if directive_type == "solar_reduction" else None,
                "minimum_energy_kwh": None,
                "max_grid_kwh": None,
                "explanation": "test",
            }
        ]
    }


def test_prompt_contains_capacity_semantics_and_omits_hourly_data() -> None:
    prompt = build_interpretation_prompt(
        ["Solar drops by 80% from 11 AM to 2 PM."],
        capacity_kwh=200,
        minimum_energy_kwh=40,
    )

    assert "80 percent leaves factor 0.2" in prompt
    assert "50 percent of 200 kWh is 100 kWh" in prompt
    assert '"capacity_kwh":200' in prompt
    assert "tariff" not in prompt.lower().split("only available context", 1)[1]


def test_successful_batch_is_cached_without_second_provider_call() -> None:
    calls = 0

    def gemini(prompt: str, schema: object, timeout: float) -> Mapping[str, Any]:
        nonlocal calls
        calls += 1
        assert '"note_index":0' in prompt and '"note_index":1' in prompt
        return {
            "interpretations": _batch()["interpretations"]
            + [{**_batch("no_op")["interpretations"][0], "note_index": 1}]
        }

    interpreter = Interpreter(
        gemini_provider=gemini,
        groq_provider=lambda *_: (_ for _ in ()).throw(AssertionError("unused")),
        cache=InterpreterCache(),
    )
    first = interpreter.interpret(["solar note", "irrelevant note"], capacity_kwh=200, minimum_energy_kwh=40)
    second = interpreter.interpret([" solar note ", "irrelevant note"], capacity_kwh=200, minimum_energy_kwh=40)

    assert calls == 1
    assert first == second
    assert first["interpretations"][0]["structured_adjustment"] == {
        "hours": [11, 12, 13],
        "factor": 0.2,
    }


def test_timeout_retries_gemini_with_stricter_prompt() -> None:
    prompts: list[str] = []

    def gemini(prompt: str, schema: object, timeout: float) -> Mapping[str, Any]:
        prompts.append(prompt)
        if len(prompts) == 1:
            raise ProviderError("timeout", retryable=True)
        return _batch("no_charge_window")

    result = Interpreter(gemini_provider=gemini, cache=InterpreterCache()).interpret(
        ["Do not charge."], capacity_kwh=200, minimum_energy_kwh=40
    )

    assert len(prompts) == 2
    assert "Do not add prose outside" in prompts[1]
    assert result["interpretations"][0]["directive_type"] == "no_charge_window"


def test_secondary_provider_runs_after_both_gemini_attempts_fail() -> None:
    gemini_calls = 0

    def gemini(*_: object) -> Mapping[str, Any]:
        nonlocal gemini_calls
        gemini_calls += 1
        raise ProviderError("timeout", retryable=True)

    result = Interpreter(
        gemini_provider=gemini,
        groq_provider=lambda *_: _batch("max_grid_window"),
        cache=InterpreterCache(),
    ).interpret(["Cap grid import."], capacity_kwh=200, minimum_energy_kwh=40)

    assert gemini_calls == 2
    assert result["interpretations"][0]["directive_type"] == "max_grid_window"


def test_all_provider_failures_degrade_every_note_to_ordered_no_op() -> None:
    def fail(*_: object) -> Mapping[str, Any]:
        raise ProviderError("timeout", retryable=True)

    result = Interpreter(gemini_provider=fail, groq_provider=fail, cache=InterpreterCache()).interpret(
        ["first", "second", "third"], capacity_kwh=200, minimum_energy_kwh=40
    )

    assert result == {
        "interpretations": [
            {
                "note_index": index,
                "applies": False,
                "directive_type": "no_op",
                "structured_adjustment": None,
                "explanation": "No operational directive applied.",
            }
            for index in range(3)
        ]
    }


def test_malformed_provider_output_uses_secondary_provider() -> None:
    result = Interpreter(
        gemini_provider=lambda *_: {"interpretations": [{"note_index": 0}]},
        groq_provider=lambda *_: _batch("minimum_battery_reserve"),
        cache=InterpreterCache(),
    ).interpret(["Keep reserve."], capacity_kwh=200, minimum_energy_kwh=40)

    assert result["interpretations"][0]["directive_type"] == "minimum_battery_reserve"


def test_gemini_schema_removes_additional_properties_recursively() -> None:
    schema = _gemini_response_schema(ProviderBatch)

    def contains_additional_properties(value: object) -> bool:
        if isinstance(value, dict):
            return "additionalProperties" in value or any(
                contains_additional_properties(nested) for nested in value.values()
            )
        if isinstance(value, list):
            return any(contains_additional_properties(nested) for nested in value)
        return False

    assert not contains_additional_properties(schema)
    assert "additionalProperties" in ProviderBatch.model_json_schema()["$defs"][
        "ProviderInterpretation"
    ]


def test_strict_local_provider_dto_still_rejects_unexpected_fields() -> None:
    payload = _batch()
    payload["interpretations"][0]["unexpected"] = "rejected locally"

    with pytest.raises(ValidationError):
        ProviderBatch.model_validate(payload)


def test_sdk_error_code_400_is_non_retryable_provider_configuration() -> None:
    class CodeOnlyError(Exception):
        code = 400
        status_code = None

    classified = _classify_provider_exception(CodeOnlyError())

    assert classified.failure_class == "provider_configuration"
    assert not classified.retryable


@pytest.mark.parametrize(
    ("directive_type", "factor", "reserve", "grid_cap", "expected_adjustment"),
    [
        ("solar_reduction", 0.2, None, None, {"hours": [11, 12], "factor": 0.2}),
        (
            "minimum_battery_reserve",
            None,
            100.0,
            None,
            {"hours": [11, 12], "minimum_energy_kwh": 100.0},
        ),
        ("no_charge_window", None, None, None, {"hours": [11, 12]}),
        ("no_discharge_window", None, None, None, {"hours": [11, 12]}),
        ("max_grid_window", None, None, 155.0, {"hours": [11, 12], "max_grid_kwh": 155.0}),
        ("no_op", None, None, None, None),
    ],
)
def test_all_supported_provider_types_are_mechanically_packaged(
    directive_type: str,
    factor: float | None,
    reserve: float | None,
    grid_cap: float | None,
    expected_adjustment: dict[str, Any] | None,
) -> None:
    provider_batch = {
        "interpretations": [
            {
                "note_index": 0,
                "applies": directive_type != "no_op",
                "directive_type": directive_type,
                "hours": [] if directive_type == "no_op" else [11, 12],
                "factor": factor,
                "minimum_energy_kwh": reserve,
                "max_grid_kwh": grid_cap,
                "explanation": "test",
            }
        ]
    }
    result = Interpreter(
        gemini_provider=lambda *_: provider_batch,
        cache=InterpreterCache(),
    ).interpret(["note"], capacity_kwh=200, minimum_energy_kwh=40)

    interpretation = result["interpretations"][0]
    assert interpretation["directive_type"] == directive_type
    assert interpretation["structured_adjustment"] == expected_adjustment
