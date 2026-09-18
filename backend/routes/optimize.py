"""`POST /optimize-energy` -- the boundary and the response assembly (WS-01).

The pipeline is `plan.md §1`, with every stage after request validation treated
as optional while its workstream is in flight. The controlling rule is
`problem.md §12.5`: never return a 5xx. A missing, failing or invalid stage
degrades to something valid and still answers 200.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from backend.logic.materializer import compute_totals, fallback_plan, materialize
from backend.routes import seams
from backend.schemas.constraints import ConstraintSet, default_constraint_set
from backend.schemas.plan import DirectiveInterpretation, HourPlan, OptimizeResponse
from backend.schemas.scenario import ScenarioRequest

logger = logging.getLogger(__name__)

router = APIRouter()

DEGRADED_EXPLANATION = (
    "Interpretation unavailable; note treated as not affecting today's schedule."
)


def _degraded_interpretation(notes: list[str]) -> list[DirectiveInterpretation]:
    """One `no_op` entry per note -- the bottom of the provider ladder (D4).

    Satisfies the §5 invariant in all three directions, so the response stays
    schema-valid when no interpreter is reachable.
    """
    return [
        DirectiveInterpretation(
            note_index=index,
            applies=False,
            directive_type="no_op",
            structured_adjustment=None,
            explanation=DEGRADED_EXPLANATION,
        )
        for index, _ in enumerate(notes)
    ]


def _field(source: Any, name: str) -> Any:
    """Read a field from a pydantic model, dataclass or plain dict alike."""
    if isinstance(source, dict):
        return source.get(name)
    return getattr(source, name, None)


def _as_interpretation(directive: Any, index: int) -> DirectiveInterpretation:
    """Adapt a trusted C-2 `Directive` into its C-4 response entry.

    Enforces the §5 invariant at this boundary too. Per D5 a single unusable
    entry degrades to `no_op` on its own rather than costing the whole request,
    so an applicable directive that arrives without its adjustment is dropped
    here instead of raising and forcing the entire response into fallback.
    """
    directive_type = _field(directive, "directive_type") or "no_op"
    applies = bool(_field(directive, "applies")) and directive_type != "no_op"
    adjustment = _field(directive, "structured_adjustment") if applies else None
    if applies and adjustment is None:
        logger.error(
            "note %d: %s arrived with no structured_adjustment; degrading to no_op",
            index,
            directive_type,
        )
        applies = False
    note_index = _field(directive, "note_index")
    explanation = _field(directive, "explanation") or ""
    return DirectiveInterpretation(
        note_index=index if note_index is None else note_index,
        applies=applies,
        directive_type=directive_type if applies else "no_op",
        structured_adjustment=adjustment,
        explanation=explanation,
    )


def _interpret(request: ScenarioRequest) -> tuple[list[DirectiveInterpretation], list[Any]]:
    """Run the interpreter and guardrails if they exist; degrade to `no_op` otherwise."""
    interpret = seams.resolve("interpret")
    guardrails = seams.resolve("guardrails")
    if interpret is None or guardrails is None:
        return _degraded_interpretation(request.operator_notes), []

    try:
        raw = interpret(request)
        directives = list(guardrails(raw, request))
    except Exception:
        logger.exception("interpretation failed; degrading every note to no_op")
        return _degraded_interpretation(request.operator_notes), []

    if len(directives) != len(request.operator_notes):
        logger.error(
            "interpreter returned %d directives for %d notes; degrading",
            len(directives),
            len(request.operator_notes),
        )
        return _degraded_interpretation(request.operator_notes), []

    entries = [
        _as_interpretation(directive, index) for index, directive in enumerate(directives)
    ]
    return entries, directives


def _constraints(request: ScenarioRequest, directives: list[Any]) -> ConstraintSet:
    """Compile directives into per-hour bounds, falling back to base rules."""
    compiler = seams.resolve("compiler")
    if compiler is None or not directives:
        return default_constraint_set(request)
    try:
        return compiler(directives, request)
    except Exception:
        logger.exception("constraint compilation failed; falling back to base rules")
        return default_constraint_set(request)


def _schedule(request: ScenarioRequest, constraints: ConstraintSet) -> list[HourPlan]:
    """Solve and materialize, descending the infeasibility ladder as needed."""
    solve = seams.resolve("optimizer")
    if solve is None:
        return fallback_plan(request, constraints)

    for attempt_constraints, label in (
        (constraints, "directives applied"),
        (default_constraint_set(request), "base rules only"),
    ):
        try:
            solar_used, charge, discharge = solve(request, attempt_constraints)
            return materialize(
                request, solar_used=solar_used, charge=charge, discharge=discharge
            )
        except Exception:
            logger.exception("solve failed (%s); descending the ladder", label)

    return fallback_plan(request, constraints)


def _verify(response: OptimizeResponse, request: ScenarioRequest) -> bool:
    """Ask WS-05's replay validator whether the assembled plan actually obeys the rules."""
    replay = seams.resolve("replay")
    if replay is None:
        return True
    try:
        result = replay(response, request)
    except Exception:
        logger.exception("replay validator raised; serving the plan unverified")
        return True
    ok = bool(_field(result, "ok"))
    if not ok:
        logger.error("replay violations: %s", _field(result, "violations"))
    return ok


def _assemble(
    request: ScenarioRequest,
    interpretations: list[DirectiveInterpretation],
    plan: list[HourPlan],
    summary: str,
) -> OptimizeResponse:
    total_grid, total_cost, peak_grid = compute_totals(plan, request)
    return OptimizeResponse(
        scenario_id=request.scenario_id,
        directive_interpretation=interpretations,
        hourly_plan=plan,
        total_grid_kwh=total_grid,
        total_cost_bdt=total_cost,
        peak_grid_kwh=peak_grid,
        plan_summary=summary,
    )


def _safe_response(request: ScenarioRequest) -> OptimizeResponse:
    """The response of last resort: degraded notes, battery idle, solar then grid."""
    return _assemble(
        request,
        _degraded_interpretation(request.operator_notes),
        fallback_plan(request, default_constraint_set(request)),
        "Fallback schedule: available solar used first, remaining demand from the grid, "
        "battery idle for all 24 hours.",
    )


def build_response(request: ScenarioRequest) -> OptimizeResponse:
    """Run the pipeline. Any failure below this line degrades rather than raises."""
    try:
        interpretations, directives = _interpret(request)
        constraints = _constraints(request, directives)
        plan = _schedule(request, constraints)
        applied = sum(1 for entry in interpretations if entry.applies)
        response = _assemble(
            request,
            interpretations,
            plan,
            f"Scheduled 24 hours against {applied} applicable operator directive(s), "
            "minimizing grid cost within the battery and energy rules.",
        )
    except Exception:
        logger.exception("response assembly failed; serving the fallback schedule")
        return _safe_response(request)

    if not _verify(response, request):
        logger.error("serving the fallback schedule after replay rejected the plan")
        return _safe_response(request)
    return response


@router.post(
    "/optimize-energy",
    response_model=OptimizeResponse,
    summary="Interpret operator notes and return a cost-minimizing 24-hour schedule",
    tags=["optimization"],
)
def optimize_energy(request: ScenarioRequest) -> OptimizeResponse:
    return build_response(request)
