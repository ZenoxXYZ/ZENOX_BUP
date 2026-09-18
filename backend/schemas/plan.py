"""C-4 response contract (`plan.md §3`, `problem.md §10`).

The response object is the scored artifact, so the invariants are enforced by
the model rather than assumed by the code that fills it. The route treats a
failure here as a reason to serve the always-valid fallback plan, never as a
reason to return a 5xx.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.schemas.scenario import HOURS_IN_DAY

DirectiveType = Literal[
    "solar_reduction",
    "minimum_battery_reserve",
    "no_charge_window",
    "no_discharge_window",
    "max_grid_window",
    "no_op",
]

BatteryAction = Literal["charge", "discharge", "idle"]

FiniteNonNegative = Field(ge=0.0, allow_inf_nan=False)


class DirectiveInterpretation(BaseModel):
    """One entry per operator note, in ascending `note_index` order."""

    note_index: int = Field(ge=0)
    applies: bool
    directive_type: DirectiveType
    structured_adjustment: dict | None
    explanation: str

    @model_validator(mode="after")
    def _no_op_invariant(self) -> DirectiveInterpretation:
        """`no_op` <=> `applies is False` <=> `structured_adjustment is None`.

        `problem.md §5` states this as a hard invariant in all three directions,
        and `no_op` is the only type permitted with `applies = false`.
        """
        is_no_op = self.directive_type == "no_op"
        if is_no_op != (self.applies is False) or is_no_op != (
            self.structured_adjustment is None
        ):
            raise ValueError(
                "no_op invariant violated: "
                f"type={self.directive_type!r} applies={self.applies} "
                f"adjustment={'None' if self.structured_adjustment is None else 'set'}"
            )
        return self


class HourPlan(BaseModel):
    """One scheduled hour of `hourly_plan`."""

    hour: int = Field(ge=0, le=HOURS_IN_DAY - 1)
    grid_kwh: float = FiniteNonNegative
    solar_used_kwh: float = FiniteNonNegative
    battery_action: BatteryAction
    battery_kwh: float = FiniteNonNegative
    battery_energy_after_kwh: float = FiniteNonNegative

    @model_validator(mode="after")
    def _idle_carries_no_energy(self) -> HourPlan:
        if self.battery_action == "idle" and self.battery_kwh != 0.0:
            raise ValueError(f"hour {self.hour}: idle requires battery_kwh == 0")
        return self


class OptimizeResponse(BaseModel):
    """The `POST /optimize-energy` response body. Seven top-level fields."""

    scenario_id: str
    directive_interpretation: list[DirectiveInterpretation]
    hourly_plan: list[HourPlan]
    total_grid_kwh: float = FiniteNonNegative
    total_cost_bdt: float = FiniteNonNegative
    peak_grid_kwh: float = FiniteNonNegative
    plan_summary: str

    @field_validator("directive_interpretation")
    @classmethod
    def _one_entry_per_note_in_order(
        cls, entries: list[DirectiveInterpretation]
    ) -> list[DirectiveInterpretation]:
        expected = list(range(len(entries)))
        if [entry.note_index for entry in entries] != expected:
            raise ValueError("note_index must be 0..N-1 ascending, one entry per note")
        return entries

    @field_validator("hourly_plan")
    @classmethod
    def _full_day_in_order(cls, plan: list[HourPlan]) -> list[HourPlan]:
        if [entry.hour for entry in plan] != list(range(HOURS_IN_DAY)):
            raise ValueError(f"hourly_plan must be hours 0-{HOURS_IN_DAY - 1} ascending")
        return plan
