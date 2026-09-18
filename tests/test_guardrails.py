from __future__ import annotations

import copy
import json
import math
import pathlib

import pytest

from backend.logic.guardrails import Directive, validate_directives
from backend.schemas.scenario import ScenarioRequest


CASES = json.loads(
    (pathlib.Path(__file__).parent / "fixtures" / "public_cases.json").read_text()
)["cases"]


def _request(note_count: int = 1) -> ScenarioRequest:
    payload = copy.deepcopy(CASES[0]["input"])
    payload["operator_notes"] = [f"note {index}" for index in range(note_count)]
    return ScenarioRequest.model_validate(payload)


def _entry(kind: str, index: int = 0, **adjustment: object) -> dict[str, object]:
    shapes: dict[str, dict[str, object] | None] = {
        "solar_reduction": {"hours": [2, 3], "factor": 0.5},
        "minimum_battery_reserve": {"hours": [2, 3], "minimum_energy_kwh": 60.0},
        "no_charge_window": {"hours": [2, 3]},
        "no_discharge_window": {"hours": [2, 3]},
        "max_grid_window": {"hours": [2, 3], "max_grid_kwh": 90.0},
        "no_op": None,
    }
    value = shapes[kind]
    if value is not None:
        value = {**value, **adjustment}
    return {
        "note_index": index,
        "applies": kind != "no_op",
        "directive_type": kind,
        "structured_adjustment": value,
    }


@pytest.mark.parametrize(
    "kind",
    [
        "solar_reduction",
        "minimum_battery_reserve",
        "no_charge_window",
        "no_discharge_window",
        "max_grid_window",
        "no_op",
    ],
)
def test_accepts_each_exact_directive_type(kind: str) -> None:
    directive = validate_directives({"interpretations": [_entry(kind)]}, _request())[0]
    assert directive.directive_type == kind
    assert directive.applies is (kind != "no_op")
    assert (directive.structured_adjustment is None) is (kind == "no_op")


def test_orders_entries_and_repairs_hours_without_range_inference() -> None:
    raw = {
        "interpretations": [
            _entry("no_charge_window", 1, hours=[14, 13, 14]),
            _entry("solar_reduction", 0, hours=[13, 15]),
        ]
    }
    directives = validate_directives(raw, _request(2))
    assert [item.note_index for item in directives] == [0, 1]
    assert directives[0].structured_adjustment == {"hours": [13, 15], "factor": 0.5}
    assert directives[1].structured_adjustment == {"hours": [13, 14]}


@pytest.mark.parametrize("hours", [[24], [-1], [True], [1.5], [], "2,3"])
def test_invalid_hours_degrade_only_the_entry(hours: object) -> None:
    raw = {"interpretations": [_entry("no_charge_window", hours=hours)]}
    assert validate_directives(raw, _request())[0] == Directive(0, False, "no_op", None)


def test_duplicate_missing_and_invalid_indexes_degrade_without_reassignment() -> None:
    raw = {
        "interpretations": [
            _entry("no_charge_window", 0),
            _entry("no_discharge_window", 0),
            _entry("max_grid_window", 4),
        ]
    }
    assert validate_directives(raw, _request(3)) == [
        Directive(0, False, "no_op", None),
        Directive(1, False, "no_op", None),
        Directive(2, False, "no_op", None),
    ]


@pytest.mark.parametrize(
    "entry",
    [
        {"note_index": 0, "applies": True, "directive_type": "solar", "structured_adjustment": {}},
        _entry("solar_reduction", factor=-0.1),
        _entry("solar_reduction", factor=1.1),
        _entry("solar_reduction", factor=math.nan),
        _entry("solar_reduction", factor=math.inf),
        _entry("minimum_battery_reserve", minimum_energy_kwh=-1),
        _entry("minimum_battery_reserve", minimum_energy_kwh=999),
        _entry("max_grid_window", max_grid_kwh=-1),
        _entry("max_grid_window", max_grid_kwh=math.inf),
    ],
)
def test_invalid_types_and_numbers_degrade(entry: dict[str, object]) -> None:
    assert validate_directives({"interpretations": [entry]}, _request())[0].directive_type == "no_op"


def test_reserve_below_base_minimum_remains_a_valid_directive() -> None:
    directive = validate_directives(
        {"interpretations": [_entry("minimum_battery_reserve", minimum_energy_kwh=30)]},
        _request(),
    )[0]
    assert directive.structured_adjustment == {"hours": [2, 3], "minimum_energy_kwh": 30.0}


def test_invariant_repairs_and_shape_errors() -> None:
    actionable = _entry("no_charge_window")
    actionable["applies"] = False
    no_op = _entry("no_op", 1)
    no_op["applies"] = True
    malformed = _entry("max_grid_window", 2)
    malformed["structured_adjustment"] = {"hours": [2], "max_grid_kwh": 5, "extra": 1}
    directives = validate_directives({"interpretations": [actionable, no_op, malformed]}, _request(3))
    assert directives[0].applies is True
    assert directives[1] == Directive(1, False, "no_op", None)
    assert directives[2] == Directive(2, False, "no_op", None)


def test_no_op_adjustment_and_mismatched_shape_are_not_trusted() -> None:
    no_op = _entry("no_op")
    no_op["structured_adjustment"] = {"hours": [2]}
    wrong_shape = _entry("no_charge_window", 1)
    wrong_shape["structured_adjustment"] = {"hours": [2], "factor": 0.5}
    directives = validate_directives({"interpretations": [no_op, wrong_shape]}, _request(2))
    assert directives == [
        Directive(0, False, "no_op", None),
        Directive(1, False, "no_op", None),
    ]


def test_bad_sibling_does_not_destroy_valid_siblings_and_runs_deterministically() -> None:
    raw = {
        "interpretations": [
            _entry("solar_reduction", 0),
            {"note_index": 1, "applies": "yes", "directive_type": "no_charge_window", "structured_adjustment": {"hours": [1]}},
            _entry("max_grid_window", 2),
        ]
    }
    first = validate_directives(raw, _request(3))
    assert [item.directive_type for item in first] == ["solar_reduction", "no_op", "max_grid_window"]
    assert first == validate_directives(copy.deepcopy(raw), _request(3))
