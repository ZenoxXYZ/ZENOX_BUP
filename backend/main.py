"""GridWise LLM-assisted energy optimization service.

Two endpoints, one process, no persistence (`plan.md §1`). The error handlers
here are load-bearing: a contract violation must answer `400`, not FastAPI's
default `422` (C-1), and nothing may escape as an uncontrolled 5xx or leak a
stack trace, a key or an environment value (`problem.md §9`, `§12.5`).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.routes import optimize, seams

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Record which collaborator workstreams are wired into this process."""
    logger.info("pipeline seams: %s", seams.available())
    yield


app = FastAPI(
    title="GridWise Energy Optimization API",
    version="1.0.0",
    description=(
        "Interprets natural-language campus operator notes into validated "
        "structured directives and returns a cost-minimizing 24-hour schedule."
    ),
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
def handle_invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Malformed or structurally invalid request -> 400 (C-1), never 422."""
    issues = [
        {
            "field": ".".join(str(part) for part in error.get("loc", ())),
            "message": error.get("msg", "invalid value"),
            "type": error.get("type", "value_error"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=400,
        content={"error": "invalid_request", "detail": issues},
    )


@app.exception_handler(Exception)
def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    """Last line of defence. Logged in full internally, opaque on the wire."""
    logger.exception("unhandled error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "The request could not be processed."},
    )


@app.get("/health", tags=["health"], summary="Readiness probe")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", tags=["health"], include_in_schema=False)
def root() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(optimize.router)
