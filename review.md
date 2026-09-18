# Review — Verification And Integration State

Owner: Member 3 (QA / Integration Lead). Requirements: `problem.md`. Design:
`plan.md`. Live assignments and status: `execute.md`.

## Status: NOTHING VERIFIED YET

No code has been written for this challenge. No workstream has reached
`LOCAL COMPLETE`. No PR has been opened. No evidence has been collected.

This file previously contained the starter template's own review content —
checked-off claims about a PostgreSQL foundation, Alembic migrations and a
"Draft PR #3" that belong to the template repository's history and are **false
for ZENOX_BUP**. That content was removed rather than left to mislead a fresh
builder session. This challenge has no database and no migrations; see
`problem.md §18`.

## Completion Gates

Separate and sequential. **Merge alone is never sufficient.**

```text
NOT LOCAL COMPLETE -> LOCAL COMPLETE -> MERGE READY -> WORKSTREAM COMPLETE
```

`WORKSTREAM COMPLETE` requires all of: the artifact exists · contracts and
assumptions hold · applicable rendezvous performed · verification run ·
evidence recorded here · exit criteria in `plan.md §5` met.

Builder self-QA is not supervisor evidence review and is not independent QA.
Builder claims are cross-checked against code, tests, git history and runtime
behaviour before anything is recorded below.

## Proof Package Status

All rows UNVERIFIED. Evidence is recorded here only after being observed, never
on the strength of a builder report. Claim definitions and owners: `problem.md §16`.

| Claim | Evidence | Owner | Status |
| --- | --- | --- | --- |
| `/health` ready <60 s cold | — | M3 | UNVERIFIED |
| Response schema exact, `scenario_id` echoed | — | M3 | UNVERIFIED |
| 10/10 public interpretations correct | — | M2 | UNVERIFIED |
| All 6 directive types + `no_op` | — | M2 | UNVERIFIED |
| Paraphrase robustness ≥3 per type | — | M2 | UNVERIFIED |
| Guardrails reject adversarial model output | — | M2 | UNVERIFIED |
| Energy balance every hour, all cases | — | M3 | UNVERIFIED |
| Battery transitions / bounds / rate limits | — | M3 | UNVERIFIED |
| Each directive obeyed in `hourly_plan` | — | M3 | UNVERIFIED |
| End-of-day neutrality | — | M3 | UNVERIFIED |
| Totals match recalculation from `hourly_plan` | — | M1 | UNVERIFIED |
| Optimization cost ratio vs 10 reference optima | — | M1 | UNVERIFIED |
| p50 / p95 latency against the **public URL** | — | M3 | UNVERIFIED |
| Five controlled-failure injections | — | M3 | UNVERIFIED |
| GHCR image pullable, reaches `/health` | — | M3 | UNVERIFIED |
| README reproduces on a clean environment | — | M3 | UNVERIFIED |

## Control Room Verification Log

Evidence observed so far, with the command or artifact that produced it.

| When | Claim | Evidence | Result |
| --- | --- | --- | --- |
| Bootstrap | `problem.md §19` sample table matches the source JSON | script re-parsed `BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json` and compared note counts, directive types, hours arrays and numerics per case | PASS 10/10 |
| Bootstrap | Load-bearing spec facts transcribed correctly | 24 verbatim substring checks against the Problem Statement and Participant Guide (weights, latency bands, 30 s ceiling, 60 s readiness, 0.01 tolerance, optimization formula, end-exclusive time, factor semantics, neutrality, balance equation, reserve `max()`) | PASS 24/24 |
| Bootstrap | No secrets in committed state files | pattern scan for provider key prefixes, tokens, private-key headers and inline assignments | PASS, no matches |
| Bootstrap | No source code modified during bootstrap | `git status --porcelain` — Markdown only | PASS |

## Open QA Findings

| # | Finding | Severity | Status |
| --- | --- | --- | --- |
| F1 | `review.md` carried the template's false verification claims (Postgres / Alembic / PR #3) while member routing pointed all three members at it as canonical | High — would have presented fabricated verification state to a fresh builder session | FIXED at bootstrap |

## QA Queue

Empty. No open PRs.
