from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from backend.logic.guardrails import validate_directives


def _dummy_request(note_count: int = 1, capacity: float = 200.0) -> MagicMock:
    req = MagicMock()
    req.operator_notes = [f"Note {i}" for i in range(note_count)]
    req.battery.capacity_kwh = capacity
    req.battery.minimum_energy_kwh = 40.0
    return req


def test_guardrails_noop_invariant_enforced() -> None:
    req = _dummy_request(1)
    raw = {
        "interpretations": [
            {
                "note_index": 0,
                "applies": True,  # Inconsistent with no_op
                "directive_type": "no_op",
                "structured_adjustment": {"hours": [12]},  # Must be None for no_op
                "explanation": "test",
            }
        ]
    }
    validated = validate_directives(raw, req)
    assert len(validated) == 1
    assert validated[0]["directive_type"] == "no_op"
    assert validated[0]["applies"] is False
    assert validated[0]["structured_adjustment"] is None


def test_guardrails_unsupported_type_degraded() -> None:
    req = _dummy_request(1)
    raw = {
        "interpretations": [
            {
                "note_index": 0,
                "applies": True,
                "directive_type": "solar_output_reduction",  # Common provider hallucination
                "structured_adjustment": {"hours": [12], "factor": 0.5},
            }
        ]
    }
    validated = validate_directives(raw, req)
    assert validated[0]["directive_type"] == "no_op"
    assert validated[0]["applies"] is False
    assert validated[0]["structured_adjustment"] is None


def test_guardrails_hours_cleaned_and_sorted() -> None:
    req = _dummy_request(1)
    raw = {
        "interpretations": [
            {
                "note_index": 0,
                "applies": True,
                "directive_type": "no_charge_window",
                "structured_adjustment": {"hours": [15, 13, 14, 13, 24, -1, "bad"]},
            }
        ]
    }
    validated = validate_directives(raw, req)
    assert validated[0]["applies"] is True
    assert validated[0]["structured_adjustment"]["hours"] == [13, 14, 15]


def test_guardrails_empty_hours_degrades_to_noop() -> None:
    req = _dummy_request(1)
    raw = {
        "interpretations": [
            {
                "note_index": 0,
                "applies": True,
                "directive_type": "no_discharge_window",
                "structured_adjustment": {"hours": []},
            }
        ]
    }
    validated = validate_directives(raw, req)
    assert validated[0]["directive_type"] == "no_op"
    assert validated[0]["applies"] is False
    assert validated[0]["structured_adjustment"] is None


def test_guardrails_factor_clamped() -> None:
    req = _dummy_request(1)
    raw = {
        "interpretations": [
            {
                "note_index": 0,
                "applies": True,
                "directive_type": "solar_reduction",
                "structured_adjustment": {"hours": [12], "factor": 1.5},
            }
        ]
    }
    validated = validate_directives(raw, req)
    assert validated[0]["structured_adjustment"]["factor"] == 1.0


def test_guardrails_reserve_clamped_to_capacity() -> None:
    req = _dummy_request(1, capacity=300.0)
    raw = {
        "interpretations": [
            {
                "note_index": 0,
                "applies": True,
                "directive_type": "minimum_battery_reserve",
                "structured_adjustment": {"hours": [18, 19], "minimum_energy_kwh": 500.0},
            }
        ]
    }
    validated = validate_directives(raw, req)
    assert validated[0]["structured_adjustment"]["minimum_energy_kwh"] == 300.0


def test_guardrails_missing_entries_filled_with_noop() -> None:
    req = _dummy_request(3)
    raw = {
        "interpretations": [
            {
                "note_index": 1,
                "applies": True,
                "directive_type": "no_charge_window",
                "structured_adjustment": {"hours": [2, 3]},
            }
        ]
    }
    validated = validate_directives(raw, req)
    assert len(validated) == 3
    assert validated[0]["directive_type"] == "no_op"
    assert validated[1]["directive_type"] == "no_charge_window"
    assert validated[2]["directive_type"] == "no_op"
