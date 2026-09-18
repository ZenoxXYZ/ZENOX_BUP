"""WS-01 API boundary tests (M1, contract C-7).

Covers the request contract C-1, the response contract C-4, the round-then-total
rule C-5, and the boundary behaviour the rubric scores directly: `400` rather
than `422` on a malformed request, and no uncontrolled 5xx anywhere.
"""

from __future__ import annotations

import copy
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

import backend.logic.replay as replay_module
import backend.routes.optimize as optimize
from backend.main import app
from backend.schemas.scenario import ScenarioRequest

TOLERANCE = 0.01
CASES = json.loads(
    (
        pathlib.Path(__file__).resolve().parents[1]
        / "docs/challenge/BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json"
    ).read_text()
)["cases"]

TOP_LEVEL_FIELDS = {
    "scenario_id",
    "directive_interpretation",
    "hourly_plan",
    "total_grid_kwh",
    "total_cost_bdt",
    "peak_grid_kwh",
    "plan_summary",
}


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def scenario() -> dict:
    return copy.deepcopy(CASES[0]["input"])


def _ids(cases: list[dict]) -> list[str]:
    return [case["id"] for case in cases]


def test_health_is_ready_and_exact(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("case", CASES, ids=_ids(CASES))
def test_every_public_case_returns_a_conforming_response(
    client: TestClient, case: dict
) -> None:
    response = client.post("/optimize-energy", json=case["input"])
    assert response.status_code == 200
    body = response.json()

    assert set(body) == TOP_LEVEL_FIELDS
    assert body["scenario_id"] == case["input"]["scenario_id"]

    interpretations = body["directive_interpretation"]
    assert len(interpretations) == len(case["input"]["operator_notes"])
    assert [entry["note_index"] for entry in interpretations] == list(
        range(len(interpretations))
    )
    for entry in interpretations:
        is_no_op = entry["directive_type"] == "no_op"
        assert is_no_op == (entry["applies"] is False)
        assert is_no_op == (entry["structured_adjustment"] is None)

    plan = body["hourly_plan"]
    assert [hour["hour"] for hour in plan] == list(range(24))
    for hour in plan:
        if hour["battery_action"] == "idle":
            assert hour["battery_kwh"] == 0
        for field in ("grid_kwh", "solar_used_kwh", "battery_kwh"):
            assert hour[field] >= 0


@pytest.mark.parametrize("case", CASES, ids=_ids(CASES))
def test_in_request_verification_accepts_our_own_plan(case: dict) -> None:
    """Regression: the seam once called the oracle with its arguments reversed.

    Nothing crashed and nothing 5xx'd -- the oracle simply saw an object with
    none of its seven fields, rejected every plan, and the service silently
    served the fallback instead. A silent validator is worse than no validator.

    This asserts the adapter itself, not the oracle: posting a request and
    replaying the body would pass even with the seam broken, because the
    fallback plan is also valid. `_verify` is where the argument order lives.
    """
    request = ScenarioRequest.model_validate(case["input"])
    response = optimize.build_response(request)
    assert optimize._verify(response, request) is True


def test_seam_hands_the_oracle_plain_dicts_request_first(
    scenario: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The oracle imports only `math` and `dataclasses`; it cannot take our models."""
    seen: list[tuple] = []

    def recorder(*args, **kwargs):
        seen.append(args)
        return replay_module.ReplayResult(ok=True, violations=[])

    monkeypatch.setattr(replay_module, "replay", recorder)
    request = ScenarioRequest.model_validate(scenario)
    optimize.build_response(request)

    assert seen, "the replay seam was never called"
    first, second = seen[0][:2]
    assert isinstance(first, dict) and isinstance(second, dict)
    assert "operator_notes" in first, "first argument must be the request"
    assert "hourly_plan" in second, "second argument must be the response"


@pytest.mark.parametrize("case", CASES, ids=_ids(CASES))
def test_totals_are_recomputed_from_the_rounded_plan(
    client: TestClient, case: dict
) -> None:
    """C-5: `hourly_plan` is the declared source of truth for the three totals."""
    body = client.post("/optimize-energy", json=case["input"]).json()
    tariffs = {hour["hour"]: hour["tariff_bdt_per_kwh"] for hour in case["input"]["hours"]}
    plan = body["hourly_plan"]

    assert body["total_grid_kwh"] == pytest.approx(
        sum(hour["grid_kwh"] for hour in plan), abs=TOLERANCE
    )
    assert body["total_cost_bdt"] == pytest.approx(
        sum(hour["grid_kwh"] * tariffs[hour["hour"]] for hour in plan), abs=TOLERANCE
    )
    assert body["peak_grid_kwh"] == pytest.approx(
        max(hour["grid_kwh"] for hour in plan), abs=TOLERANCE
    )


def _drop_capacity(payload: dict) -> None:
    payload["battery"].pop("capacity_kwh")


def _twenty_five_hours(payload: dict) -> None:
    payload["hours"].append(dict(payload["hours"][23]))


def _duplicate_hour(payload: dict) -> None:
    payload["hours"][5] = {**payload["hours"][5], "hour": 6}


def _hour_out_of_range(payload: dict) -> None:
    payload["hours"][5] = {**payload["hours"][5], "hour": 24}


def _four_notes(payload: dict) -> None:
    payload["operator_notes"] = ["a", "b", "c", "d"]


def _no_notes(payload: dict) -> None:
    payload["operator_notes"] = []


def _blank_note(payload: dict) -> None:
    payload["operator_notes"] = ["   "]


def _negative_demand(payload: dict) -> None:
    payload["hours"][0] = {**payload["hours"][0], "demand_kwh": -1.0}


def _wrong_type(payload: dict) -> None:
    payload["hours"][0] = {**payload["hours"][0], "demand_kwh": "lots"}


MALFORMED = [
    _drop_capacity,
    _twenty_five_hours,
    _duplicate_hour,
    _hour_out_of_range,
    _four_notes,
    _no_notes,
    _blank_note,
    _negative_demand,
    _wrong_type,
]


@pytest.mark.parametrize("mutate", MALFORMED, ids=[f.__name__ for f in MALFORMED])
def test_malformed_requests_are_400_not_422(
    client: TestClient, scenario: dict, mutate
) -> None:
    mutate(scenario)
    response = client.post("/optimize-energy", json=scenario)
    assert response.status_code == 400
    assert "Traceback" not in response.text


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_numbers_are_rejected(
    client: TestClient, scenario: dict, literal: str
) -> None:
    """JSON permits these literals; the contract does not."""
    raw = json.dumps(scenario)
    key = f'"demand_kwh": {scenario["hours"][0]["demand_kwh"]}'
    assert key in raw
    response = client.post(
        "/optimize-energy",
        content=raw.replace(key, f'"demand_kwh": {literal}', 1),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_broken_json_body_is_400(client: TestClient) -> None:
    response = client.post(
        "/optimize-energy",
        content="{not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_repeated_requests_are_stable(client: TestClient, scenario: dict) -> None:
    bodies = {
        json.dumps(client.post("/optimize-energy", json=scenario).json(), sort_keys=True)
        for _ in range(5)
    }
    assert len(bodies) == 1
