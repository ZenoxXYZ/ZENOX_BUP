"""Plan materialization: netting, grid derivation, rounding, totals.

Implements the three rules that keep a solver's floats from becoming an invalid
response:

* `plan.md §4a` -- net simultaneous charge and discharge into one signed action,
  because the schema forbids both in one hour and a lossless LP will produce it.
* `plan.md §4b` -- derive `grid_kwh` from the balance equation rather than
  reporting the solver's own float, so balance holds exactly, not to tolerance.
* C-5 -- round every plan value to 6 decimals *first*, then compute the three
  totals from those rounded values. `hourly_plan` is the declared source of
  truth and totals disagreeing with it is an explicit penalty.

WS-01 uses this for the fallback plan and the response totals; WS-04 adds the LP
that feeds it real charge/discharge vectors.
"""

from __future__ import annotations

from backend.schemas.constraints import ConstraintSet
from backend.schemas.plan import HourPlan
from backend.schemas.scenario import ScenarioRequest

ROUNDING_DECIMALS = 6

#: Below this magnitude a netted battery flow is treated as idle.
IDLE_TOLERANCE = 1e-9

#: Solver noise this far below zero is clamped up; anything lower is a real bug.
NEGATIVE_CLAMP = -1e-9


def _clean(value: float) -> float:
    """Clamp solver noise, round to the contract's precision, kill negative zero."""
    if NEGATIVE_CLAMP < value < 0.0:
        value = 0.0
    return round(value, ROUNDING_DECIMALS) + 0.0


def net_battery_flow(charge: float, discharge: float) -> tuple[str, float]:
    """Collapse a same-hour charge and discharge into one action and magnitude.

    Netting is provably equivalent in a lossless model: the balance equation
    shifts by the same amount on both sides and magnitudes only shrink, so rate
    limits still hold. One `+20` where the solver wrote `+50` and `-30`.
    """
    net = charge - discharge
    if net > IDLE_TOLERANCE:
        return "charge", net
    if net < -IDLE_TOLERANCE:
        return "discharge", -net
    return "idle", 0.0


def materialize(
    request: ScenarioRequest,
    *,
    solar_used: list[float],
    charge: list[float],
    discharge: list[float],
) -> list[HourPlan]:
    """Turn raw per-hour solver vectors into the 24-row `hourly_plan`."""
    hours = request.hours_ascending()
    energy = request.battery.initial_energy_kwh
    plan: list[HourPlan] = []

    for index, entry in enumerate(hours):
        action, magnitude = net_battery_flow(charge[index], discharge[index])
        charge_amount = magnitude if action == "charge" else 0.0
        discharge_amount = magnitude if action == "discharge" else 0.0

        # Energy trajectory follows the netted values, not the solver's pair.
        energy = energy + charge_amount - discharge_amount

        grid = entry.demand_kwh + charge_amount - solar_used[index] - discharge_amount

        plan.append(
            HourPlan(
                hour=entry.hour,
                grid_kwh=_clean(grid),
                solar_used_kwh=_clean(solar_used[index]),
                battery_action=action,
                battery_kwh=_clean(magnitude),
                battery_energy_after_kwh=_clean(energy),
            )
        )

    return plan


def compute_totals(
    plan: list[HourPlan], request: ScenarioRequest
) -> tuple[float, float, float]:
    """The three totals, computed from the rounded plan (C-5).

    Returns `(total_grid_kwh, total_cost_bdt, peak_grid_kwh)`.
    """
    tariffs = [entry.tariff_bdt_per_kwh for entry in request.hours_ascending()]
    total_grid = sum(entry.grid_kwh for entry in plan)
    total_cost = sum(entry.grid_kwh * tariff for entry, tariff in zip(plan, tariffs))
    peak_grid = max((entry.grid_kwh for entry in plan), default=0.0)
    return _clean(total_grid), _clean(total_cost), _clean(peak_grid)


def fallback_plan(request: ScenarioRequest, constraints: ConstraintSet) -> list[HourPlan]:
    """The always-valid plan: use the solar available, buy the rest, never move the battery.

    Bottom rung of the infeasibility ladder (`plan.md §4c`). Satisfies balance by
    construction, respects charge/discharge bounds trivially, and is neutral
    because the battery never moves.
    """
    hours = request.hours_ascending()
    solar_used = [
        min(entry.demand_kwh, constraints.eff_solar[index])
        for index, entry in enumerate(hours)
    ]
    idle = [0.0] * len(hours)
    return materialize(request, solar_used=solar_used, charge=idle, discharge=idle)
