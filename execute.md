# Execution Tracker

## Status Model

Use the canonical [Workstream statuses and completion gates](docs/core/DEFINITION_OF_DONE.md).

`TODO -> IN PROGRESS -> VERIFYING -> VERIFIED`

`BLOCKED` and `NEEDS CLARIFICATION` may replace an active status when they
accurately describe the current condition. Record Local Complete, Merge Ready
where the repository workflow uses branches/PRs, and Workstream Complete as
separate evidence-backed gates.

## Timebox And Lifecycle Checkpoints

- **Available time / selected strategy:**
- **Official deadlines / mandatory checkpoints:**
- **First credible proof target:**
- **Riskiest integration boundary / target:**
- **Approximate Solution Freeze zone:**
- **Submission packaging / live-demo requirement:**

## Current Foundation State

- [x] Generic runtime foundation exists and has recorded verification evidence.
- [x] Generic PostgreSQL Compose, Alembic-baseline, and PostgreSQL CI artifacts exist without product-domain schema.
- [x] Supervisor-verified local PostgreSQL startup, connectivity, migration upgrade/version tracking, and PostgreSQL-backed pytest passed using an alternate host port because native PostgreSQL occupied `5432`.
- [x] Draft PR #3 CI passed its PostgreSQL readiness, migration-upgrade, and pytest path.
- [?] Product-specific work requires approved `problem.md` and `plan.md`.

## Workstream Summary

| ID | Objective | Status | Critical Proof Path | Primary owner | Dependencies | Verification / evidence | Next |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WS-XX | TBD from approved plan | TODO | TBD | TBD | TBD | TBD | TBD |

## Workstream Card

### WS-XX — Name

- **Objective:**
- **Critical-Proof-Path relevance:**
- **Primary owner:**
- **Contributors / optional specialist owners:**
- **Integration Owner (optional):**
- **Verification Owner (optional):**
- **Dependencies:**
- **Governing Interface / Assumption Contracts:** `APPROVED CONTRACT` or `PROVISIONAL ASSUMPTION` where useful.
- **Risk level:**
- **Implementation / construction state:**
- **Integration applicability / state:** Use `N/A` only with a short rationale when no independently developed boundary exists.
- **Verification state:**
- **Required evidence:**
- **Current evidence:**
- **Branch / worktree:**
- **Builder / Builder status:**
- **Local status:**
- **PR / CI / Reviewer / Review verdict:**
- **Merge status / synchronization / rendezvous where applicable:**
- **Exit criteria:**
- **Blockers:**
- **Decision needed:**
- **Next action:**
- **Deferrals:**
- **Overall status:**

Track only evidence-backed state. Use `N/A` for layers that do not belong to the approved workstream.
