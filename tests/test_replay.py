"""Red-green verification of the replay validator.

The validator is the scoring oracle, so it needs proving in both directions:

* **Green** -- the ten public reference schedules are valid by construction, so
  the validator must pass all ten. A flag here means the *validator* is wrong.
* **Red** -- every injected fault must be caught, and caught by the right check.
  A validator that passes everything is worse than none: it manufactures false
  confidence.

One earlier mutation in this suite was a silent no-op (it set two hours to the
values the reference already held) and therefore could never have failed. Each
mutation below asserts it actually changed the response, which is why
``_mutate`` compares before and after.
"""

from __future__ import annotations

import copy
import json
import math
import pathlib

import pytest

from backend.logic.replay import (
    compile_constraints,
    recomputed_cost,
    replay,
    validate_directives,
    validate_request,
)

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "public_cases.json"
CASES = {c["id"]: c for c in json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]}
CASE_IDS = sorted(CASES)

GAP_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "gap_cases.json"
GAP_CASES = {c["id"]: c for c in json.loads(GAP_FIXTURE.read_text(encoding="utf-8"))["cases"]}


def _fix_totals(request: dict, response: dict) -> None:
    """Recompute the three totals so an injected fault stays isolated."""
    tariff = {h["hour"]: h["tariff_bdt_per_kwh"] for h in request["hours"]}
    plan = response["hourly_plan"]
    response["total_grid_kwh"] = sum(p["grid_kwh"] for p in plan)
    response["total_cost_bdt"] = sum(p["grid_kwh"] * tariff[p["hour"]] for p in plan)
    response["peak_grid_kwh"] = max(p["grid_kwh"] for p in plan)


def _mutate(case_id: str, fn, fix_totals: bool = True) -> tuple[dict, dict]:
    """Deep-copy a case, apply a mutation, and assert the mutation did something."""
    case = copy.deepcopy(CASES[case_id])
    request, response = case["input"], case["expected_output"]
    before = json.dumps(response, sort_keys=True)
    fn(request, response)
    if fix_totals:
        _fix_totals(request, response)
    assert json.dumps(response, sort_keys=True) != before, (
        f"mutation for {case_id} changed nothing -- the test could never fail"
    )
    return request, response


# --------------------------------------------------------------------------
# GREEN: the ten reference schedules must validate in both modes
# --------------------------------------------------------------------------


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_reference_schedule_is_valid_mode_a(case_id: str) -> None:
    """Mode A -- replay against the response's own interpretation."""
    case = CASES[case_id]
    result = replay(case["input"], case["expected_output"])
    assert result.ok, f"{case_id} flagged in Mode A:\n{result.report()}"


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_reference_schedule_is_valid_mode_b(case_id: str) -> None:
    """Mode B -- replay against the supplied ground-truth directives."""
    case = CASES[case_id]
    truth = case["expected_output"]["directive_interpretation"]
    result = replay(case["input"], case["expected_output"], directives=truth)
    assert result.ok, f"{case_id} flagged in Mode B:\n{result.report()}"


def test_fixture_covers_all_ten_cases() -> None:
    assert len(CASES) == 10


def test_recomputed_cost_matches_reference_totals() -> None:
    for case_id in CASE_IDS:
        case = CASES[case_id]
        cost = recomputed_cost(case["input"], case["expected_output"])
        assert abs(cost - case["expected_output"]["total_cost_bdt"]) < 0.01, case_id


# --------------------------------------------------------------------------
# RED: physics faults
# --------------------------------------------------------------------------


def test_catches_broken_energy_balance() -> None:
    req, resp = _mutate(
        "SAMPLE-01", lambda q, r: r["hourly_plan"][5].update(grid_kwh=r["hourly_plan"][5]["grid_kwh"] + 10)
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("ENERGY BALANCE" in v for v in result.violations), result.report()


def test_catches_broken_neutrality() -> None:
    req, resp = _mutate(
        "SAMPLE-02",
        lambda q, r: r["hourly_plan"][23].update(
            battery_energy_after_kwh=r["hourly_plan"][23]["battery_energy_after_kwh"] - 5
        ),
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("NEUTRALITY" in v for v in result.violations), result.report()


def test_catches_charge_inside_no_charge_window() -> None:
    def fn(q, r):
        # SAMPLE-02 forbids charging in hours 2, 3 and 4.
        p = r["hourly_plan"][3]
        p.update(battery_action="charge", battery_kwh=10.0, grid_kwh=p["grid_kwh"] + 10.0)

    req, resp = _mutate("SAMPLE-02", fn)
    result = replay(req, resp)
    assert not result.ok
    assert any("no_charge_window" in v for v in result.violations), result.report()


def test_catches_discharge_inside_no_discharge_window() -> None:
    def fn(q, r):
        # SAMPLE-04 forbids discharging in hours 18 and 19.
        p = r["hourly_plan"][18]
        p.update(battery_action="discharge", battery_kwh=10.0, grid_kwh=p["grid_kwh"] - 10.0)

    req, resp = _mutate("SAMPLE-04", fn)
    result = replay(req, resp)
    assert not result.ok
    assert any("no_discharge_window" in v for v in result.violations), result.report()


def test_catches_grid_above_window_cap() -> None:
    # SAMPLE-05 caps grid import at 155 kWh in hours 18, 19 and 20.
    req, resp = _mutate("SAMPLE-05", lambda q, r: r["hourly_plan"][19].update(grid_kwh=200.0))
    result = replay(req, resp)
    assert not result.ok
    assert any("exceeds grid cap" in v for v in result.violations), result.report()


def test_catches_solar_above_effective_solar() -> None:
    # SAMPLE-01 reduces solar to 25% in hours 12 and 13: 180 * 0.25 = 45.
    req, resp = _mutate("SAMPLE-01", lambda q, r: r["hourly_plan"][12].update(solar_used_kwh=180.0))
    result = replay(req, resp)
    assert not result.ok
    assert any("exceeds effective solar" in v for v in result.violations), result.report()


def test_catches_charge_above_rate_limit() -> None:
    req, resp = _mutate(
        "SAMPLE-03",
        lambda q, r: r["hourly_plan"][2].update(battery_action="charge", battery_kwh=999.0),
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("exceeds charge limit" in v for v in result.violations), result.report()


def test_catches_idle_with_nonzero_battery_kwh() -> None:
    req, resp = _mutate("SAMPLE-01", lambda q, r: r["hourly_plan"][0].update(battery_kwh=7.0))
    result = replay(req, resp)
    assert not result.ok
    assert any("idle but battery_kwh" in v for v in result.violations), result.report()


def test_catches_energy_below_active_reserve() -> None:
    """SAMPLE-03 requires >= 100 kWh stored in hours 18, 19 and 20.

    Hour 20 is idle at exactly 100 in the reference. Discharging 50 there (with
    grid reduced by 50 so the balance equation still holds) drives it to 50,
    breaching the directive floor while leaving the balance intact.
    """

    def fn(q, r):
        p = r["hourly_plan"][20]
        p.update(
            battery_action="discharge",
            battery_kwh=50.0,
            grid_kwh=p["grid_kwh"] - 50.0,
            battery_energy_after_kwh=50.0,
        )
        for later in r["hourly_plan"][21:]:
            later["battery_energy_after_kwh"] -= 50.0

    req, resp = _mutate("SAMPLE-03", fn)
    result = replay(req, resp)
    assert not result.ok
    assert any("below active minimum" in v for v in result.violations), result.report()


def test_catches_energy_above_capacity() -> None:
    def fn(q, r):
        p = r["hourly_plan"][5]
        p.update(battery_kwh=60.0, battery_energy_after_kwh=205.0, grid_kwh=p["grid_kwh"] + 5.0)

    req, resp = _mutate("SAMPLE-02", fn)
    result = replay(req, resp)
    assert not result.ok
    assert any("above capacity" in v for v in result.violations), result.report()


def test_catches_altered_totals() -> None:
    req, resp = _mutate(
        "SAMPLE-01",
        lambda q, r: r.update(total_cost_bdt=r["total_cost_bdt"] + 500),
        fix_totals=False,
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("total_cost_bdt" in v for v in result.violations), result.report()


def test_catches_reported_energy_off_trajectory() -> None:
    req, resp = _mutate(
        "SAMPLE-02", lambda q, r: r["hourly_plan"][1].update(battery_energy_after_kwh=999.0)
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("does not match the trajectory" in v for v in result.violations), result.report()


def test_catches_negative_grid() -> None:
    req, resp = _mutate("SAMPLE-01", lambda q, r: r["hourly_plan"][7].update(grid_kwh=-5.0))
    result = replay(req, resp)
    assert not result.ok
    assert any("is negative" in v for v in result.violations), result.report()


def test_cascade_is_suppressed() -> None:
    """A single trajectory slip must not bury the root cause under 20 violations."""
    req, resp = _mutate(
        "SAMPLE-02", lambda q, r: r["hourly_plan"][1].update(battery_energy_after_kwh=999.0)
    )
    result = replay(req, resp)
    assert not result.ok
    assert len(result.violations) <= 4, (
        f"cascade not suppressed, {len(result.violations)} violations:\n{result.report()}"
    )
    assert result.root is not None and "h1" in result.root


# --------------------------------------------------------------------------
# RED: schema and guardrail faults
# --------------------------------------------------------------------------


def test_catches_no_op_with_applies_true() -> None:
    req, resp = _mutate(
        "SAMPLE-01", lambda q, r: r["directive_interpretation"][1].update(applies=True)
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("no_op requires applies=false" in v for v in result.violations), result.report()


def test_catches_no_op_with_non_null_adjustment() -> None:
    req, resp = _mutate(
        "SAMPLE-01",
        lambda q, r: r["directive_interpretation"][1].update(structured_adjustment={"hours": [1]}),
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("structured_adjustment=null" in v for v in result.violations), result.report()


def test_catches_real_directive_with_applies_false() -> None:
    req, resp = _mutate(
        "SAMPLE-02", lambda q, r: r["directive_interpretation"][0].update(applies=False)
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("requires applies=true" in v for v in result.violations), result.report()


def test_catches_missing_note_entry() -> None:
    req, resp = _mutate("SAMPLE-01", lambda q, r: r["directive_interpretation"].pop(1))
    result = replay(req, resp)
    assert not result.ok
    assert any("entries for 2 notes" in v for v in result.violations), result.report()


def test_catches_hours_not_ascending() -> None:
    req, resp = _mutate(
        "SAMPLE-05",
        lambda q, r: r["directive_interpretation"][0]["structured_adjustment"].update(
            hours=[20, 19, 18]
        ),
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("not in ascending order" in v for v in result.violations), result.report()


def test_catches_duplicate_hours() -> None:
    req, resp = _mutate(
        "SAMPLE-02",
        lambda q, r: r["directive_interpretation"][0]["structured_adjustment"].update(
            hours=[2, 2, 4]
        ),
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("duplicates" in v for v in result.violations), result.report()


def test_catches_factor_out_of_range() -> None:
    req, resp = _mutate(
        "SAMPLE-01",
        lambda q, r: r["directive_interpretation"][0]["structured_adjustment"].update(factor=1.5),
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("must be a number in [0,1]" in v for v in result.violations), result.report()


def test_catches_reserve_above_capacity() -> None:
    req, resp = _mutate(
        "SAMPLE-03",
        lambda q, r: r["directive_interpretation"][0]["structured_adjustment"].update(
            minimum_energy_kwh=99999.0
        ),
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("exceeds capacity" in v for v in result.violations), result.report()


def test_catches_unsupported_directive_type() -> None:
    req, resp = _mutate(
        "SAMPLE-02", lambda q, r: r["directive_interpretation"][0].update(directive_type="turbo_mode")
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("unsupported directive_type" in v for v in result.violations), result.report()


def test_catches_scenario_id_not_echoed() -> None:
    req, resp = _mutate("SAMPLE-01", lambda q, r: r.update(scenario_id="WRONG"), fix_totals=False)
    result = replay(req, resp)
    assert not result.ok
    assert any("does not echo" in v for v in result.violations), result.report()


def test_catches_wrong_plan_length() -> None:
    req, resp = _mutate("SAMPLE-01", lambda q, r: r["hourly_plan"].pop(), fix_totals=False)
    result = replay(req, resp)
    assert not result.ok
    assert any("exactly 24 entries" in v for v in result.violations), result.report()


def test_catches_missing_top_level_field() -> None:
    req, resp = _mutate("SAMPLE-01", lambda q, r: r.pop("plan_summary"), fix_totals=False)
    result = replay(req, resp)
    assert not result.ok
    assert any("missing top-level field" in v for v in result.violations), result.report()


def test_catches_bad_battery_action() -> None:
    req, resp = _mutate(
        "SAMPLE-01", lambda q, r: r["hourly_plan"][0].update(battery_action="float"), fix_totals=False
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("not one of" in v for v in result.violations), result.report()


# --------------------------------------------------------------------------
# The mode distinction: Mode B catches what Mode A structurally cannot
# --------------------------------------------------------------------------


def test_mode_b_catches_what_mode_a_cannot() -> None:
    """A plan consistent with a *wrong* interpretation but violating the truth.

    SAMPLE-01's real directive cuts solar to 25% in hours 12 and 13, so effective
    solar at hour 12 is 45 kWh. Here the service reports every note as ``no_op``
    and then uses 90 kWh of solar at hour 12 -- legal under its own (wrong)
    interpretation, since unreduced solar is 180, and the battery action is
    untouched so the trajectory and neutrality still hold.

    Mode A therefore sees nothing wrong. Mode B, replaying against the organizer's
    real directive, catches it. This is the whole reason both modes exist: the
    judge replays against ground truth, not against what we claimed to understand.
    """
    case = copy.deepcopy(CASES["SAMPLE-01"])
    request, response = case["input"], case["expected_output"]
    truth = copy.deepcopy(response["directive_interpretation"])

    response["directive_interpretation"] = [
        {
            "note_index": i,
            "applies": False,
            "directive_type": "no_op",
            "structured_adjustment": None,
            "explanation": "misread as irrelevant",
        }
        for i in range(len(request["operator_notes"]))
    ]
    p = response["hourly_plan"][12]
    p.update(grid_kwh=p["grid_kwh"] - 45.0, solar_used_kwh=p["solar_used_kwh"] + 45.0)
    _fix_totals(request, response)

    mode_a = replay(request, response)
    mode_b = replay(request, response, directives=truth)

    assert mode_a.ok, f"Mode A should be self-consistent here:\n{mode_a.report()}"
    assert not mode_b.ok, "Mode B must catch the ground-truth violation"
    assert any("exceeds effective solar" in v for v in mode_b.violations), mode_b.report()


# ==========================================================================
# WS-05 PART 2: DIRECTIVE COMPILATION & COVERAGE GAP FIXTURE SUITE
# ==========================================================================


def test_gap_fixtures_schema_and_directives_valid() -> None:
    """Assert all 16 coverage gap and paraphrase fixtures are structurally valid."""
    assert len(GAP_CASES) == 16
    for case_id, case in GAP_CASES.items():
        req = case["input"]
        req_violations = validate_request(req)
        assert not req_violations, f"{case_id} request invalid: {req_violations}"

        dirs = case["expected_output"]["directive_interpretation"]
        cap = req["battery"]["capacity_kwh"]
        dir_violations = validate_directives(dirs, len(req["operator_notes"]), cap)
        assert not dir_violations, f"{case_id} directives invalid: {dir_violations}"


def test_compile_constraints_reserves_take_max() -> None:
    """Plan.md C-3: Two overlapping reserves take the maximum reserve, not sum or min."""
    case = GAP_CASES["GAP-10"]
    req = case["input"]
    dirs = case["expected_output"]["directive_interpretation"]

    bounds = compile_constraints(req, dirs)
    # Note 0 requires 60 kWh in [17, 18, 19, 20]
    # Note 1 requires 95 kWh in [19, 20, 21]
    # Base minimum is 40.0
    assert bounds["energy_lb"][17] == 60.0
    assert bounds["energy_lb"][18] == 60.0
    assert bounds["energy_lb"][19] == 95.0, "Must be max(60, 95) = 95"
    assert bounds["energy_lb"][20] == 95.0, "Must be max(60, 95) = 95"
    assert bounds["energy_lb"][21] == 95.0
    assert bounds["energy_lb"][16] == 40.0  # untouched hour retains base min


def test_compile_constraints_grid_caps_take_min() -> None:
    """Plan.md C-3: Two overlapping grid caps take the minimum cap."""
    case = GAP_CASES["GAP-11"]
    req = case["input"]
    dirs = case["expected_output"]["directive_interpretation"]

    bounds = compile_constraints(req, dirs)
    # Note 0 caps at 160 kWh in [18, 19, 20]
    # Note 1 caps at 130 kWh in [19, 20, 21]
    assert bounds["grid_ub"][18] == 160.0
    assert bounds["grid_ub"][19] == 130.0, "Must be min(160, 130) = 130"
    assert bounds["grid_ub"][20] == 130.0, "Must be min(160, 130) = 130"
    assert bounds["grid_ub"][21] == 130.0
    assert bounds["grid_ub"][17] == math.inf  # untouched hour is inf


def test_compile_constraints_solar_reductions_take_min_factor_not_product() -> None:
    """Plan.md C-3: Two overlapping solar reductions take MIN factor, never multiply."""
    case = GAP_CASES["GAP-12"]
    req = case["input"]
    dirs = case["expected_output"]["directive_interpretation"]

    bounds = compile_constraints(req, dirs)
    hours = {h["hour"]: h for h in req["hours"]}
    h13_base = hours[13]["solar_kwh"]  # 220.0

    # Note 0 factor=0.6 in [11, 12, 13] -> 220 * 0.6 = 132.0
    # Note 1 factor=0.4 in [13, 14, 15] -> 220 * 0.4 = 88.0
    # Min factor rule gives 88.0; multiplication would give 220 * 0.24 = 52.8
    assert bounds["eff_solar"][13] == pytest.approx(h13_base * 0.4)
    assert bounds["eff_solar"][13] != pytest.approx(h13_base * 0.6 * 0.4)
    assert bounds["eff_solar"][11] == pytest.approx(hours[11]["solar_kwh"] * 0.6)
    assert bounds["eff_solar"][15] == pytest.approx(hours[15]["solar_kwh"] * 0.4)


def test_compile_constraints_no_charge_window_union() -> None:
    """Plan.md C-3: Overlapping no_charge windows merge as a union of hours."""
    case = GAP_CASES["GAP-13"]
    req = case["input"]
    dirs = case["expected_output"]["directive_interpretation"]

    bounds = compile_constraints(req, dirs)
    # Note 0: [1, 2], Note 1: [2, 3, 4] -> Union is [1, 2, 3, 4]
    for h in [1, 2, 3, 4]:
        assert bounds["charge_ub"][h] == 0.0, f"hour {h} charge_ub should be 0.0"
    assert bounds["charge_ub"][0] == 50.0  # max_charge rate
    assert bounds["charge_ub"][5] == 50.0


def test_compile_constraints_no_discharge_window_union() -> None:
    """Plan.md C-3: Overlapping no_discharge windows merge as a union of hours."""
    case = GAP_CASES["GAP-14"]
    req = case["input"]
    dirs = case["expected_output"]["directive_interpretation"]

    bounds = compile_constraints(req, dirs)
    # Note 0: [17, 18], Note 1: [18, 19, 20] -> Union is [17, 18, 19, 20]
    for h in [17, 18, 19, 20]:
        assert bounds["discharge_ub"][h] == 0.0, f"hour {h} discharge_ub should be 0.0"
    assert bounds["discharge_ub"][16] == 50.0
    assert bounds["discharge_ub"][21] == 50.0


def test_compile_constraints_single_hour_windows() -> None:
    """Problem.md §19: Single-hour windows apply bounds strictly to the single hour."""
    case = GAP_CASES["GAP-03"]
    req = case["input"]
    dirs = case["expected_output"]["directive_interpretation"]

    bounds = compile_constraints(req, dirs)
    # no_charge [14]
    assert bounds["charge_ub"][14] == 0.0
    assert bounds["charge_ub"][13] == 50.0
    assert bounds["charge_ub"][15] == 50.0

    # max_grid [19] at 110.0
    assert bounds["grid_ub"][19] == 110.0
    assert bounds["grid_ub"][18] == math.inf
    assert bounds["grid_ub"][20] == math.inf


def test_compile_constraints_factor_extremes_zero_and_one() -> None:
    """Problem.md §19: Factor at exactly 0.0 cuts solar to zero; factor 1.0 preserves forecast."""
    # GAP-04 has factor 0.0 in hours [9, 10]
    case_0 = GAP_CASES["GAP-04"]
    bounds_0 = compile_constraints(case_0["input"], case_0["expected_output"]["directive_interpretation"])
    assert bounds_0["eff_solar"][9] == 0.0
    assert bounds_0["eff_solar"][10] == 0.0
    assert bounds_0["eff_solar"][8] > 0.0

    # GAP-05 has factor 1.0 in hours [11, 12]
    case_1 = GAP_CASES["GAP-05"]
    h_map = {h["hour"]: h for h in case_1["input"]["hours"]}
    bounds_1 = compile_constraints(case_1["input"], case_1["expected_output"]["directive_interpretation"])
    assert bounds_1["eff_solar"][11] == h_map[11]["solar_kwh"]
    assert bounds_1["eff_solar"][12] == h_map[12]["solar_kwh"]


def test_compile_constraints_midnight_crossing_windows() -> None:
    """Problem.md §19: Windows crossing midnight (e.g. [0, 1, 23])."""
    case = GAP_CASES["GAP-06"]
    req = case["input"]
    dirs = case["expected_output"]["directive_interpretation"]

    bounds = compile_constraints(req, dirs)
    # no_discharge [0, 1, 23]
    assert bounds["discharge_ub"][0] == 0.0
    assert bounds["discharge_ub"][1] == 0.0
    assert bounds["discharge_ub"][23] == 0.0
    assert bounds["discharge_ub"][2] == 50.0

    # max_grid [0, 22, 23] at 90.0
    assert bounds["grid_ub"][0] == 90.0
    assert bounds["grid_ub"][22] == 90.0
    assert bounds["grid_ub"][23] == 90.0
    assert bounds["grid_ub"][21] == math.inf


def test_compile_constraints_three_simultaneous_real_directives() -> None:
    """Problem.md §19: Three simultaneous real directives compile without interference."""
    case = GAP_CASES["GAP-01"]
    req = case["input"]
    dirs = case["expected_output"]["directive_interpretation"]

    bounds = compile_constraints(req, dirs)
    # solar_reduction [10, 11, 12] f=0.3
    h_map = {h["hour"]: h for h in req["hours"]}
    for h in [10, 11, 12]:
        assert bounds["eff_solar"][h] == pytest.approx(h_map[h]["solar_kwh"] * 0.3)

    # no_charge [13, 14, 15]
    for h in [13, 14, 15]:
        assert bounds["charge_ub"][h] == 0.0

    # reserve [18, 19, 20, 21] 80.0
    for h in [18, 19, 20, 21]:
        assert bounds["energy_lb"][h] == 80.0


def test_compile_constraints_solar_and_reserve_cooccurrence() -> None:
    """Problem.md §19: solar_reduction combined with minimum_battery_reserve."""
    case = GAP_CASES["GAP-02"]
    req = case["input"]
    dirs = case["expected_output"]["directive_interpretation"]

    bounds = compile_constraints(req, dirs)
    h_map = {h["hour"]: h for h in req["hours"]}

    # solar_reduction [12, 13, 14] f=0.5
    for h in [12, 13, 14]:
        assert bounds["eff_solar"][h] == pytest.approx(h_map[h]["solar_kwh"] * 0.5)

    # reserve [14, 15, 16] 90.0
    for h in [14, 15, 16]:
        assert bounds["energy_lb"][h] == 90.0


# ==========================================================================
# WS-05 PART 2: THE FIVE FAILURE-INJECTION MODES (PROBLEM.MD §15)
# ==========================================================================

# --------------------------------------------------------------------------
# Failure Mode 1: Malformed JSON / missing fields / 25 hours / 4 notes
# --------------------------------------------------------------------------


def test_failure_mode_1_missing_required_request_fields() -> None:
    """Oracle catches missing scenario_id, missing battery, or missing battery fields."""
    base_req = copy.deepcopy(CASES["SAMPLE-01"]["input"])

    # 1. Missing scenario_id
    req1 = copy.deepcopy(base_req)
    del req1["scenario_id"]
    v1 = validate_request(req1)
    assert any("scenario_id" in x for x in v1), f"Expected scenario_id violation, got {v1}"

    # 2. Empty scenario_id
    req2 = copy.deepcopy(base_req)
    req2["scenario_id"] = "   "
    v2 = validate_request(req2)
    assert any("scenario_id" in x for x in v2), f"Expected scenario_id violation, got {v2}"

    # 3. Missing battery object
    req3 = copy.deepcopy(base_req)
    del req3["battery"]
    v3 = validate_request(req3)
    assert any("battery object missing" in x for x in v3), f"Expected missing battery violation, got {v3}"

    # 4. Missing battery field (capacity_kwh)
    req4 = copy.deepcopy(base_req)
    del req4["battery"]["capacity_kwh"]
    v4 = validate_request(req4)
    assert any("battery.capacity_kwh" in x for x in v4), f"Expected capacity violation, got {v4}"

    # 5. Negative battery parameter
    req5 = copy.deepcopy(base_req)
    req5["battery"]["minimum_energy_kwh"] = -10.0
    v5 = validate_request(req5)
    assert any("battery.minimum_energy_kwh" in x for x in v5), f"Expected negative min violation, got {v5}"


def test_failure_mode_1_hours_cardinality_and_duplicates() -> None:
    """Oracle catches 25 hours, 23 hours, non-unique hours, or hour outside 0-23."""
    base_req = copy.deepcopy(CASES["SAMPLE-01"]["input"])

    # 1. 25 hours
    req1 = copy.deepcopy(base_req)
    extra_h = copy.deepcopy(req1["hours"][0])
    extra_h["hour"] = 24
    req1["hours"].append(extra_h)
    v1 = validate_request(req1)
    assert any("exactly 24 entries" in x for x in v1), f"Expected 24 entries violation, got {v1}"

    # 2. 23 hours
    req2 = copy.deepcopy(base_req)
    req2["hours"].pop()
    v2 = validate_request(req2)
    assert any("exactly 24 entries" in x for x in v2), f"Expected 24 entries violation, got {v2}"

    # 3. Duplicate hours (two hour 0s, missing hour 23)
    req3 = copy.deepcopy(base_req)
    req3["hours"][23]["hour"] = 0
    v3 = validate_request(req3)
    assert any("0-23, unique" in x for x in v3), f"Expected unique hours violation, got {v3}"


def test_failure_mode_1_notes_cardinality_and_content() -> None:
    """Oracle catches 4 notes, 0 notes, empty note string, or whitespace note."""
    base_req = copy.deepcopy(CASES["SAMPLE-01"]["input"])

    # 1. 4 notes
    req1 = copy.deepcopy(base_req)
    req1["operator_notes"] = ["Note 1", "Note 2", "Note 3", "Note 4"]
    v1 = validate_request(req1)
    assert any("1-3 entries" in x for x in v1), f"Expected 1-3 notes violation, got {v1}"

    # 2. 0 notes
    req2 = copy.deepcopy(base_req)
    req2["operator_notes"] = []
    v2 = validate_request(req2)
    assert any("1-3 entries" in x for x in v2), f"Expected 1-3 notes violation, got {v2}"

    # 3. Empty note string
    req3 = copy.deepcopy(base_req)
    req3["operator_notes"] = ["Valid note", ""]
    v3 = validate_request(req3)
    assert any("non-empty strings" in x for x in v3), f"Expected non-empty note violation, got {v3}"

    # 4. Whitespace-only note string
    req4 = copy.deepcopy(base_req)
    req4["operator_notes"] = ["   \t\n  "]
    v4 = validate_request(req4)
    assert any("non-empty strings" in x for x in v4), f"Expected non-empty note violation, got {v4}"


def test_failure_mode_1_response_non_dict_or_malformed() -> None:
    """Oracle rejects non-dict responses and responses with malformed shapes."""
    req = CASES["SAMPLE-01"]["input"]

    # 1. Non-dict response (e.g. raw string, list, int)
    res1 = replay(req, "<html>502 Bad Gateway</html>")
    assert not res1.ok
    assert any("must be a JSON object" in v for v in res1.violations)

    res2 = replay(req, ["item1", "item2"])
    assert not res2.ok
    assert any("must be a JSON object" in v for v in res2.violations)

    # 2. Non-dict request
    res3 = replay("not a dict", CASES["SAMPLE-01"]["expected_output"])
    assert not res3.ok
    assert any("must be a JSON object" in v for v in res3.violations)


# --------------------------------------------------------------------------
# Failure Mode 2: LLM provider timeout or 5xx
# --------------------------------------------------------------------------


def test_failure_mode_2_provider_timeout_or_5xx_detected() -> None:
    """Oracle rejects unhandled provider error responses (missing top-level fields)."""
    req = CASES["SAMPLE-01"]["input"]

    # Simulated provider timeout error payload returned as response
    provider_504 = {
        "detail": "Upstream LLM provider timed out after 30.0s",
        "status_code": 504,
    }
    result = replay(req, provider_504)
    assert not result.ok
    assert any("missing top-level field" in v for v in result.violations)
    assert result.root is not None and "missing top-level field" in result.root


def test_failure_mode_2_controlled_provider_degradation_validates() -> None:
    """Plan.md D4: Under provider failure, degradation to no_op satisfies base rules."""
    req = copy.deepcopy(CASES["SAMPLE-01"]["input"])
    ref_resp = copy.deepcopy(CASES["SAMPLE-01"]["expected_output"])

    # Build documented degradation response: all notes degraded to no_op
    degraded_resp = copy.deepcopy(ref_resp)
    degraded_resp["directive_interpretation"] = [
        {
            "note_index": i,
            "applies": False,
            "directive_type": "no_op",
            "structured_adjustment": None,
            "explanation": "Provider failed; note degraded to no_op.",
        }
        for i in range(len(req["operator_notes"]))
    ]
    # Build valid base-rules schedule (e.g. trivial fallback: battery idle all day)
    hours = {h["hour"]: h for h in req["hours"]}
    initial_e = req["battery"]["initial_energy_kwh"]
    trivial_plan = []
    tot_grid = 0.0
    tot_cost = 0.0
    peak_grid = 0.0

    for h in range(24):
        dem = hours[h]["demand_kwh"]
        sol = min(dem, hours[h]["solar_kwh"])
        grid = dem - sol
        tariff = hours[h]["tariff_bdt_per_kwh"]
        tot_grid += grid
        tot_cost += grid * tariff
        peak_grid = max(peak_grid, grid)
        trivial_plan.append({
            "hour": h,
            "grid_kwh": round(grid, 6),
            "solar_used_kwh": round(sol, 6),
            "battery_action": "idle",
            "battery_kwh": 0.0,
            "battery_energy_after_kwh": round(initial_e, 6),
        })

    degraded_resp["hourly_plan"] = trivial_plan
    degraded_resp["total_grid_kwh"] = round(tot_grid, 6)
    degraded_resp["total_cost_bdt"] = round(tot_cost, 6)
    degraded_resp["peak_grid_kwh"] = round(peak_grid, 6)
    degraded_resp["plan_summary"] = "Controlled degradation fallback plan under provider failure."

    result = replay(req, degraded_resp)
    assert result.ok, f"Controlled degradation plan must validate clean in Mode A:\n{result.report()}"


# --------------------------------------------------------------------------
# Failure Mode 3: Model returns unsupported type or broken shape
# --------------------------------------------------------------------------


def test_failure_mode_3_unsupported_directive_type_rejected() -> None:
    """Problem.md §11: Unsupported directive types are flagged and rejected."""
    cap = 200.0
    bad_dirs = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "generator_boost",  # unsupported!
            "structured_adjustment": {"hours": [12, 13]},
            "explanation": "Invalid type.",
        }
    ]
    violations = validate_directives(bad_dirs, 1, cap)
    assert any("unsupported directive_type" in v for v in violations), f"Expected unsupported type violation: {violations}"


def test_failure_mode_3_broken_adjustment_shapes() -> None:
    """Problem.md §11: Injected malformed shapes are caught by guardrails and validator."""
    cap = 200.0

    # 1. Non-ascending hours
    dirs1 = [{
        "note_index": 0, "applies": True, "directive_type": "no_charge_window",
        "structured_adjustment": {"hours": [15, 14]}, "explanation": "",
    }]
    v1 = validate_directives(dirs1, 1, cap)
    assert any("ascending" in x for x in v1), f"Expected ascending violation: {v1}"

    # 2. Duplicate hours
    dirs2 = [{
        "note_index": 0, "applies": True, "directive_type": "no_charge_window",
        "structured_adjustment": {"hours": [14, 14]}, "explanation": "",
    }]
    v2 = validate_directives(dirs2, 1, cap)
    assert any("duplicates" in x for x in v2), f"Expected duplicate violation: {v2}"

    # 3. Factor > 1.0
    dirs3 = [{
        "note_index": 0, "applies": True, "directive_type": "solar_reduction",
        "structured_adjustment": {"hours": [12], "factor": 1.25}, "explanation": "",
    }]
    v3 = validate_directives(dirs3, 1, cap)
    assert any("must be a number in [0,1]" in x for x in v3), f"Expected factor range violation: {v3}"

    # 4. Factor < 0.0
    dirs4 = [{
        "note_index": 0, "applies": True, "directive_type": "solar_reduction",
        "structured_adjustment": {"hours": [12], "factor": -0.1}, "explanation": "",
    }]
    v4 = validate_directives(dirs4, 1, cap)
    assert any("must be a number in [0,1]" in x for x in v4), f"Expected factor range violation: {v4}"

    # 5. Reserve > capacity
    dirs5 = [{
        "note_index": 0, "applies": True, "directive_type": "minimum_battery_reserve",
        "structured_adjustment": {"hours": [18], "minimum_energy_kwh": 250.0}, "explanation": "",
    }]
    v5 = validate_directives(dirs5, 1, cap)
    assert any("exceeds capacity" in x for x in v5), f"Expected reserve > capacity violation: {v5}"

    # 6. Negative max_grid_kwh
    dirs6 = [{
        "note_index": 0, "applies": True, "directive_type": "max_grid_window",
        "structured_adjustment": {"hours": [18], "max_grid_kwh": -50.0}, "explanation": "",
    }]
    v6 = validate_directives(dirs6, 1, cap)
    assert any("max_grid_kwh" in x for x in v6), f"Expected negative grid violation: {v6}"


def test_failure_mode_3_invariant_enforcement() -> None:
    """Problem.md §5: no_op <==> applies=False <==> structured_adjustment=None."""
    cap = 200.0

    # 1. no_op with applies=True
    dirs1 = [{
        "note_index": 0, "applies": True, "directive_type": "no_op",
        "structured_adjustment": None, "explanation": "",
    }]
    v1 = validate_directives(dirs1, 1, cap)
    assert any("no_op requires applies=false" in x for x in v1)

    # 2. no_op with non-null adjustment
    dirs2 = [{
        "note_index": 0, "applies": False, "directive_type": "no_op",
        "structured_adjustment": {"hours": [1]}, "explanation": "",
    }]
    v2 = validate_directives(dirs2, 1, cap)
    assert any("structured_adjustment=null" in x for x in v2)

    # 3. real directive with applies=False
    dirs3 = [{
        "note_index": 0, "applies": False, "directive_type": "no_charge_window",
        "structured_adjustment": {"hours": [2, 3]}, "explanation": "",
    }]
    v3 = validate_directives(dirs3, 1, cap)
    assert any("requires applies=true" in x for x in v3)


# --------------------------------------------------------------------------
# Failure Mode 4: LP infeasible
# --------------------------------------------------------------------------


def test_failure_mode_4_infeasible_schedules_detected() -> None:
    """Problem.md §15: When solver produces an infeasible plan, the oracle catches each breach."""
    # 1. Unmet energy balance breach
    req1, resp1 = _mutate(
        "SAMPLE-01",
        lambda q, r: r["hourly_plan"][10].update(grid_kwh=r["hourly_plan"][10]["grid_kwh"] - 20.0),
        fix_totals=True,
    )
    res1 = replay(req1, resp1)
    assert not res1.ok
    assert any("ENERGY BALANCE" in v for v in res1.violations)

    # 2. Battery reserve floor breach
    req2, resp2 = _mutate(
        "SAMPLE-03",
        lambda q, r: r["hourly_plan"][19].update(
            battery_energy_after_kwh=30.0,
            battery_action="idle",
            battery_kwh=0.0,
        ),
        fix_totals=True,
    )
    res2 = replay(req2, resp2)
    assert not res2.ok
    assert any("below active minimum" in v for v in res2.violations)

    # 3. Neutrality breach
    req3, resp3 = _mutate(
        "SAMPLE-01",
        lambda q, r: r["hourly_plan"][23].update(
            battery_energy_after_kwh=r["hourly_plan"][23]["battery_energy_after_kwh"] + 15.0
        ),
        fix_totals=True,
    )
    res3 = replay(req3, resp3)
    assert not res3.ok
    assert any("NEUTRALITY" in v for v in res3.violations)


def test_failure_mode_4_infeasibility_ladder_fallback_schedule_validates() -> None:
    """Plan.md §4c: Canonical base-rules fallback trivial plan is verified valid by oracle."""
    # Under conflicting or infeasible directives, the service falls back to base rules
    req = copy.deepcopy(CASES["SAMPLE-02"]["input"])
    hours = {h["hour"]: h for h in req["hours"]}
    initial_e = req["battery"]["initial_energy_kwh"]

    # Emit the canonical trivial plan: battery idle, solar = min(demand, solar), grid = demand - solar
    plan = []
    tot_grid = 0.0
    tot_cost = 0.0
    peak_grid = 0.0

    for h in range(24):
        dem = hours[h]["demand_kwh"]
        sol = min(dem, hours[h]["solar_kwh"])
        grid = dem - sol
        tariff = hours[h]["tariff_bdt_per_kwh"]
        tot_grid += grid
        tot_cost += grid * tariff
        peak_grid = max(peak_grid, grid)
        plan.append({
            "hour": h,
            "grid_kwh": round(grid, 6),
            "solar_used_kwh": round(sol, 6),
            "battery_action": "idle",
            "battery_kwh": 0.0,
            "battery_energy_after_kwh": round(initial_e, 6),
        })

    resp = {
        "scenario_id": req["scenario_id"],
        "directive_interpretation": [
            {
                "note_index": 0,
                "applies": False,
                "directive_type": "no_op",
                "structured_adjustment": None,
                "explanation": "Infeasible directives dropped to base rules fallback.",
            }
        ],
        "hourly_plan": plan,
        "total_grid_kwh": round(tot_grid, 6),
        "total_cost_bdt": round(tot_cost, 6),
        "peak_grid_kwh": round(peak_grid, 6),
        "plan_summary": "Trivial base-rules plan guarantees balance and neutrality.",
    }

    result = replay(req, resp)
    assert result.ok, f"Base-rules fallback schedule must validate clean:\n{result.report()}"


# --------------------------------------------------------------------------
# Failure Mode 5: Repeated identical requests / stability / no drift
# --------------------------------------------------------------------------


def test_failure_mode_5_repeated_identical_requests_deterministic() -> None:
    """Problem.md §15: Replay is purely deterministic and stateless across repeated invocations."""
    case = CASES["SAMPLE-01"]
    req = case["input"]
    resp = case["expected_output"]

    req_json_before = json.dumps(req, sort_keys=True)
    resp_json_before = json.dumps(resp, sort_keys=True)

    results = []
    for _ in range(5):
        r = replay(req, resp)
        results.append((r.ok, list(r.violations)))

    # Assert all 5 invocations produced identical results
    assert all(res[0] is True for res in results)
    assert all(res[1] == [] for res in results)

    # Assert neither input was mutated
    assert json.dumps(req, sort_keys=True) == req_json_before, "replay() mutated request object!"
    assert json.dumps(resp, sort_keys=True) == resp_json_before, "replay() mutated response object!"


def test_failure_mode_5_subtle_numerical_drift_detected() -> None:
    """Problem.md §15: Floating-point drift exceeding TOL (0.01) is immediately detected."""
    # Inject a tiny 0.02 kWh drift into total_grid_kwh (exceeding 0.01 tolerance)
    req, resp = _mutate(
        "SAMPLE-01",
        lambda q, r: r.update(total_grid_kwh=r["total_grid_kwh"] + 0.02),
        fix_totals=False,
    )
    result = replay(req, resp)
    assert not result.ok
    assert any("total_grid_kwh" in v for v in result.violations), f"Expected drift violation: {result.report()}"


# ==========================================================================
# WS-05 PART 2: HARNESS UNIT TESTS
# ==========================================================================


def test_harness_check_schema_validity() -> None:
    """Harness schema evaluator correctly scores valid and malformed responses."""
    from tests.harness import check_schema_validity

    # Valid response
    resp = copy.deepcopy(CASES["SAMPLE-01"]["expected_output"])
    score, v = check_schema_validity(resp, "SAMPLE-01")
    assert score == 10.0
    assert len(v) == 0

    # Mismatched scenario_id
    score_bad, v_bad = check_schema_validity(resp, "OTHER-ID")
    assert score_bad < 10.0
    assert any("scenario_id" in x for x in v_bad)

    # Missing hourly_plan
    del resp["hourly_plan"]
    score_del, v_del = check_schema_validity(resp, "SAMPLE-01")
    assert score_del < 10.0
    assert any("missing top-level field 'hourly_plan'" in x for x in v_del)


def test_harness_score_interpretation() -> None:
    """Harness interpretation scorer correctly evaluates 4 sub-checks and relevance."""
    from tests.harness import score_interpretation

    truth = CASES["SAMPLE-01"]["expected_output"]["directive_interpretation"]
    # Perfect match
    res = score_interpretation(truth, truth, 2)
    assert res["count_correct"] is True
    assert res["type_correct"] is True
    assert res["hours_correct"] is True
    assert res["numeric_correct"] is True
    assert res["relevance_correct"] is True
    assert res["score"] == 25.0

    # Type mismatch
    bad_type = copy.deepcopy(truth)
    bad_type[0]["directive_type"] = "no_charge_window"
    res_bad = score_interpretation(bad_type, truth, 2)
    assert res_bad["type_correct"] is False
    assert res_bad["score"] < 25.0


def test_harness_compute_latency_stats() -> None:
    """Harness latency calculator assigns correct percentiles and rubric bands."""
    from tests.harness import compute_latency_stats

    # Band 1: p95 <= 5s
    latencies_1 = [0.5, 1.0, 1.5, 2.0, 2.5]
    stats_1 = compute_latency_stats(latencies_1)
    assert stats_1["band_pts"] == 3.0
    assert "Band 1" in stats_1["band"]
    assert stats_1["p50"] == 1.5

    # Band 2: 5s < p95 <= 15s
    latencies_2 = [2.0, 4.0, 6.0, 8.0, 10.0]
    stats_2 = compute_latency_stats(latencies_2)
    assert stats_2["band_pts"] == 2.0
    assert "Band 2" in stats_2["band"]

    # Band 4: > 30s
    latencies_4 = [5.0, 10.0, 15.0, 25.0, 35.0]
    stats_4 = compute_latency_stats(latencies_4)
    assert stats_4["band_pts"] == 0.0
    assert "Band 4" in stats_4["band"]


def test_harness_discover_optimize_route_finds_the_declared_path() -> None:
    """Discovery reads backend/routes/ and returns the endpoint M1 actually declared."""
    from tests.harness import discover_optimize_route

    endpoint, found = discover_optimize_route()
    assert found is True, (
        "route discovery found nothing, but backend/routes/optimize.py declares an "
        "endpoint -- discovery is broken, or the route moved"
    )
    assert endpoint == "/optimize-energy", (
        "the spec mandates POST /optimize-energy (problem.md 15); discovery "
        "returned {!r}".format(endpoint)
    )


def test_harness_route_fallback_is_the_spec_path(tmp_path) -> None:
    """With no routes to read, the fallback must still be the spec-mandated path.

    A fallback of /optimize would make the harness POST to a dead URL and report
    every case as failing, which under contest pressure reads as a broken
    service rather than a broken harness.
    """
    from tests.harness import discover_optimize_route

    empty = tmp_path / "routes"
    empty.mkdir()
    endpoint, found = discover_optimize_route(empty)
    assert found is False
    assert endpoint == "/optimize-energy"


