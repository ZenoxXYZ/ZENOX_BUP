"""WS-03 deterministic guardrail over untrusted model output.

The interpreter's output is untrusted: it comes from a language model that has
been observed inventing directive type names and mis-shaping parameters. This
module is the only thing standing between that output and the solver, so it
trusts nothing and repairs what it can.

Policy is **repair-first** (`execute.md` D5). A repaired directive still earns
its hour credit; a rejected one forfeits the note *and* invalidates the case on
replay. So a recoverable problem is clamped rather than dropped, and only a
directive that cannot be made meaningful degrades to `no_op`.

Contract: `validate_directives(raw, request) -> list` returning exactly one
entry per operator note, in note order, as the `interpret`/`guardrails` seam in
`backend/routes/optimize.py` requires.

Note on hour lists: a two-element list is **never** re-interpreted as a
`[start, end]` range. `[13, 14]` is genuinely ambiguous between the explicit
pair and the range 13->14, so guessing would silently corrupt a correct answer.
The prompt is responsible for emitting explicit hours; this layer only clamps,
de-duplicates and sorts. See finding F7 in `review.md`.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.schemas.scenario import ScenarioRequest

logger = logging.getLogger(__name__)

HOURS_IN_DAY = 24

#: The six types of `problem.md §5`, plus the explicit no-op.
_APPLICABLE_TYPES = frozenset(
    {
        "solar_reduction",
        "minimum_battery_reserve",
        "no_charge_window",
        "no_discharge_window",
        "max_grid_window",
    }
)

#: Every applicable type needs hours; these need one numeric parameter too.
_NUMERIC_FIELD = {
    "solar_reduction": "factor",
    "minimum_battery_reserve": "minimum_energy_kwh",
    "max_grid_window": "max_grid_kwh",
}


def _no_op(note_index: int, reason: str) -> dict[str, Any]:
    return {
        "note_index": note_index,
        "applies": False,
        "directive_type": "no_op",
        "structured_adjustment": None,
        "explanation": reason,
    }


def _clean_hours(value: Any) -> list[int] | None:
    """Clamp to 0-23, drop non-integers, de-duplicate, sort. None if nothing survives."""
    if not isinstance(value, (list, tuple)):
        return None
    kept: set[int] = set()
    for item in value:
        # bool is an int subclass; a True in an hour list is corruption, not hour 1.
        if isinstance(item, bool):
            continue
        if isinstance(item, int):
            hour = item
        elif isinstance(item, float) and float(item).is_integer():
            hour = int(item)
        else:
            continue
        if 0 <= hour < HOURS_IN_DAY:
            kept.add(hour)
    return sorted(kept) or None


def _clean_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def validate_directives(raw: Any, request: ScenarioRequest) -> list[dict[str, Any]]:
    """Repair untrusted interpreter output into exactly one directive per note."""
    notes = request.operator_notes
    capacity = float(request.battery.capacity_kwh)
    floor = float(request.battery.minimum_energy_kwh)

    entries: list[Any] = []
    if isinstance(raw, dict):
        candidate = raw.get("interpretations")
        if isinstance(candidate, list):
            entries = candidate
    elif isinstance(raw, list):
        entries = raw

    # Entries are keyed by the note_index they declare, not by their position in
    # the list: a model that returns only the second note's directive must not
    # have it applied to the first note. Entries without a usable note_index fall
    # back to their position, and only into a slot nothing has claimed.
    by_note: dict[int, dict[str, Any]] = {}
    unkeyed: list[dict[str, Any]] = []
    for position, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        declared = entry.get("note_index")
        if isinstance(declared, bool) or not isinstance(declared, int):
            unkeyed.append(entry)
        elif 0 <= declared < len(notes) and declared not in by_note:
            by_note[declared] = entry
        else:
            unkeyed.append(entry)
    for slot in range(len(notes)):
        if slot not in by_note and unkeyed:
            by_note[slot] = unkeyed.pop(0)

    out: list[dict[str, Any]] = []
    for index in range(len(notes)):
        entry = by_note.get(index)
        if not isinstance(entry, dict):
            logger.error("note %d: interpreter produced no usable entry", index)
            out.append(_no_op(index, "no directive produced for this note"))
            continue

        dtype = entry.get("directive_type")
        applies = bool(entry.get("applies"))
        explanation = entry.get("explanation") or ""

        if dtype == "no_op" or not applies:
            out.append(_no_op(index, explanation or "note carries no directive"))
            continue

        if dtype not in _APPLICABLE_TYPES:
            # F9: providers invent names such as solar_output_reduction or solar.
            logger.error("note %d: unsupported directive_type %r; degrading", index, dtype)
            out.append(_no_op(index, f"unsupported directive type {dtype!r}"))
            continue

        adjustment = entry.get("structured_adjustment")
        if not isinstance(adjustment, dict):
            logger.error("note %d: %s arrived with no adjustment; degrading", index, dtype)
            out.append(_no_op(index, f"{dtype} arrived without a structured_adjustment"))
            continue

        hours = _clean_hours(adjustment.get("hours"))
        if hours is None:
            logger.error("note %d: %s has no usable hours; degrading", index, dtype)
            out.append(_no_op(index, f"{dtype} had no valid hours"))
            continue
        if hours != adjustment.get("hours"):
            logger.warning("note %d: repaired hours for %s", index, dtype)

        repaired: dict[str, Any] = {"hours": hours}
        field = _NUMERIC_FIELD.get(dtype)
        if field is not None:
            number = _clean_number(adjustment.get(field))
            if number is None:
                logger.error("note %d: %s has no usable %s; degrading", index, dtype, field)
                out.append(_no_op(index, f"{dtype} had no valid {field}"))
                continue
            if field == "factor":
                # Fraction REMAINING, so it must lie in [0, 1] (problem.md §6).
                clamped = min(1.0, max(0.0, number))
            elif field == "minimum_energy_kwh":
                # A reserve above capacity is unsatisfiable; below the floor is a no-op.
                clamped = min(capacity, max(floor, number))
            else:
                clamped = max(0.0, number)
            if clamped != number:
                logger.warning(
                    "note %d: clamped %s %s from %s to %s", index, dtype, field, number, clamped
                )
            repaired[field] = clamped

        out.append(
            {
                "note_index": index,
                "applies": True,
                "directive_type": dtype,
                "structured_adjustment": repaired,
                "explanation": explanation,
            }
        )

    return out
