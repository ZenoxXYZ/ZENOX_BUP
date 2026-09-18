"""C-3 `ConstraintSet` (`plan.md §3`): compiler output, optimizer input.

Shared boundary type. M2's constraint compiler (WS-03) produces it, M1's
optimizer (WS-04) consumes it. Both sides import this definition rather than
declaring their own, so the contract cannot drift between them.

`default_constraint_set` is the no-directives baseline: every field at the value
`plan.md §3` gives as its default. It keeps WS-04 unblocked while WS-03 is still
in flight, and it is also the second rung of the infeasibility ladder
(`plan.md §4c`) -- a solve under base rules only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from backend.schemas.scenario import HOURS_IN_DAY, ScenarioRequest


@dataclass(frozen=True)
class ConstraintSet:
    """Five per-hour arrays, each of length 24."""

    eff_solar: tuple[float, ...]
    charge_ub: tuple[float, ...]
    discharge_ub: tuple[float, ...]
    grid_ub: tuple[float, ...]
    energy_lb: tuple[float, ...]

    def __post_init__(self) -> None:
        for name in (
            "eff_solar",
            "charge_ub",
            "discharge_ub",
            "grid_ub",
            "energy_lb",
        ):
            values = getattr(self, name)
            if len(values) != HOURS_IN_DAY:
                raise ValueError(f"{name} must have {HOURS_IN_DAY} entries")
            if any(math.isnan(value) for value in values):
                raise ValueError(f"{name} contains NaN")


def default_constraint_set(request: ScenarioRequest) -> ConstraintSet:
    """Baseline bounds for a scenario with no directives applied."""
    hours = request.hours_ascending()
    battery = request.battery
    return ConstraintSet(
        eff_solar=tuple(entry.solar_kwh for entry in hours),
        charge_ub=(battery.max_charge_kwh_per_hour,) * HOURS_IN_DAY,
        discharge_ub=(battery.max_discharge_kwh_per_hour,) * HOURS_IN_DAY,
        grid_ub=(math.inf,) * HOURS_IN_DAY,
        energy_lb=(battery.minimum_energy_kwh,) * HOURS_IN_DAY,
    )
