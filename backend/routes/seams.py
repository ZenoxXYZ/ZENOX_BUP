"""Optional seams to the workstreams that are still in flight.

WS-01 has to serve a valid response before WS-02, WS-03, WS-04 and WS-05 exist.
Each collaborator module is therefore resolved at call time and treated as
absent until it lands, so the service degrades instead of failing to import.

Expected entrypoints -- types are frozen by the contracts, these names are the
only open detail, and any owner who prefers a different one should say so:

    backend.services.interpreter.interpret_notes(request) -> dict          WS-02 / M2
    backend.logic.guardrails.validate_directives(raw, request) -> list     WS-03 / M2
    backend.logic.constraints.compile_constraints(directives, request)
        -> ConstraintSet                                                   WS-03 / M2
    backend.logic.optimizer.solve(request, constraints)
        -> (solar_used, charge, discharge)                                 WS-04 / M1
    backend.logic.replay.replay(response, request) -> ReplayResult (C-6)   WS-05 / M3
"""

from __future__ import annotations

import importlib
from collections.abc import Callable

_SEAMS: dict[str, tuple[str, str]] = {
    "interpret": ("backend.services.interpreter", "interpret_notes"),
    "guardrails": ("backend.logic.guardrails", "validate_directives"),
    "compiler": ("backend.logic.constraints", "compile_constraints"),
    "optimizer": ("backend.logic.optimizer", "solve"),
    "replay": ("backend.logic.replay", "replay"),
}


def resolve(seam: str) -> Callable | None:
    """Return the collaborator callable, or `None` while its workstream is pending."""
    module_name, attribute = _SEAMS[seam]
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None
    candidate = getattr(module, attribute, None)
    return candidate if callable(candidate) else None


def available() -> dict[str, bool]:
    """Which seams are wired right now. Useful in logs and at the health boundary."""
    return {name: resolve(name) is not None for name in _SEAMS}
