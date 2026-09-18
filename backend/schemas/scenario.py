"""C-1 request contract (`plan.md §3`, `problem.md §9`).

Validation is exactly what the frozen contract states and no more. Anything a
request violates here becomes a `400`; semantic questions the contract does not
raise (a reserve above capacity, a starting charge above capacity) are left to
the optimizer's infeasibility ladder rather than rejected at the boundary.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

HOURS_IN_DAY = 24
MAX_OPERATOR_NOTES = 3

#: Rejects NaN and Infinity, which JSON permits and the contract does not.
FiniteNonNegative = Field(ge=0.0, allow_inf_nan=False)


class HourInput(BaseModel):
    """One hourly interval of the 24-hour scenario."""

    hour: int = Field(ge=0, le=HOURS_IN_DAY - 1)
    demand_kwh: float = FiniteNonNegative
    solar_kwh: float = FiniteNonNegative
    tariff_bdt_per_kwh: float = FiniteNonNegative


class BatteryInput(BaseModel):
    """Battery parameters. All five fields required, finite, non-negative."""

    capacity_kwh: float = FiniteNonNegative
    initial_energy_kwh: float = FiniteNonNegative
    minimum_energy_kwh: float = FiniteNonNegative
    max_charge_kwh_per_hour: float = FiniteNonNegative
    max_discharge_kwh_per_hour: float = FiniteNonNegative


class ScenarioRequest(BaseModel):
    """The `POST /optimize-energy` request body."""

    scenario_id: str
    operator_notes: list[str] = Field(min_length=1, max_length=MAX_OPERATOR_NOTES)
    hours: list[HourInput]
    battery: BatteryInput

    @field_validator("operator_notes")
    @classmethod
    def _notes_non_empty(cls, notes: list[str]) -> list[str]:
        for index, note in enumerate(notes):
            if not note.strip():
                raise ValueError(f"operator_notes[{index}] is empty after strip")
        return notes

    @field_validator("hours")
    @classmethod
    def _hours_cover_the_day(cls, hours: list[HourInput]) -> list[HourInput]:
        if len(hours) != HOURS_IN_DAY:
            raise ValueError(f"hours must contain exactly {HOURS_IN_DAY} entries")
        if {entry.hour for entry in hours} != set(range(HOURS_IN_DAY)):
            raise ValueError("hour values must be exactly 0-23, each appearing once")
        return hours

    def hours_ascending(self) -> list[HourInput]:
        """The 24 intervals in ascending hour order, whatever order they arrived in."""
        return sorted(self.hours, key=lambda entry: entry.hour)
