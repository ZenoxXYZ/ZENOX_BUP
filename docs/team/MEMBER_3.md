# Member 3 — Routing

Routing only. Canonical sources: `AGENTS.md` (policy) · `problem.md`
(requirements) · `plan.md` (design + contracts) · `execute.md` (live state) ·
`review.md` (verification) · `docs/AGENT_WORKFLOW.md` (reconstruction procedure).

| | |
| --- | --- |
| Name / GitHub | [@FMAmax](https://github.com/FMAmax) |
| Role | **QA / Integration Lead** · HADF Control Room participant · independent Reviewer · repository-state verifier · rendezvous coordinator |
| Current assignment | **WS-05** — replay validator + public-sample harness + failure-injection suite |
| Then | **WS-06** — Dockerfile, GHCR publish, public deployment, README, CI reduction |
| Branch | `feat/ws-05-replay-harness`, then `feat/ws-06-deploy-docker-readme` |

## Owned

- `backend/logic/replay.py`, `tests/`, `tests/fixtures/`
- `Dockerfile`, `README.md`, `.github/workflows/ci.yml`
- Contract **C-6** (`ReplayResult`) — `plan.md §3`
- **`execute.md` and `review.md`** — builders propose updates in their
  Implementation Reports; you write them

## Do not touch

`backend/main.py`, `backend/routes/`, `backend/schemas/`,
`backend/logic/optimizer.py`, `backend/logic/materializer.py` (M1) ·
`backend/services/interpreter.py`, `backend/logic/guardrails.py`,
`backend/logic/constraints.py` (M2)

## Why WS-05 is yours and starts first

It validates against the **specification**, not the implementation. If the
optimizer's author also writes its validator, both inherit the same misreading and
the error stays invisible until the judge finds it. It also has **zero code
dependencies** — start it at T+0 and it becomes the oracle every other workstream
self-verifies against.

**Build both replay modes** (`plan.md §5`):
- **Mode A, self-consistent** — against the directives the service itself returned
- **Mode B, ground-truth** — against the *expected* directives from the sample pack

Mode B is what the judge does, and the only mode that distinguishes "interpreted
correctly but applied wrong" from "interpreted wrong".

## Key references

- Schema + physics rules to replay — `problem.md §7`, `§10`, `§11`
- Scoring model to mirror in the scorecard — `problem.md §12`
- Failure-path proof requirements — `problem.md §15`
- Proof Package — `problem.md §16`
- Public corpus + coverage gaps — `problem.md §19`
- Deployment constraints and decisions — `execute.md` D2
- Submission checklist — `execute.md §7`

## Non-negotiables

1. **Deploy a `/health`-only skeleton to the real public URL by 20:00**, while it
   is still trivial to debug. Deployment + documentation is 20 points and cannot
   be rushed at 22:45.
2. **Verify a deliberately broken plan is correctly flagged.** A validator that
   passes everything is worse than none — it manufactures false confidence.
3. **Measure latency against the public URL**, never localhost.
4. **Test both endpoints from outside our network** before submitting.
5. **Make the repo and the GHCR package public only *after* the 23:00 deadline** —
   private during, public after, per the rules.
6. Reduce `ci.yml` to `pip install` + `pytest`. It currently spins up Postgres and
   runs `alembic upgrade head`, and will go red on every PR.

## QA discipline

- Builder self-QA ≠ supervisor evidence review ≠ independent QA.
- Do not trust "done" claims — cross-check code, tests, git history, runtime behaviour.
- **Merge ≠ integration ≠ Workstream Complete.** Nothing is complete on a green PR alone.
- A passing review does not automatically mean merge. You decide merge-readiness.
- If repository evidence contradicts a state file, verify the repo, report the
  inconsistency, and correct the stale doc only after the real state is understood.
- Call the integration rendezvous. **Enforce Solution Freeze at 22:20** regardless
  of state.

## First action — blocker B2

Create the Hugging Face Space and confirm the GitHub Actions → GHCR path (no local
Docker daemon required). In parallel, begin WS-05 — it needs nothing from anyone.
