# Project Truth Model

Repository truth is distributed by purpose. These sources are complementary, not interchangeable.

| Source | Authority or evidence it holds |
| --- | --- |
| `AGENTS.md` | Stable agent operating policy. |
| `problem.md` | Normalized current problem and requirements. |
| `plan.md` | Approved system design. |
| `execute.md` | Live workstream and implementation state. |
| `review.md` | Verified findings, risks, and quality state. |
| `README.md` | Project orientation and actual usage. |
| Code | Actual implementation truth. |
| Tests | Executable verification. |
| Git history | Historical source evolution. |

## Authority And Precedence

For requirements and design, use: official event rules and clarifications, official challenge, approved `problem.md`, then approved `plan.md`.

For implemented state, use code, tests, migrations, Git state/history, and safe runtime verification. `execute.md`, `review.md`, and phase/review records summarize that evidence; they do not override it.

If sources conflict, inspect the implementation evidence, report the inconsistency, and correct summaries only after the actual state is understood.

## Active Truth And Historical Evidence

Root project records, code, tests, migrations, runtime checks, and Git state
are active project truth or active implementation evidence. They are not
historical merely because the repository began as a starter.

`docs/phases/` and `docs/reviews/` are historical implementation and review
evidence. They provide context and learning history, but do not replace active
root records or current repository evidence for onboarding or decisions.

## Four States

1. **Design state** — `problem.md`, `plan.md`, and approved contracts.
2. **Implementation state** — branches, worktrees, and local changes.
3. **Shared source state** — merged PRs and `origin/main`.
4. **Runtime state** — actual frontend, backend, database, and user-visible behavior.

## Stable Methodology And Dynamic Project State

Stable methodology belongs in `AGENTS.md`, detailed role workflows, and the HADF core/Git/runbook/prompt documentation. Dynamic challenge state belongs in the project-state files, phase/review records, and approved implementation evidence. Keep challenge-specific rules out of reusable methodology, and do not let a stale summary overrule code, tests, migrations, or Git evidence.
