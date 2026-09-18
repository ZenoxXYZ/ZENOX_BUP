# Member 1 — Routing

Routing only. Canonical sources: `AGENTS.md` (policy) · `problem.md`
(requirements) · `plan.md` (design + contracts) · `execute.md` (live state) ·
`review.md` (verification) · `docs/AGENT_WORKFLOW.md` (reconstruction procedure).

If this file conflicts with `execute.md`, **`execute.md` wins** — report the
drift, do not guess.

| | |
| --- | --- |
| Name / GitHub | [@abidhasan9538](https://github.com/abidhasan9538) |
| Role | Builder |
| Current assignment | **WS-01** — API boundary, request/response models, error handling, response assembly, scaffold removal |
| Then | **WS-04** — LP optimizer + plan materializer |
| Branch | `feat/ws-01-api-contract`, then `feat/ws-04-optimizer-materializer` |

## Owned

- `backend/main.py`, `backend/routes/`, `backend/schemas/`
- `backend/logic/optimizer.py`, `backend/logic/materializer.py`
- Contract shapes **C-1** (request) and **C-4** (response), plus **C-5** (rounding
  and totals) — see `plan.md §3`

## Do not touch

`backend/services/interpreter.py`, `backend/logic/guardrails.py`,
`backend/logic/constraints.py` (M2) · `backend/logic/replay.py`, `tests/`,
`Dockerfile`, `README.md`, `.github/workflows/ci.yml` (M3)

## Note on scaffold removal

Your master prompt's scaffold-removal step listed `tests/test_database.py` and
`tests/test_config.py`. **Skip those — M3 already deleted them** (along with
`tests/test_app.py`) in WS-05, because `tests/` is M3's directory. Your scaffold
removal covers non-test files only: `frontend/`, `migrations/`, `alembic.ini`,
`compose.yaml`, `backend/database.py`, and the `sqlalchemy` / `psycopg` /
`alembic` entries in `requirements.txt`.

Test-file ownership is contract **C-7** in `plan.md`. Yours are
`tests/test_api.py` and `tests/test_optimizer.py`.

## Key references

- Request / response schemas — `problem.md §9`, `§10`
- Battery and energy rules — `problem.md §7`
- LP formulation, netting, grid derivation, infeasibility ladder — `plan.md §4`
- `ConstraintSet` you consume from M2 — `plan.md §3` C-3
- Exit criteria — `plan.md §5`

## Non-negotiables for WS-04

1. **Net out simultaneous charge + discharge** (`plan.md §4a`). The schema forbids
   both in one hour; the LP will produce it.
2. **Derive `grid_kwh` from the balance equation** (`plan.md §4b`), never report
   the solver float.
3. **Round to 6 decimals first, then compute the three totals** from the rounded
   plan (C-5).
4. **Never 500.** Use the infeasibility ladder (`plan.md §4c`).

## Standing authorization

Combined Task + Implementation Plan is pre-authorized. Stop for a human decision
before changing C-1 … C-7 or touching another member's files. Do not commit or
push unless explicitly requested.

## First action

WS-01 is on the critical path and unblocks both other members. Land it first,
small and complete. Build a hand-written `ConstraintSet` stub returning the
defaults so WS-04 is never blocked on M2.

Verify against `backend/logic/replay.py` (M3) the moment it exists. It is the
scoring oracle — if it flags your plan, it is right until proven otherwise.
