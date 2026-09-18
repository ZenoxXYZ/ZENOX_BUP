"""WS-04 optimizer tests (M1, contract C-7).

The decisive test is Mode B: replay every solved plan against the organizer's
ground-truth directives, which is the judge's own procedure, and compare
recalculated cost against the reference optimum.
"""

from __future__ import annotations

import json
import math
import pathlib

import pytest

from backend.logic.materializer import materialize
from backend.logic.optimizer import InfeasibleScenario, solve
from backend.logic.replay import recomputed_cost, replay
from backend.routes.optimize import _assemble
from backend.schemas.constraints import ConstraintSet, default_constraint_set
from backend.schemas.plan import DirectiveInterpretation
from backend.schemas.scenario import ScenarioRequest

TOLERANCE = 0.01
CASES = json.loads(
    (
        pathlib.Path(__file__).resolve().parents[1]
        / "docs/challenge/BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json"
    ).read_text()
)["cases"]


def _compile_truth(request: ScenarioRequest, directives: list[dict]) -> ConstraintSet:
    """Stand-in for M2's WS-03 compiler, for tests only.

    Applies `plan.md §3`'s merge rules: minimum factor for overlapping solar
    reductions (never multiply), maximum reserve, minimum grid cap.
    """
    base = default_constraint_set(request)
    eff = list(base.eff_solar)
    charge_ub = list(base.charge_ub)
    discharge_ub = list(base.discharge_ub)
    grid_ub = list(base.grid_ub)
    energy_lb = list(base.energy_lb)
    factors: dict[int, float] = {}

    for directive in directives:
        if not directive.get("applies"):
            continue
        kind = directive["directive_type"]
        adjustment = directive["structured_adjustment"] or {}
        for hour in adjustment.get("hours", []):
            if kind == "solar_reduction":
                factors[hour] = min(factors.get(hour, 1.0), float(adjustment["factor"]))
            elif kind == "minimum_battery_reserve":
                energy_lb[hour] = max(
                    energy_lb[hour], float(adjustment["minimum_energy_kwh"])
                )
            elif kind == "no_charge_window":
                charge_ub[hour] = 0.0
            elif kind == "no_discharge_window":
                discharge_ub[hour] = 0.0
            elif kind == "max_grid_window":
                grid_ub[hour] = min(grid_ub[hour], float(adjustment["max_grid_kwh"]))

    for hour, factor in factors.items():
        eff[hour] = base.eff_solar[hour] * factor

    return ConstraintSet(
        tuple(eff), tuple(charge_ub), tuple(discharge_ub), tuple(grid_ub), tuple(energy_lb)
    )


def _solved(case: dict) -> tuple[ScenarioRequest, dict]:
    request = ScenarioRequest.model_validate(case["input"])
    truth = case["expected_output"]["directive_interpretation"]
    solar, charge, discharge = solve(request, _compile_truth(request, truth))
    plan = materialize(request, solar_used=solar, charge=charge, discharge=discharge)
    interpretations = [DirectiveInterpretation(**entry) for entry in truth]
    response = _assemble(request, interpretations, plan, "test").model_dump(mode="json")
    return request, response


IDS = [case["id"] for case in CASES]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_ground_truth_replay_is_clean(case: dict) -> None:
    """Mode B -- the judge's procedure. Catches misapplication, not just misreading."""
    _, response = _solved(case)
    truth = case["expected_output"]["directive_interpretation"]
    result = replay(case["input"], response, directives=truth)
    assert result.ok, result.violations


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_cost_is_at_least_as_good_as_the_reference(case: dict) -> None:
    _, response = _solved(case)
    ours = recomputed_cost(case["input"], response)
    reference = recomputed_cost(case["input"], case["expected_output"])
    assert min(1.0, reference / ours) >= 0.95

    # Cheaper than the organizer's optimum means a constraint went unapplied.
    # Those cases score zero, so a suspiciously good number is a failure.
    assert ours >= reference - TOLERANCE, "cheaper than reference: check validity"


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_battery_never_charges_and_discharges_in_one_hour(case: dict) -> None:
    _, response = _solved(case)
    for hour in response["hourly_plan"]:
        if hour["battery_action"] == "idle":
            assert hour["battery_kwh"] == 0


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_day_ends_where_it_started(case: dict) -> None:
    request, response = _solved(case)
    assert response["hourly_plan"][23]["battery_energy_after_kwh"] == pytest.approx(
        request.battery.initial_energy_kwh, abs=TOLERANCE
    )


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_solution_is_deterministic(case: dict) -> None:
    first = json.dumps(_solved(case)[1], sort_keys=True)
    second = json.dumps(_solved(case)[1], sort_keys=True)
    assert first == second


def _request() -> ScenarioRequest:
    return ScenarioRequest.model_validate(CASES[0]["input"])


def test_per_hour_grid_cap_is_respected() -> None:
    """The cap is derived from the uncapped solution so it provably binds.

    A hand-picked constant is how a cap test becomes a no-op: if the optimizer
    would have stayed under it anyway, the test passes even when the bound is
    ignored entirely.
    """
    request = _request()
    base = default_constraint_set(request)

    solar, charge, discharge = solve(request, base)
    uncapped = materialize(request, solar_used=solar, charge=charge, discharge=discharge)

    # A cheap early hour, where the optimizer imports extra to charge the battery.
    hour = max(range(6), key=lambda index: uncapped[index].grid_kwh)
    cap = uncapped[hour].grid_kwh * 0.8
    assert uncapped[hour].grid_kwh > cap + TOLERANCE, "cap must actually bind"

    grid_ub = list(base.grid_ub)
    grid_ub[hour] = cap
    constraints = ConstraintSet(
        base.eff_solar, base.charge_ub, base.discharge_ub, tuple(grid_ub), base.energy_lb
    )
    solar, charge, discharge = solve(request, constraints)
    capped = materialize(request, solar_used=solar, charge=charge, discharge=discharge)
    assert capped[hour].grid_kwh <= cap + TOLERANCE


def test_no_charge_window_is_respected() -> None:
    request = _request()
    base = default_constraint_set(request)
    blocked = list(base.charge_ub)
    for hour in (2, 3, 4):
        blocked[hour] = 0.0
    constraints = ConstraintSet(
        base.eff_solar, tuple(blocked), base.discharge_ub, base.grid_ub, base.energy_lb
    )
    solar, charge, discharge = solve(request, constraints)
    plan = materialize(request, solar_used=solar, charge=charge, discharge=discharge)
    for hour in (2, 3, 4):
        assert plan[hour].battery_action != "charge"


def test_reserve_floor_is_respected() -> None:
    request = _request()
    base = default_constraint_set(request)
    floors = list(base.energy_lb)
    for hour in (18, 19, 20):
        floors[hour] = 100.0
    constraints = ConstraintSet(
        base.eff_solar, base.charge_ub, base.discharge_ub, base.grid_ub, tuple(floors)
    )
    solar, charge, discharge = solve(request, constraints)
    plan = materialize(request, solar_used=solar, charge=charge, discharge=discharge)
    for hour in (18, 19, 20):
        assert plan[hour].battery_energy_after_kwh >= 100.0 - TOLERANCE


def test_unsatisfiable_constraints_raise_rather_than_return_nonsense() -> None:
    """The route's ladder depends on this raising (`plan.md §4c`)."""
    request = _request()
    base = default_constraint_set(request)
    constraints = ConstraintSet(
        base.eff_solar,
        base.charge_ub,
        base.discharge_ub,
        (0.0,) * 24,  # no grid import at all, with demand exceeding solar
        base.energy_lb,
    )
    with pytest.raises(InfeasibleScenario):
        solve(request, constraints)


def test_infeasible_scenario_still_serves_a_valid_plan_over_http() -> None:
    """End to end: the ladder turns an impossible directive set into a 200."""
    from fastapi.testclient import TestClient

    from backend.main import app

    payload = json.loads(json.dumps(CASES[0]["input"]))
    payload["battery"]["minimum_energy_kwh"] = payload["battery"]["capacity_kwh"] * 10
    with TestClient(app) as client:
        response = client.post("/optimize-energy", json=payload)
    assert response.status_code == 200
    assert len(response.json()["hourly_plan"]) == 24


def test_unbounded_grid_is_expressed_as_unbounded() -> None:
    """A large finite stand-in for infinity would silently cap the solution."""
    assert math.isinf(default_constraint_set(_request()).grid_ub[0])
