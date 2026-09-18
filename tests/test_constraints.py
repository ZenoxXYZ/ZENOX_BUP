from __future__ import annotations

import json
import math
import pytest

from backend.logic.constraints import compile_constraints
from backend.schemas.constraints import ConstraintSet, default_constraint_set
from backend.schemas.scenario import ScenarioRequest


def _load_sample_case() -> ScenarioRequest:
    with open("tests/fixtures/public_cases.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return ScenarioRequest.model_validate(data["cases"][0]["input"])


def test_compile_constraints_empty_matches_default() -> None:
    req = _load_sample_case()
    default_cs = default_constraint_set(req)
    compiled_cs = compile_constraints([], req)

    assert isinstance(compiled_cs, ConstraintSet)
    assert compiled_cs.eff_solar == default_cs.eff_solar
    assert compiled_cs.charge_ub == default_cs.charge_ub
    assert compiled_cs.discharge_ub == default_cs.discharge_ub
    assert compiled_cs.grid_ub == default_cs.grid_ub
    assert compiled_cs.energy_lb == default_cs.energy_lb


def test_compile_constraints_argument_order_agnostic() -> None:
    req = _load_sample_case()
    directives = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "no_charge_window",
            "structured_adjustment": {"hours": [2, 3]},
        }
    ]
    cs1 = compile_constraints(directives, req)
    cs2 = compile_constraints(req, directives)

    assert cs1 == cs2
    assert cs1.charge_ub[2] == 0.0
    assert cs1.charge_ub[3] == 0.0
    assert cs1.charge_ub[4] > 0.0


def test_compile_constraints_applies_all_bounds() -> None:
    req = _load_sample_case()
    directives = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "solar_reduction",
            "structured_adjustment": {"hours": [12], "factor": 0.25},
        },
        {
            "note_index": 1,
            "applies": True,
            "directive_type": "minimum_battery_reserve",
            "structured_adjustment": {"hours": [18, 19], "minimum_energy_kwh": 150.0},
        },
        {
            "note_index": 2,
            "applies": True,
            "directive_type": "max_grid_window",
            "structured_adjustment": {"hours": [14, 15], "max_grid_kwh": 75.0},
        },
    ]
    cs = compile_constraints(directives, req)

    # Solar reduction
    orig_solar = req.hours_ascending()[12].solar_kwh
    assert cs.eff_solar[12] == pytest.approx(orig_solar * 0.25, abs=1e-5)

    # Reserve
    assert cs.energy_lb[18] == 150.0
    assert cs.energy_lb[19] == 150.0

    # Grid cap
    assert cs.grid_ub[14] == 75.0
    assert cs.grid_ub[15] == 75.0
    assert cs.grid_ub[16] == math.inf
