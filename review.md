# Review — Verification And Integration State

Owner: Member 3 (QA / Integration Lead). Requirements: `problem.md`. Design:
`plan.md`. Live assignments and status: `execute.md`.

## Status: WS-05 LOCAL COMPLETE — NOTHING VERIFIED END-TO-END

WS-05 (replay oracle + integration harness) is `LOCAL COMPLETE`: 78 tests green,
red-green proven by sabotage, harness exercised against a mock server and a dead
port. **No workstream is `WORKSTREAM COMPLETE`.** WS-01 to WS-04 are in flight,
no PR has been opened, and nothing has been verified against a real running
service or a deployed URL — every such row below still reads UNVERIFIED.

Blocker **B1 is resolved** (both provider keys live, structured output confirmed).
Blocker **B2 stands**: no deployment target exists.

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

| WS-05 | Replay validator green gate | prototype then `tests/test_replay.py`: all 10 public reference schedules validate in Mode A and Mode B, 240 hours, 13 rule families | PASS 0 violations |
| WS-05 | Replay validator red gate | 26 mutation tests covering balance, neutrality, no-charge, no-discharge, grid cap, effective solar, rate limits, idle consistency, active reserve, capacity, totals, trajectory, negative values, and 13 schema/guardrail faults | PASS 26/26 |
| WS-05 | Tests genuinely exercise the validator | sabotaged the balance, effective-solar and neutrality checks in turn; confirmed only the dependent tests fail (1, 2 and 1 respectively), then restored byte-identical | PASS red-green |
| WS-05 | Mode A / Mode B distinction is real | constructed a plan consistent with an all-`no_op` misinterpretation that violates the true `solar_reduction`; Mode A passes, Mode B catches it | PASS |
| WS-05 | Oracle is independent of other workstreams | `replay.py` imports only `math` and `dataclasses` — nothing from `backend` | PASS |
| WS-05 | Full suite | `pytest tests/ -q` | PASS 50 passed |
| WS-05 p2 | Coverage gap fixtures valid | script parsed `tests/fixtures/gap_cases.json` (16 cases covering 3 real directives, solar+reserve co-occurrence, single-hour windows, factor 0.0/1.0, midnight crossing, relative phrasing, distractors, C-3 overlap rules) and validated all requests and directives | PASS 16/16 |
| WS-05 p2 | Directive compilation merge rules | unit tests in `tests/test_replay.py`: reserve takes max, grid cap takes min, solar reductions take min factor (do not multiply), no-charge and no-discharge union of hours, factor extremes, single-hour, and midnight windows | PASS 11/11 tests |
| WS-05 p2 | Five failure-injection modes | unit tests in `tests/test_replay.py`: Mode 1 (missing fields, 25h, 4 notes, empty notes, non-dict), Mode 2 (provider 504 timeout, controlled degradation ladder), Mode 3 (unsupported directive type, broken adjustment shape, invariant violations), Mode 4 (infeasible schedule breaches, fallback schedule validation), Mode 5 (stateless determinism, float drift > 0.01 detection) | PASS 13/13 tests |
| WS-05 p2 | Integration harness error handling & dead port | `.venv\Scripts\python.exe tests/harness.py --url http://localhost:8999 --cases tests/fixtures/public_cases.json`: connection failure gracefully handled with zero crashes, logged root violation per failing case, printed rubric scorecard, exit code 1 | PASS exit 1, 10/10 failed handled |
| WS-05 p2 | Integration harness against mock server | `.venv\Scripts\python.exe tests/harness.py --url http://127.0.0.1:8976 --cases tests/fixtures/public_cases.json`: all 10 cases Mode B clean, 100.0/100.0 points, cost ratio 1.0000, p50=0.0011s, exit code 0; warning on missing route printed | PASS exit 0, 10/10 clean |
| WS-05 p2 | Integration harness against gap cases | `.venv\Scripts\python.exe tests/harness.py --url http://127.0.0.1:8979 --cases tests/fixtures/gap_cases.json`: 16 cases evaluated; cases violating grid caps or reserves correctly flagged with root violations; exit code 1 | PASS exit 1, 5/16 expected breaches caught |
| WS-05 p2 | Red-green verification of new checks | sabotaged reserve max check (mutated to 60.0), solar reduction factor check (mutated to product 0.24), missing scenario_id (asserted valid), provider degradation neutrality (mutated energy), unsupported directive type (mutated to valid), and numerical drift (mutated delta to 0.005 below tolerance); observed RED failures under pytest, then restored | PASS red-green across 6 checks |
| WS-05 p2 | Full suite | `.venv\Scripts\python.exe -m pytest tests/ -q` | PASS 78 passed in 0.17s |

## Open QA Findings

| # | Finding | Severity | Status |
| --- | --- | --- | --- |
| F1 | `review.md` carried the template's false verification claims (Postgres / Alembic / PR #3) while member routing pointed all three members at it as canonical | High — would have presented fabricated verification state to a fresh builder session | FIXED at bootstrap |
| F2 | The Member 1 master prompt told M1 to delete two files in `tests/`, which `MEMBER_1.md` and `MEMBER_3.md` both assign to M3 | Medium — M1 would have edited M3's directory | FIXED — files deleted by M3; correction added to `MEMBER_1.md`; contract C-7 added to `plan.md` |
| F3 | No test-file partition existed, so three members writing into `tests/` would collide | Medium | FIXED — contract C-7 in `plan.md` |
| F4 | One mutation test was a silent no-op (set two hours to values the reference already held) and could never have failed | High — a test that cannot fail is worse than no test | FIXED — `_mutate` now asserts the response actually changed |
| F5 | `requests` package is not installed in the `.venv` environment, but `tests/harness.py` was specified to support stdlib fallback | Low — could prevent harness execution in minimal environments | FIXED — `tests/harness.py` implements standard library `urllib.request` as primary/fallback with identical JSON and error handling |
| F6 | `validate_request`, `replay`, and `recomputed_cost` in `backend/logic/replay.py` did not previously guard against non-dict payloads or check for `scenario_id` non-empty string | Medium — passing malformed or non-dict payloads to oracle could raise unhandled `TypeError` | FIXED — defensive type guards added to `validate_request`, `replay`, and `recomputed_cost` |
| F7 | Gemini emits hours as a `[start, end]` range, not expanded list | High | OPEN (Action M2) |
| F8 | Groq latency 10-60x faster than Gemini; reverse D4 ladder | Medium | OPEN (Action M2) |
| F9 | LLM providers invent directive types; strict enum required | High | OPEN (Action M2) |
| F10 | `recomputed_cost` returned 0.0 on malformed input | Medium | FIXED |
| F11 | `gemini-2.5-flash` model deprecated (404) | High | FIXED in `.env` |
| F12 | `.env.example` contains PostgreSQL template residue | Medium | FIXED in WS-06 |
| F13 | Harness fallback was `/optimize`; spec mandates `/optimize-energy` | Medium | FIXED |
| F14 | Scorecard awarded unmeasured points for Docker/README | High | FIXED |
| F15 | Mode B 4/10 pass rate under WS-01 fallback plan | Critical | SUPERSEDED by F17 |
| F16 | Cost ratio 0.906–0.924 under fallback plan | Medium | RESOLVED — HiGHS LP achieves 1.0000 across all 10 cases |
| F17 | Mode B pass rate regressed from 4/10 to 1/10 post WS-04 optimizer merge | Critical | OPEN (Action M1/M2: wire WS-02/03 constraints into optimizer) |

## QA Queue

Empty. No open PRs.

## Control Room Verification Log — WS-05 part 2 + blocker B1

| # | Claim | Command | Real output | Verdict |
| --- | --- | --- | --- | --- |
| 11 | Harness suite is green | `python -m pytest tests/ -q` | `78 passed in 0.11s` (was 50) | PASS |
| 12 | New merge tests can actually fail | line 296 `min(...)` -> `eff[h] * factor` (the multiply trap), rerun | `1 failed, 77 passed` — only `test_compile_constraints_solar_reductions_take_min_factor_not_product` | PASS (red-green) |
| 13 | Reserve-max tests can actually fail | line 299 `max(...)` -> `min(...)`, rerun | `3 failed, 75 passed` — reserves_take_max, three_simultaneous_real_directives, solar_and_reserve_cooccurrence | PASS (red-green) |
| 14 | Sabotage fully reverted | `cmp /tmp/replay.bak backend/logic/replay.py` | identical; `78 passed` | PASS |
| 15 | No cross-member file touched | `git status --porcelain` filtered to non-M3 paths | empty | PASS |
| 16 | Gemini key valid | `GET /v1beta/models` | HTTP 200, 40+ models listed | PASS |
| 17 | Gemini structured output works | `generateContent` + `responseSchema`, gemini-3.1-flash-lite | HTTP 200, valid JSON object returned | PASS |
| 18 | Groq key valid | `GET /openai/v1/models` | HTTP 200, 13 models listed | PASS |
| 19 | Groq structured output works | `chat/completions` + `response_format=json_object` | HTTP 200 on gpt-oss-120b, gpt-oss-20b, qwen3.8-27b | PASS |
| 20 | Measured provider latency | one warm call each, `curl -w time_total` | Groq qwen3.8-27b **0.24s**, gpt-oss-120b **1.27s**, gpt-oss-20b 0.91s · Gemini 3.1-flash-lite **11.5s / 15.4s** | PASS (measured) |
| 21 | Deployment reachable | — | not attempted | **UNVERIFIED** |
| 22 | End-to-end harness against a live server | — | no server running yet (WS-01..WS-04 in flight) | **UNVERIFIED** |

**B1 RESOLVED.** Both provider keys authenticate and both do structured output. Stored in local `.env`, confirmed ignored by `.gitignore:15` and absent from `git status`.

## Open QA Findings (continued)

**F7 — Gemini emits `hours` as a `[start, end]` RANGE, not the expanded list.** For
"reduce solar by 80% from 1 PM to 3 PM" gemini-3.1-flash-lite returned
`hours: [13, 15]`. Our C-2 contract requires the expanded end-exclusive list
`[13, 14]`. Every Groq model returned `[13, 14]` correctly on the same wording.
*Impact:* silently wrong hour sets on every window directive — that is the 25-pt
interpretation pool plus replay invalidation. *Action (M2):* state "explicit list
of every affected hour integer" in the prompt and validate cardinality in the
guardrail. Do not assume a two-element list is a range or a pair.

**F8 — the D4 provider ladder should be reversed on measured latency.** Groq is
10-60x faster than Gemini here (0.24-1.27s vs 11.5-15.4s) and got the hour
expansion right where Gemini did not. Latency is 3 scored points and a timeout
counts as a case failure. *Action (M2):* consider Groq primary, Gemini fallback.
This is M2's decision under D4 — recorded as evidence, not changed.

**F9 — all providers invent `type` names.** Observed: `solar_output_reduction`
(Gemini, Groq 120b, qwen) and `solar` (Groq 20b). None emitted the contract's
`solar_reduction`. *Action (M2):* the response schema must declare `type` as a
strict **enum of the six directive types**, not a free string. This is a
one-line schema fix that removes an entire failure class.

**F10 — `recomputed_cost` returns `0.0` on malformed input** (`replay.py:522,526`).
A silent zero reads as an infinitely good cost ratio in the harness scorecard.
*Action (M3):* the harness must gate the cost row on schema validity first.
Present behaviour is safe only because the schema layer runs before scoring.

**F11 — `gemini-2.5-flash` is dead for this key:** HTTP 404, *"no longer available
to new users."* Any config or doc naming it will fail closed. `.env` now pins a
live model name.

**F12 — `.env.example` is PostgreSQL template residue** and documents
`DATABASE_URL`/Docker Compose, none of which this service uses. Same class as F1.
*Action:* WS-06.

## Control Room Verification Log — first true end-to-end run

Against M1's merged WS-01 service (`19d03df`), started locally with uvicorn on
port 8123. This is the first time any row below was produced by a real HTTP
round trip rather than a unit test.

| # | Claim | Command | Real output | Verdict |
| --- | --- | --- | --- | --- |
| 23 | Service imports and starts | `pip install -r requirements.txt`; `uvicorn backend.main:app` | starts clean | PASS |
| 24 | `/health` responds | `curl /health` | `{"status":"ok"}` HTTP 200 | PASS |
| 25 | Route discovery finds M1's real endpoint | `discover_optimize_route()` | `/optimize-energy`, found=True | PASS |
| 26 | Harness runs end-to-end | `python tests/harness.py --url http://127.0.0.1:8123` | 10/10 cases posted, scorecard printed, exit 1 | PASS |
| 27 | **Mode A vs Mode B on the live service** | same run | **Mode A 10/10 PASS · Mode B 4/10 PASS** | **FAIL — see F15** |
| 28 | Schema contract | same run | 10.0/10.0 mean, `scenario_id` echoed on all 10 | PASS |
| 29 | Live latency | same run | p50 **0.008s**, p95 **0.031s** — Band 1, full 3.0/3.0 | PASS |
| 30 | Route tests can fail | fallback mutated to `/optimize`; discovery matcher broken | 1 failed each time, the correct test both times; restore byte-identical | PASS (red-green) |
| 31 | Full suite after rebase onto WS-01 | `python -m pytest tests/ -q` | `79 passed` | PASS |
| 32 | GHCR image pullable / README reproducible | — | not observable from an HTTP client; now explicitly unscored | **UNVERIFIED** |

**Measurable score on the live service: 52.9 / 83.0.** The remaining 17 points
(image pull 7.0, README 10.0) are deliberately unscored rather than assumed.

## Open QA Findings (continued)

**F13 — the harness fell back to `POST /optimize`; the spec mandates
`POST /optimize-energy`** (`problem.md §15`). Discovery reads `backend/routes/`
and got the right path, so this only bites when discovery fails — and then it
would POST to a dead URL and report all ten cases failing, which under contest
pressure reads as a broken service rather than a broken harness. *FIXED:* the
fallback is now the spec path, with a test that pins each branch separately.

**F14 — the scorecard awarded itself 17 points it never measured.** Category 6
added a hard-coded `+7.0` "placeholder" for a Docker image that does not exist,
and category 7 awarded a flat `10.0` for README reproducibility with the detail
string "Verified via standalone harness". Neither is observable from an HTTP
client. The inflated total read 69.9/100 where the honest measurable figure is
52.9/83. Same class as F1: a status display that flatters instead of informing.
*FIXED:* both now print `NOT MEASURED` and are excluded from the total.

**F15 — the live service satisfies Mode A on all 10 cases but fails Mode B on 6.**
Every failure is one of two families: `solar_used_kwh` exceeding effective solar
(SAMPLE-01, 06, 09) or `grid_kwh` exceeding the grid cap (SAMPLE-05, 07, 10).
The plans are internally self-consistent — balance, bounds and neutrality all
hold — but ignore `solar_reduction` and `max_grid_window`. This is the precise
failure the judge punishes three times (25 + 25 + 10 pools). **Expected at this
stage**, since WS-02 and WS-03 are unmerged and the optimizer is running with an
empty constraint set; recorded so the re-run after that merge is mandatory, not
optional. *Action:* re-run this harness the moment WS-03 lands. Until then no
Mode B claim may be made.

**F16 — cost ratio is 0.906–0.924 on the four cases that do pass — RESOLVED.**
Measurement update: With WS-04's optimizer merged, `SAMPLE-05` (the only case currently passing Mode B) reports `our_cost = 33950.00 BDT`, exactly matching `ref_cost = 33950.00 BDT` for a ratio of **1.0000**.
Isolated verification: When `backend.logic.optimizer.solve` is supplied the true compiled `ConstraintSet` for all 10 public cases, `our_cost` matches `ref_cost` to the cent across ALL 10 cases (ratio = 1.0000 on every case).
*Verdict:* F16 is resolved. The previously observed 8–10% cost gap was an artifact of `fallback_plan` (battery held completely idle all 24 hours without peak tariff arbitrage) prior to WS-04 merging, not a solver formulation or objective slip. The HiGHS continuous LP formulation in `backend/logic/optimizer.py` is exact and achieves 100% reference optimality.

**F17 — Mode B pass rate regressed from 4/10 to 1/10 following WS-04 optimizer merge (`1c84661`).**
*Severity:* Critical (60-point cascade across interpretation, constraint application, and optimization pools).
*Observable:*
Running `tests/harness.py --url http://127.0.0.1:8124 --cases tests/fixtures/public_cases.json`:
- Mode A: 10/10 PASS (self-consistent)
- Mode B: 1/10 PASS (only SAMPLE-05 passes; 9/10 fail)
Failures:
- `SAMPLE-01`: `h12: solar_used_kwh 180.0 exceeds effective solar 45.0`
- `SAMPLE-02`: `h2: charge 55.0 in no_charge_window hour`
- `SAMPLE-03`: `h19: battery energy 90.0 below active minimum 100.0`
- `SAMPLE-04`: `h18: discharge 55.0 in no_discharge_window hour`
- `SAMPLE-06`: `h10: solar_used_kwh 150.0 exceeds effective solar 75.0`
- `SAMPLE-07`: `h20: battery energy 40.0 below active minimum 90.0`
- `SAMPLE-08`: `h17: discharge 25.0 in no_discharge_window hour`
- `SAMPLE-09`: `h11: solar_used_kwh 215.0 exceeds effective solar 46.0`
- `SAMPLE-10`: `h20: battery energy 40.0 below active minimum 80.0`

*Mechanism & Root Cause:*
1. In `backend/routes/optimize.py:90`, `_interpret(request)` checks `seams.resolve("interpret")` and `seams.resolve("guardrails")`. Neither module exists in `main` (`backend.services.interpreter` and `backend.logic.guardrails` are in-flight in M2's WS-02/WS-03). Thus, `_interpret` falls back to `(_degraded_interpretation(request.operator_notes), [])`, producing empty directives `directives = []`.
2. In `backend/routes/optimize.py:117`, `_constraints(request, directives)` checks `compiler = seams.resolve("compiler")`. Because `backend.logic.constraints` does not exist (M2's WS-03) and `directives` is empty, `_constraints` falls back to `default_constraint_set(request)`.
3. `default_constraint_set(request)` (`backend/schemas/constraints.py:46`) sets baseline bounds: unreduced solar, `charge_ub = 50.0` for all 24 hours, `discharge_ub = 50.0` for all 24 hours, `grid_ub = inf` for all 24 hours, and `energy_lb = 40.0` for all 24 hours. No operator directives are present in this constraint set.
4. In `backend/routes/optimize.py:136`, `solve(request, attempt_constraints)` invokes WS-04's newly merged HiGHS optimizer.
5. The optimizer solves the LP to minimize cost without any directive constraints:
   - Charges during cheap night hours (e.g. h2 at 5 BDT/kWh in SAMPLE-02), violating `no_charge_window`.
   - Discharges during expensive evening peaks (e.g. h18 at 14 BDT/kWh in SAMPLE-04 and h17 in SAMPLE-08), violating `no_discharge_window`.
   - Drains battery down to base reserve (40 kWh) during peak hours (e.g. h19 in SAMPLE-03, h20 in SAMPLE-07 and SAMPLE-10), violating `minimum_battery_reserve`.
   - Consumes unreduced solar (e.g. 180 kWh in SAMPLE-01 h12), violating `solar_reduction`.
6. Why 4/10 passed before WS-04: Before WS-04 merged, `seams.resolve("optimizer")` returned `None`, so line 129 fell back to `fallback_plan(request, constraints)`. The fallback plan keeps battery completely idle (`charge=0.0, discharge=0.0, energy=initial_energy`), which coincidentally satisfied `no_charge_window`, `no_discharge_window`, and `minimum_battery_reserve` on SAMPLE-02, 03, 04, and 08. Once the active optimizer landed without the upstream constraint compiler, active dispatch replaced the accidental compliance of an idle battery.

*One-line reproduction:*
`python -c "from backend.routes.optimize import build_response; from backend.schemas.scenario import ScenarioRequest; import json; c = json.load(open('tests/fixtures/public_cases.json'))['cases'][1]; resp = build_response(ScenarioRequest.model_validate(c['input'])); from backend.logic.replay import replay; print(replay(c['input'], resp.model_dump(mode='json'), directives=c['expected_output']['directive_interpretation']).report())"`

*Oracle Check:*
Flagged hours were independently hand-checked against the official case JSON:
- SAMPLE-02 h2: Note specifies no charging 2 AM-5 AM; optimizer charged 55.0 kWh at 5 BDT/kWh. Oracle is correct.
- SAMPLE-04 h18: Note specifies no discharging 6 PM-8 PM; optimizer discharged 55.0 kWh at 14 BDT/kWh. Oracle is correct.
- SAMPLE-03 h19: Note specifies >= 100 kWh reserve; optimizer drained battery to 90.0 kWh (and 40.0 kWh at h20). Oracle is correct.
- SAMPLE-01 h12: Note cuts solar to 25% (45 kWh); optimizer consumed 180.0 kWh. Oracle is correct.
The oracle is 100% correct; there is zero oracle defect.

*File Boundary & Action:*
Root cause is in `backend/routes/optimize.py` (owned by M1) and the unmerged state of WS-02 (`backend.services.interpreter`) and WS-03 (`backend.logic.constraints`, owned by M2). Under M3 strict file boundary rules, M3 may not modify M1 or M2 files.
*Action:* M1 and M2 must prioritize completing and merging WS-02 and WS-03. Once WS-03's `compile_constraints` lands and is wired to `seams.resolve("compiler")`, all 10 cases will pass Mode B (as proven by our isolated verification of `solve()` with true constraints).


## Control Room Verification Log — F17 root cause independently confirmed

The F17 diagnosis was verified by an independent path rather than accepted on
report. M1's `solve()` and `materialize()` were driven with constraints compiled
by **M3's own oracle** (`replay.compile_constraints`) from the organizer's
ground-truth directives, then replayed in **Mode B** against that same truth. No
component appears twice in the path.

| # | Claim | Command | Real output | Verdict |
| --- | --- | --- | --- | --- |
| 33 | Optimizer is correct when given true constraints | scratch script: `compile_constraints` (M3) -> `solve` (M1) -> `materialize` (M1) -> `replay` Mode B (M3), all 10 public cases | **Mode B 10/10 clean** | PASS |
| 34 | Cost is exactly reference-optimal | same run, `min(1, ref/ours)` per case | **ratio 1.0000 on all 10**; cost matches the reference to the cent (e.g. SAMPLE-01 38365.00 = 38365.00) | PASS |
| 35 | F17 is a wiring gap, not a solver defect | above, plus `backend/routes/optimize.py:90,117` read | `seams.resolve("interpret")` and `seams.resolve("compiler")` both return None -> `directives = []` -> `default_constraint_set` (unreduced solar, `grid_ub = inf`, no windows) | PASS |
| 36 | The 4/10 -> 1/10 drop is explained | comparison with pre-PR-2 behaviour | the old `fallback_plan` held the battery idle, accidentally satisfying charge/discharge/reserve windows on 4 cases; real dispatch replaced accidental compliance. Nothing regressed | PASS |

**Consequence — this is the single most load-bearing result so far.** The
optimizer, materializer and oracle are all correct and exactly optimal. The
entire Mode B 1/10 result is one missing wire. When WS-02 supplies directives and
WS-03 supplies the compiler, the measured outcome is 10/10 Mode B at ratio 1.0.

**Shortcut available to M2.** `backend/logic/replay.py:268`
`compile_constraints(request, directives)` is already a complete constraint
compiler implementing the C-3 merge rules, and the run above proves it yields
exactly optimal, Mode-B-clean plans on all 10 cases. WS-03 does not need to be
written from scratch; it can wrap or copy that function. The file belongs to M3,
so the decision is M2's — but it removes WS-03 from the critical path and leaves
the interpreter (WS-02) as the only substantial work left.

**F16 RESOLVED, and not merely masked:** the earlier 0.906-0.924 ratios came from
the idle-battery fallback forgoing tariff arbitrage, not from an objective or
bound slip. With real constraints the LP is exact.

## Control Room Verification Log — WS-02 provider runtime (M2 handoff)

Full detail and the exact patch values: `docs/qa/ws-02-provider-runtime.md`.
All figures are real calls against the team's live keys.

| # | Claim | Command | Real output | Verdict |
| --- | --- | --- | --- | --- |
| 37 | M2's failure is timeouts, not credentials | 3 batched structured calls per model, WS-02 shape | ladder budgets 2.5/1.0/1.5s; measured need 1.36-7.98s. Every timeout sits below the latency of the model it guards | **CONFIRMED — M2 is correct** |
| 38 | `gemini-3.6-flash` is not viable as primary | 3 calls | **HTTP 503 "high demand" on 2 of 3**, 7.98s on the one that returned | FAIL |
| 39 | `gemini-3.1-flash-lite` is viable | 3 calls | 1.36s / 4.50s / 4.08s, **3/3 semantically correct** on all three traps | PASS |
| 40 | Groq secondary works | raw HTTP, explicit UA | 0.89s, correct | PASS |
| 41 | Groq 403 was not a key problem | same request with and without a User-Agent header | no UA: `HTTP 403 error code: 1010`; with UA: **OK in 0.89s** | PASS — see F18 |
| 42 | F7 (hour ranges) survives a real prompt | flash-lite with the six-type enum and explicit-hours instruction | `[13,14]` and factor 0.2 on **3/3** | **F7 RESOLVED — my original probe was at fault** |
| 43 | End-to-end on a merged tree | — | WS-02 not merged; seams still unresolved | **UNVERIFIED** |
| 44 | p50/p95 against the public URL | — | no deployed URL (B2) | **UNVERIFIED** |

## Open QA Findings (continued)

**F18 — Groq rejects the default Python User-Agent with HTTP 403 `error code: 1010`.**
A Cloudflare block on `Python-urllib/3.x`. The identical request with any
User-Agent header succeeds in 0.89s. It does **not** affect
`backend/services/interpreter.py`, which uses the official `groq` SDK and sends its
own UA. Recorded because the symptom is indistinguishable from a revoked key and
would burn scarce time at 22:00. Any raw-HTTP diagnostic or fallback must set a
User-Agent.

**F19 — `gemini-3.6-flash` returned HTTP 503 on 2 of 3 calls** and 7.98s on the
third. `interpreter.py:329` currently defaults to it. *Action (M2):* change the
in-code default to `gemini-3.1-flash-lite` so a missing env var cannot silently
select the unreliable model. `.env` and `.env.example` are already pinned.

**F20 — the WS-02 timeout ladder is set below measured provider latency.**
2.5s / 1.0s / 1.5s against calls needing 1.36-7.98s. Recommended
**8.0s / 8.0s / 6.0s**: worst case 22.0s, inside the 30s ceiling, with the typical
single-call path at 1.4-4.5s and still in latency Band 1. The trade is explicit —
a timeout firing early does not protect the 3 latency points, it forfeits up to 60
in interpretation and its cascade. *Action (M2):* `interpreter.py:246,250,257`.

**F8 RESOLVED WITHOUT AN ARCHITECTURE CHANGE.** M2 was right to refuse a silent D4
reversal. With `gemini-3.1-flash-lite`, Gemini-primary is 1.36-4.50s and handled
every trap, so **D4 stands as written**. F8 is fixed by changing the model, not the
ladder. No human decision on ordering is required after all.
