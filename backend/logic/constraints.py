"""Compile trusted C-2 directives into the shared C-3 constraint set."""

from __future__ import annotations

from collections.abc import Sequence

from backend.logic.guardrails import Directive
from backend.schemas.constraints import ConstraintSet, default_constraint_set
from backend.schemas.scenario import ScenarioRequest


def compile_constraints(
    directives: Sequence[Directive], request: ScenarioRequest
) -> ConstraintSet:
    """Apply the frozen per-hour merge rules without sharing replay-oracle code."""
    base = default_constraint_set(request)
    eff_solar = list(base.eff_solar)
    charge_ub = list(base.charge_ub)
    discharge_ub = list(base.discharge_ub)
    grid_ub = list(base.grid_ub)
    energy_lb = list(base.energy_lb)
    solar_factors = [1.0] * len(eff_solar)

    for directive in directives:
        if not directive.applies or directive.structured_adjustment is None:
            continue
        adjustment = directive.structured_adjustment
        hours = adjustment["hours"]
        for hour in hours:
            if directive.directive_type == "solar_reduction":
                solar_factors[hour] = min(solar_factors[hour], adjustment["factor"])
            elif directive.directive_type == "minimum_battery_reserve":
                energy_lb[hour] = max(energy_lb[hour], adjustment["minimum_energy_kwh"])
            elif directive.directive_type == "no_charge_window":
                charge_ub[hour] = 0.0
            elif directive.directive_type == "no_discharge_window":
                discharge_ub[hour] = 0.0
            elif directive.directive_type == "max_grid_window":
                grid_ub[hour] = min(grid_ub[hour], adjustment["max_grid_kwh"])

    for hour, factor in enumerate(solar_factors):
        eff_solar[hour] = base.eff_solar[hour] * factor

    return ConstraintSet(
        eff_solar=tuple(eff_solar),
        charge_ub=tuple(charge_ub),
        discharge_ub=tuple(discharge_ub),
        grid_ub=tuple(grid_ub),
        energy_lb=tuple(energy_lb),
    )
