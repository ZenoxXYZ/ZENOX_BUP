"""WS-04: the 24-hour dispatch as a linear program (`plan.md §4`).

Minimize grid cost subject to the hourly energy balance, the battery's state-of-
charge corridor, its charge and discharge rates, any per-hour grid cap, and
end-of-day neutrality. Everything is continuous and every constraint is linear,
so this is a pure LP with no integer variables -- HiGHS solves it exactly, in
milliseconds, deterministically.

`battery_action` is not a decision variable. It is a label the materializer
reads off the netted solution.

Infeasibility is not handled here. `solve` raises, and the route's ladder
(`plan.md §4c`) retries under base rules and then falls back to the always-valid
plan, so an unsatisfiable directive set can never become a 5xx.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.optimize import linprog

from backend.schemas.constraints import ConstraintSet
from backend.schemas.scenario import HOURS_IN_DAY, ScenarioRequest

#: Variable layout of the 96-element solution vector, by block:
#:     [ 0..23] g -- grid import        [24..47] s -- solar used
#:     [48..71] c -- battery charge     [72..95] d -- battery discharge
GRID, SOLAR, CHARGE, DISCHARGE = (
    slice(0, 24),
    slice(24, 48),
    slice(48, 72),
    slice(72, 96),
)
VARIABLES = 4 * HOURS_IN_DAY


class InfeasibleScenario(RuntimeError):
    """No schedule satisfies this constraint set. The caller descends the ladder."""


def _bound(upper: float) -> tuple[float, float | None]:
    """scipy wants `None` for an unbounded variable, not an infinite float."""
    return (0.0, None if math.isinf(upper) else float(upper))


def solve(
    request: ScenarioRequest, constraints: ConstraintSet
) -> tuple[list[float], list[float], list[float]]:
    """Return `(solar_used, charge, discharge)`, each 24 long, ascending by hour.

    `grid_kwh` is deliberately not returned: the materializer derives it from the
    balance equation so that balance holds exactly rather than to solver
    tolerance (`plan.md §4b`).
    """
    hours = request.hours_ascending()
    battery = request.battery
    demand = np.array([entry.demand_kwh for entry in hours], dtype=float)
    tariff = np.array([entry.tariff_bdt_per_kwh for entry in hours], dtype=float)

    # Objective: only grid import costs anything.
    cost = np.zeros(VARIABLES)
    cost[GRID] = tariff

    eye = np.eye(HOURS_IN_DAY)

    # Hourly balance: g + s + d - c = demand.
    balance = np.zeros((HOURS_IN_DAY, VARIABLES))
    balance[:, GRID] = eye
    balance[:, SOLAR] = eye
    balance[:, DISCHARGE] = eye
    balance[:, CHARGE] = -eye

    # Neutrality: the battery ends the day where it started.
    neutrality = np.zeros((1, VARIABLES))
    neutrality[0, CHARGE] = 1.0
    neutrality[0, DISCHARGE] = -1.0

    a_eq = np.vstack([balance, neutrality])
    b_eq = np.concatenate([demand, [0.0]])

    # State of charge after hour h is initial + cumulative (charge - discharge).
    # Lower triangular ones give that running sum for every hour at once.
    cumulative = np.tril(np.ones((HOURS_IN_DAY, HOURS_IN_DAY)))
    trajectory = np.zeros((HOURS_IN_DAY, VARIABLES))
    trajectory[:, CHARGE] = cumulative
    trajectory[:, DISCHARGE] = -cumulative

    energy_lb = np.array(constraints.energy_lb, dtype=float)
    initial = float(battery.initial_energy_kwh)

    # Upper: trajectory <= capacity - initial.  Lower: -trajectory <= initial - floor.
    a_ub = np.vstack([trajectory, -trajectory])
    b_ub = np.concatenate(
        [
            np.full(HOURS_IN_DAY, float(battery.capacity_kwh) - initial),
            initial - energy_lb,
        ]
    )

    bounds = (
        [_bound(value) for value in constraints.grid_ub]
        + [_bound(value) for value in constraints.eff_solar]
        + [_bound(value) for value in constraints.charge_ub]
        + [_bound(value) for value in constraints.discharge_ub]
    )

    result = linprog(
        cost, A_ub=a_ub, b_ub=b_ub, A_eq=a_eq, b_eq=b_eq, bounds=bounds, method="highs"
    )
    if not result.success:
        raise InfeasibleScenario(result.message)

    solution = np.asarray(result.x, dtype=float)
    return (
        solution[SOLAR].tolist(),
        solution[CHARGE].tolist(),
        solution[DISCHARGE].tolist(),
    )
