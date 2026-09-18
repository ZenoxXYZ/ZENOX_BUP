# Plan — Approved Master System Design

Approved architecture, contracts, workstreams and topology for the GridWise
preliminary. Requirements live in `problem.md`; live execution state lives in
`execute.md`.

**Status:** approved by human design review. Contracts C-1 … C-7 are frozen —
changing any of them requires a human decision, not a builder's judgement.

## 1. Architecture

Smallest architecture that reliably meets the judge contract. Single FastAPI
process. No database, no frontend, no persistence, no auth.

```text
  HTTP boundary (FastAPI + Pydantic v2)
        |  validated ScenarioRequest
        v
  (1) Interpreter  --(one batched call, structured output)-->  LLM provider
        |  raw untrusted dict
        v
  (2) Guardrail Validator      (normalize - validate - reject)
        |  List[Directive]  (trusted)
        v
  (3) Constraint Compiler      (directives -> per-hour numeric bounds)
        |  ConstraintSet
        v
  (4) LP Optimizer             (scipy / HiGHS)
        |  raw float solution
        v
  (5) Plan Materializer        (net - derive grid - round - label action)
        |  hourly_plan + totals
        v
  (6) Replay Validator         (independent re-check of the final object)
        |
        v
  (7) Response Assembler       -> OptimizeResponse
```

| # | Component | In | Out | Failure behaviour | Test strategy | WS |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `interpreter` | notes, `capacity_kwh`, `minimum_energy_kwh`, note count | raw dict | timeout → retry → secondary provider → documented degrade; never raises | mocked provider; live smoke; paraphrase suite | WS-02 |
| 2 | `guardrails` | raw dict, scenario | `List[Directive]` | repairs the repairable; degrades a bad entry to `no_op`; never invents | pure unit tests, adversarial inputs | WS-03 |
| 3 | `constraints` | directives, hours, battery | `ConstraintSet` | merge rules resolve overlaps deterministically | table-driven unit tests | WS-03 |
| 4 | `optimizer` | `ConstraintSet` | float vectors | infeasibility ladder; never 500 | LP vs reference cost on 10 cases | WS-04 |
| 5 | `materializer` | float vectors | `hourly_plan`, 3 totals | nets simultaneity; derives grid; rounds then sums | property tests: balance, neutrality | WS-04 |
| 6 | `replay` | final response object | `ReplayResult` | violation → log, serve best valid fallback; never ship invalid silently | **is** the test oracle | WS-05 |
| 7 | `api` | all of the above | HTTP | `400` malformed, `200` degraded, controlled `500`, no secrets | schema + endpoint tests | WS-01 |

## 2. Technology Decisions

| Decision | Choice | Reasoning | Trade-off accepted |
| --- | --- | --- | --- |
| Web framework | **FastAPI + Pydantic v2** | already declared; gives exact request validation and response shaping, which is directly 10 rubric points | none |
| Solver | **`scipy.optimize.linprog` (HiGHS)** | the problem is a 96-variable continuous LP; HiGHS is exact, deterministic, solves in milliseconds, ships as a wheel with no external binary | larger wheel than PuLP; accepted for container reliability |
| Rejected: PuLP/CBC | — | friendlier API but bundles a CBC binary that intermittently breaks in slim images — avoidable risk against 10 Docker points | — |
| Rejected: hand-rolled heuristic | — | more code, provably worse cost, and risks **invalid** schedules under overlapping hard directives — attacks the 25-point pool to protect the 10-point one | — |
| LLM primary | **Google AI Studio, current Flash-class model** | free, instant key, no card, native JSON-schema structured output, fast enough for p95 ≤ 5s | free-tier RPM limits → mitigated by cache |
| LLM secondary | **Groq** | free, instant, very fast, JSON mode; different vendor so it survives a primary outage | second key to manage |
| Rejected: regex fallback | — | "hard-coded phrase matching as the sole interpreter" is named non-compliant, hidden notes paraphrase, and a phrase-matcher in the repo muddies the eligibility story for ~2 reliability points | — |
| Public endpoint | **Hugging Face Spaces (Docker SDK)** | free, no card, builds our Dockerfile, does not spin down on a minutes-scale idle timer the way free Render services do | — |
| Fallback image | **GHCR, built by GitHub Actions** | needs no local Docker daemon (ours is not running); `GITHUB_TOKEN` has package-write by default; exact immutable tag | package must be made **public** before the deadline |
| Container base | `python:3.12-slim` | small, no baked secrets, documented `EXPOSE`, binds `0.0.0.0` | — |

## 3. Frozen Contracts

### C-1 · `ScenarioRequest`
Exactly per `problem.md §9`. `operator_notes` 1–3 non-empty after strip; `hours`
exactly 24 with the `hour` set exactly 0–23 unique; `battery` all five fields
finite and non-negative. Violations → `400`.

### C-2 · `Directive` (validator output, trusted)
`note_index: int` · `applies: bool` · `directive_type: Literal[6]` ·
`structured_adjustment: dict | None`.

Invariant **enforced**, not assumed:
`directive_type == "no_op"` ⟺ `applies is False` ⟺ `structured_adjustment is None`.

### C-3 · `ConstraintSet` (compiler output → optimizer input)
Five arrays of length 24.

| Field | Default | Set by |
| --- | --- | --- |
| `eff_solar[h]` | `solar_kwh[h]` | `solar_reduction` |
| `charge_ub[h]` | `max_charge_kwh_per_hour` | `no_charge_window` → 0 |
| `discharge_ub[h]` | `max_discharge_kwh_per_hour` | `no_discharge_window` → 0 |
| `grid_ub[h]` | `+inf` | `max_grid_window` |
| `energy_lb[h]` | `minimum_energy_kwh` | `minimum_battery_reserve` |

**Overlap merge rules.** Each directive is a ceiling or a floor, so merge in the
direction that satisfies every individual directive simultaneously:

- two reserves on one hour → **maximum** (spec-stated)
- two grid caps on one hour → **minimum**
- two `solar_reduction`s on one hour → **minimum factor, do not multiply.**
  Multiplying two independent 0.5s to 0.25 over-reduces and could tighten our
  solar ceiling below the judge's. `min(factors)` provably satisfies every
  individual directive's ceiling under any reading.
- no-charge / no-discharge windows → union of hours, bound set to 0

### C-4 · `OptimizeResponse`
Exactly per `problem.md §10`. Seven top-level fields; one interpretation entry per
note in ascending `note_index`; 24 plan entries in ascending `hour`;
`battery_action` in `{charge, discharge, idle}`; `battery_kwh == 0` when `idle`;
all numerics finite and non-negative; `scenario_id` echoed verbatim.

### C-5 · Rounding and totals
Round all `hourly_plan` numerics to **6 decimals first**, then compute
`total_grid_kwh`, `total_cost_bdt` and `peak_grid_kwh` **from those rounded
values**. Never from solver floats. "Reported totals disagree with `hourly_plan`"
is an explicit penalty and `hourly_plan` is the declared source of truth.

### C-6 · `ReplayResult`
`ok: bool` · `violations: list[str]`, each naming the hour and the rule.
Consumed both in-request and by the test harness — same code path, so the harness
tests what ships.

### C-7 · Test-file partition

`tests/` is owned by M3, but all three members write focused tests for their own
components (`AGENTS.md §12`). Without a partition, three people writing into one
directory collide. Assignment is by filename:

| Owner | Files |
| --- | --- |
| M1 | `tests/test_api.py`, `tests/test_optimizer.py` |
| M2 | `tests/test_interpreter.py`, `tests/test_guardrails.py`, `tests/test_constraints.py` |
| M3 | `tests/test_replay.py`, `tests/harness.py`, `tests/fixtures/`, `tests/conftest.py` |

`tests/conftest.py` puts the repository root on `sys.path`; it exists already, so
no member needs to add import plumbing.

The three template test files (`test_app.py`, `test_config.py`,
`test_database.py`) were deleted by M3 in WS-05 — they exercised the Postgres and
`DATABASE_URL` scaffold plus a `GET /` route and a `Generic Hackathon Starter`
title that this challenge does not have. **M1 does not need to delete them**; the
Member 1 master prompt's scaffold-removal step listed two of them before the
partition existed.

## 4. The Optimization Is A Pure Linear Program

For `h` in 0..23: `g[h] >= 0` · `s[h] in [0, eff_solar[h]]` ·
`c[h] in [0, charge_ub[h]]` · `d[h] in [0, discharge_ub[h]]`.

```text
minimize   SUM  g[h] * tariff[h]

subject to (1) g[h] + s[h] + d[h] - c[h] = demand[h]              per hour
           (2) g[h] <= grid_ub[h]
           (3) energy_lb[h] <= initial + SUM_{k<=h}(c[k]-d[k]) <= capacity_kwh
           (4) SUM_h (c[h] - d[h]) = 0                            neutrality
```

No integer variables are required. `battery_action` is not a decision variable —
it is a label read off the solution.

### 4a. Net out simultaneous charge + discharge — required

This model has no round-trip loss, so an LP may legitimately return `c[h]=50` and
`d[h]=30` in the same hour, which the schema forbids. Netting is provably
equivalent: the balance equation shifts by `+50-30` on one side and the state
update by the same amount, and netting only shrinks magnitudes, so rate limits
still hold. It is a teller recording one `+20` instead of a `+50` and a `-30`.

```text
net = c[h] - d[h]
net >  tol  -> action="charge",    battery_kwh = net
net < -tol  -> action="discharge", battery_kwh = -net
otherwise   -> action="idle",      battery_kwh = 0
```

Recompute the `E` trajectory from the **netted** values.

### 4b. Derive `grid_kwh`, never report the solver float — required

```text
grid_kwh[h] = demand[h] + charge_amt[h] - solar_used[h] - discharge_amt[h]
```

This makes the energy-balance equation hold **exactly** rather than within solver
tolerance. Clamp values in `(-1e-9, 0)` to 0.

### 4c. Infeasibility ladder — never 500

1. solve with all directives
2. if infeasible: solve base rules only, log loudly
3. if still infeasible: emit the always-valid trivial plan —
   `solar_used[h] = min(demand[h], eff_solar[h])`,
   `grid_kwh[h] = demand[h] - solar_used[h]`, battery idle all 24 hours.
   This always satisfies balance, bounds and neutrality.

## 5. Workstreams

| ID | Capability | Owner | Depends on | Exit criteria |
| --- | --- | --- | --- | --- |
| **WS-01** | API boundary, request/response models, error handling, response assembly, scaffold removal | M1 | — | both endpoints serve; C-1/C-4 exact; malformed → `400`; no 5xx on bad input; scaffold removed |
| **WS-02** | LLM interpreter: client, prompt, structured output, batching, timeout/retry/fallback, cache | M2 | C-1 | 10/10 public interpretations exact; ≥3 paraphrases per type; provider failure degrades without 5xx or key leak; call p95 inside budget |
| **WS-03** | Guardrail validator + constraint compiler | M2 | C-2, C-3 | all guardrails enforced; adversarial output never reaches the optimizer; invariant unconditional; merge rules table-tested; repairs logged |
| **WS-04** | LP model, netting, grid derivation, rounding, action labelling, infeasibility ladder | M1 | C-3, C-5 | all 10 cases replay clean; mean cost ratio ≥ 0.95; no simultaneous charge+discharge; neutrality within 0.01; totals match |
| **WS-05** | Replay validator + public-sample harness + failure injection | M3 | spec only | both replay modes; scorecard prints; gap + paraphrase suites; 5 failure injections; correctly flags a deliberately broken plan |
| **WS-06** | Dockerfile, GHCR publish, public deployment, README, CI reduction | M3 | WS-01 skeleton | public URL serves both endpoints from outside the network; image pullable by tag reaching `/health`; README reproduces on a clean environment, witnessed; CI green |

**WS-05 is owned by QA, not by the optimizer author, by design.** It validates
against the specification, not against the implementation. If one person writes
both, both inherit the same misreading and the error stays invisible until the
judge finds it.

### WS-05 has two replay modes — this distinction is the point

- **Mode A, self-consistent:** replay the plan against the directives the service
  itself returned. Used by the in-request validator.
- **Mode B, ground-truth:** replay the plan against the **expected** directives
  from the sample pack. This is what the judge does, and the only mode that
  catches "interpreted correctly but applied wrong" *and* "interpreted wrong".

## 6. Dependency Graph

```text
                  +--------------------------------------------+
                  | WS-05  Replay validator + harness (M3)     |  <- starts T+0, no deps
                  |        becomes the oracle for all below    |
                  +----------------+---------------------------+
                                   | verifies
       +---------------------------+---------------------------+
       v                           v                           v
  WS-01 API  ----------->  WS-03 Guardrails+Compiler  ---->  WS-04 Optimizer
    (M1)  |                       (M2)                          (M1)
          |                         ^
          |                         | raw dict
          |                 WS-02 LLM Interpreter (M2)
          |                         ^
          +------ C-1 types --------+
          |
          +---------->  WS-06 Docker + Deploy + README (M3)  <- skeleton is enough
```

**Critical path:** `WS-01 → WS-03 → WS-04 → integration rendezvous`.
**Parallel from T+0:** WS-05 (spec only), WS-02 (C-1 frozen), WS-06 (after the WS-01 skeleton).

**Riskiest boundary: WS-02 ↔ WS-03** — untrusted model output meeting
deterministic validation. Exercise it early with a hand-written fake provider
response, long before the real provider is wired in. Do not discover it at 22:00.

## 7. Git Topology

```text
main                                  <- PR-only for workstream work
+-- feat/ws-01-api-contract           (M1)
+-- feat/ws-02-llm-interpreter        (M2)
+-- feat/ws-03-guardrails-compiler    (M2)
+-- feat/ws-04-optimizer-materializer (M1)
+-- feat/ws-05-replay-harness         (M3)
+-- feat/ws-06-deploy-docker-readme   (M3)
```

No `ws/` parent branches. Each workstream is a single bounded change by a single
owner with no subpart assembly, so a shared parent would add merge surface for no
benefit.

Merge order follows the dependency graph: WS-01, then WS-05, then the rest.
**Merge ≠ integration ≠ Workstream Complete.** Nothing is marked complete on a
green PR alone.

## 8. Risks

| # | Risk | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| R1 | LLM key/quota unverified | eligibility + 60 pts | one live structured-output call before any planning | M2 |
| R2 | Public reachability unproven | 10 pts + judging path | deploy `/health` skeleton by T+45 | M3 |
| R3 | Local Docker daemon not running | 4 pts | build and push via GitHub Actions; no local Docker needed | M3 |
| R4 | p95 ≤ 5s with an LLM in-path | 3 pts | fast model, one batched call, capped tokens, cache, hard client timeout | M2 |
| R5 | LP degeneracy → simultaneous charge+discharge | schema + validity | netting (§4a) + property test | M1 |
| R6 | Float drift breaks balance or totals | penalty + validity | derive grid (§4b); round-then-sum (C-5) | M1 |
| R7 | Relative quantities mis-converted | interpretation cascade | capacity in the prompt; SAMPLE-03 regression | M2 |
| R8 | Our misinterpretation makes the LP infeasible | case validity | infeasibility ladder (§4c) | M1 |
| R9 | Hidden notes probe uncovered combinations | 25 pts | paraphrase + combination suites over `problem.md §19` gaps | M2 + M3 |
| R10 | `ci.yml` red on every PR (Postgres/alembic) | attention drain | reduce CI early in WS-06 | M3 |
| R11 | Template scaffold in `Initial commit` | eligibility question | README credits disclosure + delete unused scaffold | M3 |
| R12 | Four-hour window, already consumed | everything | freeze at T+200 regardless of state | M3 |
| R13 | Provider outage during judging, after submission | total | secondary provider in the interpreter | M2 |
