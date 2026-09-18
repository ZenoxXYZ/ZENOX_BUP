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
import pathlib

import pytest

from backend.logic.replay import recomputed_cost, replay

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "public_cases.json"
CASES = {c["id"]: c for c in json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]}
CASE_IDS = sorted(CASES)


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
