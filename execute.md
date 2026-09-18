# Execute — Canonical Live Execution State

Single source of truth for assignments, authorizations, status and blockers.
Requirements: `problem.md`. Approved design: `plan.md`. Verification and
integration state: `review.md`.

**Owner:** Member 3 (QA / Integration Lead). Builders propose updates in their
Implementation Reports; M3 writes them. If member routing conflicts with this
file, **this file wins** — report the drift, do not silently reconcile.

## 1. Locked Decisions

Approved at human design review. Changing any of these requires a new human
decision, not builder judgement.

| # | Decision | Verdict |
| --- | --- | --- |
| D1 | LLM provider | **Google AI Studio (current Flash-class model) primary; Groq secondary.** Both free, instant, no card, native JSON-schema output. |
| D2 | Deployment | **Hugging Face Spaces (Docker SDK)** for the public endpoint. **GHCR built by GitHub Actions** for the pullable fallback image — no local Docker daemon required. |
| D3 | Solver | **`scipy.optimize.linprog` (HiGHS).** No hand-rolled heuristic. No PuLP/CBC. |
| D4 | LLM-failure policy | **Provider ladder:** primary → stricter retry → secondary provider → degrade all notes to `no_op` and still return a valid schedule with 200. **No regex or phrase-matching interpreter at any tier.** |
| D5 | Guardrail policy | **Repair-first.** Repair the unambiguously repairable; reject only unsupported types and broken shapes, degrading that single entry to `no_op` rather than the whole request. Log every repair. |
| D6 | Seat assignment | Strongest prompt-engineering person on **Member 2** — 60 points cascade from that seat. |
| D7 | Planning gate | **Combined Task + Implementation Plans pre-authorized** for the remainder of the round. See §2. |
| D8 | State files | `problem.md`, `plan.md`, `execute.md`, `docs/team/MEMBER_{1,2,3}.md` written now. `review.md` **also initialized** — it carried the template's false verification claims (Postgres / Alembic / "Draft PR #3") and could not be left in place while member routing pointed at it. See `review.md` finding F1. |

## 2. Standing Authorizations

**Combined Task + Implementation Plan is PRE-AUTHORIZED** for all workstreams for
the remainder of this round, per `docs/runbooks/TEAM_EXECUTION.md`'s allowance for
bounded low-risk tasks under explicit human authorization. At the remaining clock
the two-stage gate does not fit.

**Two carve-outs where the full gate still applies.** Stop for a human decision
before:

1. changing any frozen contract — **C-1 … C-7** in `plan.md §3`
2. any change that crosses into another member's workstream or files

Also still requiring a human decision: material architecture changes, invariant
changes, and anything evaluation-critical.

Unchanged from `AGENTS.md`: **do not commit or push unless explicitly requested.**
Report what changed and what was verified before any commit.

## 3. Member Assignments

One primary mutable assignment per member at a time. Ownership is accountability,
not a wall.

| Member | Name / GitHub | Primary | Then | Cross-cutting |
| --- | --- | --- | --- | --- |
| **M1** | [@abidhasan9538](https://github.com/abidhasan9538) | **WS-01** API boundary, schemas, error handling, scaffold removal | **WS-04** LP optimizer + materializer | owns C-1 and C-4 shapes |
| **M2** | [@ZenoxXYZ](https://github.com/ZenoxXYZ) | **WS-02** LLM interpreter | **WS-03** guardrails + constraint compiler | owns the prompt; holds both sides of the untrusted boundary |
| **M3** | [@FMAmax](https://github.com/FMAmax) | **WS-05** replay validator + harness | **WS-06** Docker, GHCR, deployment, README, CI | QA / Integration Lead · PR reviewer · owns `execute.md` + `review.md` · rendezvous · post-merge verification |

Collaborator invites must be **accepted** before M1 and M2 can push. Confirm this
before anything else — it is a silent blocker.

## 4. Workstream Status

Canonical gates are separate and sequential: `NOT LOCAL COMPLETE` → `LOCAL
COMPLETE` → `MERGE READY` → `WORKSTREAM COMPLETE`. **Merge alone is never
sufficient.**

| WS | Capability | Owner | Branch | Status | Blockers |
| --- | --- | --- | --- | --- | --- |
| WS-01 | API boundary + schemas | M1 | `feat/ws-01-api-contract` | NOT STARTED | — |
| WS-02 | LLM interpreter | M2 | `feat/ws-02-llm-interpreter` | NOT STARTED | B1 CLEARED — key live in `.env` |
| WS-03 | Guardrails + compiler | M2 | `feat/ws-03-guardrails-compiler` | NOT STARTED | WS-02 |
| WS-04 | Optimizer + materializer | M1 | `feat/ws-04-optimizer-materializer` | NOT STARTED | WS-01, C-3 stub |
| WS-05 | Replay validator + harness | M3 | pushed to `main` (bootstrap) | **LOCAL COMPLETE** — 79/79 green, red-green proven. Harness run end-to-end against M1's live WS-01 service: Mode A 10/10, **Mode B 4/10** (F15), schema 10/10, p50 0.008s. Re-run is MANDATORY once WS-03 merges. | none |
| WS-06 | Docker, deploy, README, CI | M3 | `feat/ws-06-deploy-docker-readme` | NOT STARTED | WS-01 skeleton; **B2 — no platform account** |

Integration applicability: all six workstreams require rendezvous. None is `N/A`.

## 5. Active Blockers

| ID | Blocker | Impact | Owner | Action |
| --- | --- | --- | --- | --- |
| ~~**B1**~~ | ~~No LLM API key exists on any team machine~~ | **RESOLVED 2026-09-18.** Gemini + Groq keys supplied by M2, both authenticate, both do structured output. Stored in local `.env` (gitignored, never committed). Measured latency: Groq 0.24-1.27s vs Gemini 11.5-15.4s -> see **F8**, the D4 ladder should likely reverse. See also **F7** (Gemini emits hour ranges, not expanded lists) and **F9** (all providers invent `type` names -- use a strict enum). | M2 | Rotate both keys after the round: they were pasted into a chat transcript. |
| **B2** | No deployment platform account; no GHCR package | 20 points, longest lead time | M3 | Create the HF Space, deploy a `/health`-only skeleton, confirm the Actions → GHCR path |
| ~~B3~~ | ~~Member names / GitHub handles unknown~~ | — | M3 | **RESOLVED** — seat order confirmed by human: M1 @abidhasan9538, M2 @ZenoxXYZ, M3 @FMAmax. Satisfies D6 (strongest prompt-engineering person on M2). All three collaborators verified with push access. |

B1 and B2 are the only blockers that can void the entire effort, and both are
resolvable in under fifteen minutes. They precede all building.

## 6. Timeline (BST, anchored on the round window)

| Clock | Function |
| --- | --- |
| 19:00 | Round start |
| 19:22 | Repo created from template (after reveal ✓), private ✓ |
| — now — | Design approved; state files written; branches to open |
| → 20:00 | **B1 and B2 cleared.** WS-01 skeleton pushed. `/health` live on the public URL while it is still trivial to debug. |
| 20:00 → 21:30 | WS-02 / WS-03 / WS-04 in parallel. **WS-05 oracle lands by 20:45** and everyone self-verifies against it. |
| 21:30 → 22:00 | Integration rendezvous. Real provider wired. All 10 public cases replay clean. Latency measured **from the public URL**. |
| 22:00 → 22:20 | GHCR image pushed and pulled from a clean machine. README written and witnessed by a teammate. |
| **22:20** | **SOLUTION FREEZE.** Critical fixes, verification, evidence and delivery only. Non-critical scope rejected. |
| 22:20 → 22:45 | Evidence collection. 3-minute video (tie-break only, ~15 minutes of effort). |
| 22:45 | **Submit** — endpoint URL, repo, README, GHCR tag, video. |
| 23:00 | Deadline. |
| after 23:00 | **Make the repo public and the GHCR package public** — the rules require private *during* the event and public *after* the submission deadline for evaluation. |

Freeze at 22:20 is not optional. The 5 points for "no judge debugging required"
and the 10 for reproducibility are won in that last stretch, not by one more
feature.

## 7. Submission Checklist

Owner M3. Nothing here is complete until verified from outside our own network.

- [ ] `GET /health` reachable externally, returns `{"status":"ok"}` within 60 s of start
- [ ] `POST /optimize-energy` reachable externally, exact C-1 request / C-4 response
- [ ] one interpretation entry per note, `note_index` order, `applies` invariant holds
- [ ] `hourly_plan` obeys ground-truth directives + balance + battery + caps + neutrality
- [ ] totals recomputed from `hourly_plan` and matching within 0.01
- [ ] p95 latency measured against the public URL and recorded
- [ ] five failure injections behave; no 5xx; no secret in any response or log
- [ ] GHCR image pullable by exact tag, reaches `/health` via the documented command, no baked secrets
- [ ] README reproduces on a clean environment with no undocumented step, witnessed by a teammate
- [ ] README credits every external library, API, and the starter template the repo was generated from
- [ ] no API key, token or `.env` committed anywhere in history
- [ ] 3-minute video accessible, ≤ 3:00, covers problem → architecture → LLM/guardrail/optimizer flow → how to run
- [ ] submitted before 23:00
- [ ] repo and GHCR package made public **after** the deadline

## 8. Change Log

| When | Who | Change |
| --- | --- | --- |
| Design review | M3 / Control Room | Repository reconstructed. Three official sources ingested. All 10 public cases parsed. Challenge classified (not Product Build). D1–D8 locked. `problem.md`, `plan.md`, `execute.md` and member routing written from the approved Control Room report. No branches created, no code written. |
| Bootstrap verification | M3 | Pre-push verification pass: `problem.md §19` table mechanically re-checked against the source JSON (10/10), 24 load-bearing spec facts confirmed verbatim against the official sources, secret scan clean, no source code touched. Found and fixed F1 — `review.md` template residue asserting a PostgreSQL foundation and a PR that does not exist in this repo. |
| Seat confirmation | M3 | Human corrected the provisional M1/M2 order: M1 @abidhasan9538 (WS-01 → WS-04), M2 @ZenoxXYZ (WS-02 → WS-03). Routing files updated to match. |
| WS-05 part 1 | M3 | `backend/logic/replay.py` landed: both replay modes, schema + physics layers, cascade suppression. `tests/test_replay.py` 50 tests. Green 10/10 reference schedules both modes; red 26 mutation tests; red-green proven by sabotaging three checks and confirming only the dependent tests fail. Deleted three obsolete template tests. Contract C-7 (test-file partition) added to `plan.md`. |
| WS-05 part 2 | M3 | `tests/harness.py` CLI scorecard and test harness implemented with stdlib fallback, route auto-discovery, Mode A/B verification, latency band calculation, failure resilience, and JSON output. 16 coverage gap and paraphrase fixtures in `tests/fixtures/gap_cases.json`. 28 new tests in `tests/test_replay.py` (78 total) covering C-3 overlap merge rules, 5 failure injection modes, and harness helpers; red-green proven across 6 distinct sabotage mutations. Finding F5 and F6 documented in `review.md`. |
