from __future__ import annotations

import copy
import json
import math
import pathlib

import pytest

from backend.logic.constraints import compile_constraints
from backend.logic.guardrails import Directive, validate_directives
from backend.schemas.constraints import default_constraint_set
from backend.schemas.scenario import ScenarioRequest


CASES = json.loads(
    (pathlib.Path(__file__).parent / "fixtures" / "public_cases.json").read_text()
)["cases"]


def _request() -> ScenarioRequest:
    return ScenarioRequest.model_validate(copy.deepcopy(CASES[0]["input"]))


def _directive(kind: str, adjustment: dict[str, object] | None) -> Directive:
    return Directive(0, kind != "no_op", kind, adjustment)  # type: ignore[arg-type]


def test_baseline_is_shared_default_and_has_exact_lengths() -> None:
    request = _request()
    actual = compile_constraints([_directive("no_op", None)], request)
    assert actual == default_constraint_set(request)
    assert all(len(getattr(actual, name)) == 24 for name in (
        "eff_solar", "charge_ub", "discharge_ub", "grid_ub", "energy_lb"
    ))
    assert math.isinf(actual.grid_ub[0])


def test_each_directive_applies_its_own_bound() -> None:
    request = _request()
    result = compile_constraints(
        [
            _directive("solar_reduction", {"hours": [1], "factor": 0.5}),
            _directive("minimum_battery_reserve", {"hours": [2], "minimum_energy_kwh": 70.0}),
            _directive("no_charge_window", {"hours": [3]}),
            _directive("no_discharge_window", {"hours": [4]}),
            _directive("max_grid_window", {"hours": [5], "max_grid_kwh": 80.0}),
        ],
        request,
    )
    base = default_constraint_set(request)
    assert result.eff_solar[1] == base.eff_solar[1] * 0.5
    assert result.energy_lb[2] == 70.0
    assert result.charge_ub[3] == 0.0
    assert result.discharge_ub[4] == 0.0
    assert result.grid_ub[5] == 80.0


def test_overlap_rules_and_base_minimum_are_deterministic() -> None:
    request = _request()
    result = compile_constraints(
        [
            _directive("minimum_battery_reserve", {"hours": [6], "minimum_energy_kwh": 30.0}),
            _directive("minimum_battery_reserve", {"hours": [6], "minimum_energy_kwh": 90.0}),
            _directive("max_grid_window", {"hours": [7], "max_grid_kwh": 100.0}),
            _directive("max_grid_window", {"hours": [7], "max_grid_kwh": 80.0}),
            _directive("solar_reduction", {"hours": [8], "factor": 0.8}),
            _directive("solar_reduction", {"hours": [8], "factor": 0.5}),
            _directive("no_charge_window", {"hours": [9, 10]}),
            _directive("no_charge_window", {"hours": [10, 11]}),
            _directive("no_discharge_window", {"hours": [12]}),
            _directive("no_discharge_window", {"hours": [12, 13]}),
        ],
        request,
    )
    base = default_constraint_set(request)
    assert result.energy_lb[6] == 90.0
    assert result.grid_ub[7] == 80.0
    assert result.eff_solar[8] == base.eff_solar[8] * 0.5
    assert result.eff_solar[8] != base.eff_solar[8] * 0.4
    assert all(result.charge_ub[h] == 0.0 for h in (9, 10, 11))
    assert all(result.discharge_ub[h] == 0.0 for h in (12, 13))
    assert result.energy_lb[0] == base.energy_lb[0]
    assert result == compile_constraints(copy.deepcopy([
        _directive("minimum_battery_reserve", {"hours": [6], "minimum_energy_kwh": 30.0}),
        _directive("minimum_battery_reserve", {"hours": [6], "minimum_energy_kwh": 90.0}),
        _directive("max_grid_window", {"hours": [7], "max_grid_kwh": 100.0}),
        _directive("max_grid_window", {"hours": [7], "max_grid_kwh": 80.0}),
        _directive("solar_reduction", {"hours": [8], "factor": 0.8}),
        _directive("solar_reduction", {"hours": [8], "factor": 0.5}),
        _directive("no_charge_window", {"hours": [9, 10]}),
        _directive("no_charge_window", {"hours": [10, 11]}),
        _directive("no_discharge_window", {"hours": [12]}),
        _directive("no_discharge_window", {"hours": [12, 13]}),
    ]), request)


def test_fake_ws02_envelope_compiles_to_exact_bounds() -> None:
    request = _request()
    raw = {"interpretations": [
        {"note_index": 0, "applies": True, "directive_type": "solar_reduction", "structured_adjustment": {"hours": [1], "factor": 0.25}},
        {"note_index": 1, "applies": True, "directive_type": "max_grid_window", "structured_adjustment": {"hours": [2], "max_grid_kwh": 77}},
    ]}
    request = request.model_copy(update={"operator_notes": ["one", "two"]})
    constraints = compile_constraints(validate_directives(raw, request), request)
    base = default_constraint_set(request)
    assert constraints.eff_solar[1] == base.eff_solar[1] * 0.25
    assert constraints.grid_ub[2] == 77.0


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_public_truth_rendezvous_replays_clean_at_reference_cost(case: dict) -> None:
    numpy = pytest.importorskip("numpy")
    pytest.importorskip("scipy")
    from backend.logic.materializer import compute_totals, materialize
    from backend.logic.optimizer import solve
    from backend.logic.replay import recomputed_cost, replay
    from backend.schemas.plan import DirectiveInterpretation, OptimizeResponse

    request = ScenarioRequest.model_validate(case["input"])
    truth = case["expected_output"]["directive_interpretation"]
    raw = {"interpretations": [
        {key: entry[key] for key in ("note_index", "applies", "directive_type", "structured_adjustment")}
        for entry in truth
    ]}
    directives = validate_directives(raw, request)
    constraints = compile_constraints(directives, request)
    solar, charge, discharge = solve(request, constraints)
    plan = materialize(request, solar_used=solar, charge=charge, discharge=discharge)
    interpretations = [DirectiveInterpretation(**entry) for entry in truth]
    total_grid, total_cost, peak_grid = compute_totals(plan, request)
    response = OptimizeResponse(
        scenario_id=request.scenario_id,
        directive_interpretation=interpretations,
        hourly_plan=plan,
        total_grid_kwh=total_grid,
        total_cost_bdt=total_cost,
        peak_grid_kwh=peak_grid,
        plan_summary="test",
    ).model_dump(mode="json")
    result = replay(case["input"], response, directives=truth)
    assert result.ok, result.violations
    ours = recomputed_cost(case["input"], response)
    reference = recomputed_cost(case["input"], case["expected_output"])
    assert ours == pytest.approx(reference, abs=0.01)
    assert min(1.0, reference / ours) == pytest.approx(1.0)
