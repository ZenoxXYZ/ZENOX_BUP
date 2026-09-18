"""WS-03 constraint compiler: trusted directives to per-hour numeric bounds.

This is deliberately a thin adapter over `backend.logic.replay.compile_constraints`
rather than a second implementation of the same rules. That function already
implements the contract C-3 merge semantics and has been verified end to end:
driving M1's `solve()` and `materialize()` with the bounds it produces, from the
organizer's ground-truth directives, replays clean in Mode B on all ten public
cases at cost ratio 1.0000 (`review.md`, verification log rows 33-36).

Two implementations of one rule set is two chances to disagree, and the merge
rules are exactly where a disagreement would be invisible until the judge ran.
So there is one implementation, and this wires the seam to it.

Merge rules, for the record (contract C-3): reserves take the **maximum**, grid
caps the **minimum**, and two `solar_reduction`s on the same hour take the
**minimum factor** and are never multiplied -- multiplying two independent 0.5s
to 0.25 over-reduces and could tighten the ceiling below what the judge computes.
"""

from __future__ import annotations

from typing import Any

from backend.logic.replay import compile_constraints as _compile_bounds
from backend.schemas.constraints import ConstraintSet
from backend.schemas.scenario import ScenarioRequest

_BOUND_FIELDS = ("eff_solar", "charge_ub", "discharge_ub", "grid_ub", "energy_lb")


def _as_request_dict(request: ScenarioRequest) -> dict[str, Any]:
    """The plain-dict view the oracle expects (contract C-6 takes dicts, not models)."""
    battery = request.battery
    return {
        "hours": [
            {"hour": entry.hour, "solar_kwh": float(entry.solar_kwh)}
            for entry in request.hours_ascending()
        ],
        "battery": {
            "capacity_kwh": float(battery.capacity_kwh),
            "minimum_energy_kwh": float(battery.minimum_energy_kwh),
            "max_charge_kwh_per_hour": float(battery.max_charge_kwh_per_hour),
            "max_discharge_kwh_per_hour": float(battery.max_discharge_kwh_per_hour),
        },
    }


def compile_constraints(
    directives: list[Any] | ScenarioRequest,
    request: ScenarioRequest | list[Any],
) -> ConstraintSet:
    """Compile guardrailed directives into the five per-hour bound arrays.

    The `compiler` seam in `backend/routes/optimize.py` calls this as
    `(directives, request)` while the oracle underneath takes `(request,
    directives)`. Both orders are accepted here, resolved by type rather than by
    position, so a caller cannot silently get it wrong: the two arguments are
    never the same type, so there is nothing to guess at.
    """
    if isinstance(directives, ScenarioRequest):
        directives, request = request, directives  # called as (request, directives)
    if not isinstance(request, ScenarioRequest):
        raise TypeError("compile_constraints needs a ScenarioRequest and a directive list")

    bounds = _compile_bounds(_as_request_dict(request), list(directives))
    return ConstraintSet(**{name: tuple(bounds[name]) for name in _BOUND_FIELDS})
