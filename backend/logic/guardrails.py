"""Deterministic boundary between untrusted interpretations and C-2 directives."""

from __future__ import annotations

import logging
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from backend.schemas.scenario import ScenarioRequest

logger = logging.getLogger(__name__)

DirectiveType = Literal[
    "solar_reduction",
    "minimum_battery_reserve",
    "no_charge_window",
    "no_discharge_window",
    "max_grid_window",
    "no_op",
]

DIRECTIVE_TYPES = frozenset(
    {
        "solar_reduction",
        "minimum_battery_reserve",
        "no_charge_window",
        "no_discharge_window",
        "max_grid_window",
        "no_op",
    }
)

_ADJUSTMENT_KEYS = {
    "solar_reduction": frozenset({"hours", "factor"}),
    "minimum_battery_reserve": frozenset({"hours", "minimum_energy_kwh"}),
    "no_charge_window": frozenset({"hours"}),
    "no_discharge_window": frozenset({"hours"}),
    "max_grid_window": frozenset({"hours", "max_grid_kwh"}),
}


@dataclass(frozen=True)
class Directive:
    """Trusted C-2 directive; response-only explanation text is excluded."""

    note_index: int
    applies: bool
    directive_type: DirectiveType
    structured_adjustment: dict[str, object] | None


def _no_op(note_index: int) -> Directive:
    return Directive(note_index, False, "no_op", None)


def _log(code: str, *, position: int | None = None, note_index: int | None = None) -> None:
    """Emit metadata only; raw model and operator content must never be logged."""
    logger.warning(
        "%s position=%s note_index=%s", code, position, note_index
    )


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _normalised_hours(
    value: object, *, position: int, note_index: int
) -> list[int] | None:
    if not isinstance(value, list) or not value:
        _log("GUARDRAIL_INVALID_HOURS", position=position, note_index=note_index)
        return None
    if any(
        isinstance(hour, bool) or not isinstance(hour, int) or not 0 <= hour <= 23
        for hour in value
    ):
        _log("GUARDRAIL_INVALID_HOURS", position=position, note_index=note_index)
        return None
    result = sorted(set(value))
    if result != value:
        _log("GUARDRAIL_HOURS_SORTED", position=position, note_index=note_index)
    return result


def _validate_actionable(
    entry: Mapping[str, object], *, position: int, note_index: int, directive_type: str, request: ScenarioRequest
) -> Directive:
    applies = entry.get("applies")
    if not isinstance(applies, bool):
        _log("GUARDRAIL_INVALID_APPLIES", position=position, note_index=note_index)
        return _no_op(note_index)

    adjustment = entry.get("structured_adjustment")
    expected_keys = _ADJUSTMENT_KEYS[directive_type]
    if not isinstance(adjustment, Mapping) or set(adjustment) != expected_keys:
        _log("GUARDRAIL_INVALID_ADJUSTMENT", position=position, note_index=note_index)
        return _no_op(note_index)

    hours = _normalised_hours(
        adjustment.get("hours"), position=position, note_index=note_index
    )
    if hours is None:
        return _no_op(note_index)

    clean_adjustment: dict[str, object] = {"hours": hours}
    if directive_type == "solar_reduction":
        factor = adjustment.get("factor")
        if not _is_finite_number(factor) or not 0.0 <= float(factor) <= 1.0:
            _log("GUARDRAIL_INVALID_FACTOR", position=position, note_index=note_index)
            return _no_op(note_index)
        clean_adjustment["factor"] = float(factor)
    elif directive_type == "minimum_battery_reserve":
        reserve = adjustment.get("minimum_energy_kwh")
        if (
            not _is_finite_number(reserve)
            or float(reserve) < 0.0
            or float(reserve) > request.battery.capacity_kwh
        ):
            _log("GUARDRAIL_INVALID_RESERVE", position=position, note_index=note_index)
            return _no_op(note_index)
        clean_adjustment["minimum_energy_kwh"] = float(reserve)
    elif directive_type == "max_grid_window":
        cap = adjustment.get("max_grid_kwh")
        if not _is_finite_number(cap) or float(cap) < 0.0:
            _log("GUARDRAIL_INVALID_GRID_CAP", position=position, note_index=note_index)
            return _no_op(note_index)
        clean_adjustment["max_grid_kwh"] = float(cap)

    if not applies:
        _log("GUARDRAIL_APPLIES_NORMALIZED", position=position, note_index=note_index)
    return Directive(note_index, True, directive_type, clean_adjustment)  # type: ignore[arg-type]


def _validate_entry(entry: Mapping[str, object], *, position: int, note_index: int, request: ScenarioRequest) -> Directive:
    directive_type = entry.get("directive_type")
    if directive_type not in DIRECTIVE_TYPES:
        _log("GUARDRAIL_UNSUPPORTED_TYPE", position=position, note_index=note_index)
        return _no_op(note_index)
    if directive_type == "no_op":
        if entry.get("applies") is not False or entry.get("structured_adjustment") is not None:
            _log("GUARDRAIL_NO_OP_NORMALIZED", position=position, note_index=note_index)
        return _no_op(note_index)
    return _validate_actionable(
        entry,
        position=position,
        note_index=note_index,
        directive_type=directive_type,
        request=request,
    )


def validate_directives(raw: object, request: ScenarioRequest) -> list[Directive]:
    """Repair safe structural defects and degrade each irreparable entry to no-op."""
    note_count = len(request.operator_notes)
    if not isinstance(raw, Mapping) or not isinstance(raw.get("interpretations"), list):
        _log("GUARDRAIL_INVALID_ENVELOPE")
        return [_no_op(index) for index in range(note_count)]

    candidates: dict[int, tuple[int, Mapping[str, object]]] = {}
    duplicates: set[int] = set()
    for position, entry in enumerate(raw["interpretations"]):
        if not isinstance(entry, Mapping):
            _log("GUARDRAIL_DEGRADED", position=position)
            continue
        note_index = entry.get("note_index")
        if (
            isinstance(note_index, bool)
            or not isinstance(note_index, int)
            or not 0 <= note_index < note_count
        ):
            _log("GUARDRAIL_INVALID_INDEX", position=position)
            continue
        if note_index in candidates or note_index in duplicates:
            duplicates.add(note_index)
            _log("GUARDRAIL_DUPLICATE_INDEX", position=position, note_index=note_index)
            continue
        candidates[note_index] = (position, entry)

    directives: list[Directive] = []
    for note_index in range(note_count):
        if note_index in duplicates:
            directives.append(_no_op(note_index))
            continue
        candidate = candidates.get(note_index)
        if candidate is None:
            _log("GUARDRAIL_MISSING_ENTRY", note_index=note_index)
            directives.append(_no_op(note_index))
            continue
        position, entry = candidate
        directives.append(
            _validate_entry(entry, position=position, note_index=note_index, request=request)
        )
    return directives
