# Problem — GridWise LLM-Assisted Energy Optimization

Normalized, approved challenge truth for the BUP CSE Fest 2026 online preliminary.
This file replaces the generic template. It is the requirements authority for this
repository; `plan.md` holds the approved design and `execute.md` holds live state.

## 1. Round Facts

| Item | Value |
| --- | --- |
| Round | Online Preliminary |
| Window | 19:00–23:00 BST (4 hours) |
| Required service | Deployed public HTTP API |
| Health endpoint | `GET /health` → `{"status":"ok"}` |
| Main endpoint | `POST /optimize-energy` |
| Planning horizon | 24 hourly intervals |
| Operator notes | 1–3 natural-language strings per scenario |
| LLM | **Mandatory** in the operator-note interpretation path |
| Data | All synthetic. No live campus, utility, billing or personal data. |

## 2. Source Authority

| Source | Canonical for |
| --- | --- |
| Problem Statement | behaviour, endpoints, schemas, directive types, `structured_adjustment` shapes, guardrails, battery/energy rules, time and factor semantics, optimization validity, tolerance |
| Participant Guide & Rubric | round timing, deliverables, deployment, Docker fallback, LLM policy, security, scoring weights, penalties, latency, submission, tie-breaks |
| Public Sample Cases JSON | validation corpus **only** — not hidden truth, never hard-coded |

Conflict rule, stated by both documents: **Problem Statement wins on behaviour,
Guide wins on deployment and evaluation policy.** No conflicts detected.

## 3. What The Service Does

One stateless HTTP service receives a 24-hour campus energy scenario plus 1–3
operator notes, and returns both a machine-checkable interpretation of every note
and the final 24-hour schedule.

A useful framing: a **translator** reads operator memos, a **compliance officer**
refuses anything not on the approved form, and a **dispatcher** buys electricity
for 24 hours as cheaply as possible under the approved memos. The decisive detail
is that the auditor re-does the dispatcher's arithmetic using the **true** memos,
not our translation — so a mistranslation is punished twice.

## 4. Mandatory LLM Requirement

A language-capable generative model must sit in the operator-note interpretation
path, and its structured output must be what reaches the optimizer.

Failing this is not a deduction — the Guide's penalty table makes the team **not
eligible for the final preliminary shortlist**, and artifact review may inspect
the repository and architecture to confirm compliance.

Forbidden:
- LLM used only for `plan_summary`, documentation or cosmetic text
- hard-coded phrase matching as the **sole** interpreter

Allowed and expected: deterministic normalization, JSON validation, guardrails,
and application of the structured directives.

## 5. Supported Directives

| `directive_type` | Meaning | Required `structured_adjustment` | Deterministic optimizer effect |
| --- | --- | --- | --- |
| `solar_reduction` | usable solar cut in listed hours | `{"hours":[...], "factor": n}` | `eff_solar[h] = solar_kwh[h] * factor` |
| `minimum_battery_reserve` | floor on stored energy | `{"hours":[...], "minimum_energy_kwh": n}` | `E_after[h] >= max(base_min, directive_min)` |
| `no_charge_window` | charging unavailable | `{"hours":[...]}` | `charge[h] = 0` |
| `no_discharge_window` | discharging unavailable | `{"hours":[...]}` | `discharge[h] = 0` |
| `max_grid_window` | per-hour grid import cap | `{"hours":[...], "max_grid_kwh": n}` | `grid_kwh[h] <= max_grid_kwh` |
| `no_op` | note does not affect today's schedule | `null` | none |

**Hard invariant:**
`directive_type == "no_op"` ⟺ `applies is False` ⟺ `structured_adjustment is None`.
Every other type carries `applies = True` and a matching adjustment shape.
`no_op` is the only type allowed with `applies = false`.

Every `hours` array: unique integers 0–23, **ascending**.

## 6. Semantics — The Three Traps

### 6.1 Time windows are start-inclusive, end-exclusive

```text
"1 PM to 3 PM"         -> [13, 14]
"noon until 2 PM"      -> [12, 13]        (SAMPLE-01)
"6 PM until 8 PM"      -> [18, 19]        (SAMPLE-04)
"2 AM until 5 AM"      -> [2, 3, 4]       (SAMPLE-02)
"from 6 PM until 9 PM" -> [18, 19, 20]    (SAMPLE-03, SAMPLE-05)
```

### 6.2 `factor` is the fraction REMAINING, not the reduction

```text
"drops to about 20%"                 -> 0.2
"an 80% reduction"                   -> 0.2
"roughly 25% of the forecast"        -> 0.25   (SAMPLE-01)
"roughly one-fifth of normal output" -> 0.2
"reduced by half"                    -> 0.5
```

Range: `0 <= factor <= 1`.

### 6.3 Relative quantities require battery capacity in the prompt

SAMPLE-03: *"at least 50% of the battery capacity"* with `capacity_kwh = 200`
→ `minimum_energy_kwh: 100`.

The model cannot convert a relative reserve without the capacity in context.
`battery.capacity_kwh` and `battery.minimum_energy_kwh` must be supplied to the
interpreter. Omitting this silently costs every percentage-expressed reserve in
the hidden set.

## 7. Battery And Energy Rules

```text
charge:     E_after = E_before + battery_kwh
discharge:  E_after = E_before - battery_kwh
idle:       E_after = E_before  AND  battery_kwh = 0

active_min[h] <= E_after[h] <= capacity_kwh
charge:    battery_kwh <= max_charge_kwh_per_hour
discharge: battery_kwh <= max_discharge_kwh_per_hour
0 <= solar_used_kwh <= eff_solar[h]        (surplus curtailed; NO grid export)
grid_kwh[h] <= grid cap where one applies

energy balance, EVERY hour:
  grid_kwh + solar_used_kwh + battery_discharge = demand_kwh + battery_charge

end-of-day neutrality:
  battery_energy_after_kwh[23] == initial_energy_kwh
```

Neutrality exists to stop the starting charge being spent as a free one-time
energy source.

Numeric tolerance: absolute **0.01 kWh / 0.01 BDT**.

## 8. Optimization Objective

```text
minimize  SUM over h=0..23 of  grid_kwh[h] * tariff_bdt_per_kwh[h]
```

**Validity strictly precedes cost.** An invalid case earns zero optimization
credit regardless of how cheap it is.

## 9. Request Schema

```json
{
  "scenario_id": "string",
  "operator_notes": ["string"],
  "hours": [
    {"hour": 0, "demand_kwh": 0, "solar_kwh": 0, "tariff_bdt_per_kwh": 0}
  ],
  "battery": {
    "capacity_kwh": 0,
    "initial_energy_kwh": 0,
    "minimum_energy_kwh": 0,
    "max_charge_kwh_per_hour": 0,
    "max_discharge_kwh_per_hour": 0
  }
}
```

- `operator_notes`: 1–3 entries, each non-empty after strip
- `hours`: exactly 24 entries; the set of `hour` values is exactly 0–23, unique

HTTP codes: `200` success · `400` malformed or structurally invalid · `422`
optional for well-formed-but-semantically-invalid · `500` controlled internal
only, never exposing secrets or stack traces.

## 10. Response Schema

```json
{
  "scenario_id": "string",
  "directive_interpretation": [
    {"note_index": 0, "applies": true, "directive_type": "string",
     "structured_adjustment": {}, "explanation": "string"}
  ],
  "hourly_plan": [
    {"hour": 0, "grid_kwh": 0, "solar_used_kwh": 0,
     "battery_action": "charge|discharge|idle", "battery_kwh": 0,
     "battery_energy_after_kwh": 0}
  ],
  "total_grid_kwh": 0,
  "total_cost_bdt": 0,
  "peak_grid_kwh": 0,
  "plan_summary": "string"
}
```

- `scenario_id` echoes the request verbatim
- one `directive_interpretation` entry per note, `note_index` ascending 0..N-1
- `hourly_plan` exactly 24 entries, `hour` ascending 0–23
- `battery_kwh` is a non-negative magnitude and **must be 0 when `idle`**
- all numerics finite and non-negative
- `plan_summary` and `explanation` are **not** matched byte-for-byte

## 11. Interpretation Guardrails

LLM output is untrusted structured data until deterministic validation passes.

- `directive_type` within the six supported values
- `note_index` identifies an existing note; each note appears exactly once
- hours: unique integers 0–23, ascending
- `factor` within `[0,1]`
- reserve values finite, non-negative, not exceeding capacity
- `max_grid_kwh` finite and non-negative
- no invention: base demand, solar, tariff and battery parameters may not change
- `applies` semantics per the §5 invariant
- final replay after optimization confirms every extracted directive was obeyed

**Safe failure:** malformed or unsupported model output must be handled in a
controlled way. The service must never invent a directive type and never crash.

## 12. Scoring Model

| Category | Pts | Breakdown |
| --- | --- | --- |
| LLM Directive Interpretation | 25 | 5 relevance/`no_op` · 5 type · 5 hours · 5 numerics+shape · 5 paraphrase robustness |
| Directive Application & Constraint Correctness | 25 | 10 ground-truth application · 5 balance/effective-solar · 5 battery transitions/bounds/rates · 5 action consistency + neutrality + non-negativity |
| Optimization Quality | 10 | `10 × mean(min(1, organizer_optimal / recalculated_team_cost))`; invalid case = 0 |
| API Contract & Schema | 10 | 2 endpoints/status · 2 request validation · 3 interpretation schema/order/types · 3 plan + top-level + `scenario_id` echo |
| Performance & Reliability | 10 | 2 health readiness · 3 p95 latency · 3 stability/failure rate · 2 controlled failure + secret safety |
| Deployment & Docker Fallback | 10 | 3 live reachability · 4 pullable image reaching `/health` · 2 clean startup · 1 no judge debugging |
| Documentation & Local Reproducibility | 10 | 3 clean quickstart · 2 env/provider docs · 2 sample test procedure · 1 architecture explanation · 1 Docker instructions · 1 deps/limits/secrets |
| **Total** | **100** | 3-minute video carries **zero** base points — tie-break only, but tie-break priority 1 |

Latency bands: p95 ≤ 5s → 3/3 · >5–15s → 2/3 · >15–30s → 1/3 · >30s → 0/3 and
the request counts as a failure.

### Implications that shape our decisions

1. **60 points cascade from interpretation accuracy.** A misread note loses its
   interpretation credit, invalidates the case on ground-truth replay, and zeroes
   that case's optimization credit. Prompt quality outranks solver sophistication.
2. **20 points are non-algorithmic** (Docker fallback + README reproducibility),
   fully parallelizable, and cannot be rushed at 22:45.
3. **Optimization Quality is ratio-scored and only 10.** A merely-valid good
   schedule banks most of it; a heuristic that risks *invalidity* attacks the
   25-point pool to protect the 10-point one.
4. **Latency is essentially all LLM.** The solver runs in milliseconds.
5. **Never return 5xx.** Malformed → 400. Provider failure → controlled. Infeasible
   → valid base-rules schedule with 200.
6. **Do not polish prose.** `plan_summary` and `explanation` are unscored on wording.

## 13. Challenge Profile

```text
Starting State:        Greenfield compute service. Spec supplied up front. Repo held only
                       generic template scaffold, none of it load-bearing.

Engineering Objective: Build and publicly deploy one HTTP service converting natural-language
                       operator notes into deterministically-validated structured directives,
                       applying them to a constrained 24-hour energy LP, returning exact
                       machine-checkable JSON inside a 30 s ceiling.

Evaluation Contract:   Black-box automated hidden-test harness, 100 points over 7 weighted
                       categories, scored against organizer ground truth with independent
                       hour-by-hour replay, plus two artifact checks worth 20.

Dominant Artifact:     A running, publicly reachable HTTP endpoint. Not a repository, not a
                       document, not a UI.

Realization/Proof:     API conformance under synthetic data, proved by independent replay of
                       our own output against the specification — the judge's own operation.
```

**This is not Product Build.** `docs/playbooks/product-build.md` excludes
"a fixed-schema, constrained hidden-checker API task" by name, which is exactly
this. Golden Path and MVP vocabulary do not apply; Minimum Winning Scope and
Critical Proof Path do.

## 14. Minimum Winning Scope

1. `GET /health` → `{"status":"ok"}`, ready within 60 s of start
2. `POST /optimize-energy` with exact request validation
3. LLM interpretation of all notes in the constraint-producing path, one batched call
4. Deterministic guardrail validation of that output
5. All six directive types, correct `no_op` detection, correct `applies` semantics
6. Correct deterministic application of each type
7. LP schedule valid under effective solar, balance, bounds, rates, neutrality
8. Final replay validator over the exact JSON about to be returned
9. Totals recomputed from the rounded `hourly_plan`
10. Controlled failure for malformed input, provider failure, invalid model output, infeasibility
11. Public reachable deployment
12. Pullable Docker fallback image, no baked secrets, binds `0.0.0.0`
13. Self-contained README with clean-environment quickstart

## 15. Critical Proof Path

```text
judge POSTs a scenario to the PUBLIC base URL
  -> request schema validated                     (400 on malformed, never 500)
  -> one batched LLM call interprets all 1-3 notes with battery capacity in context
  -> guardrail validator normalizes and accepts/rejects the structured output
  -> directives compiled into per-hour bounds
  -> LP minimizes grid cost subject to balance, bounds, rates, neutrality
  -> materializer nets charge/discharge, derives grid, rounds
  -> replay validator re-checks every rule against the final JSON
  -> 200 with exact schema, under 5 s
```

Failure-path proof is equally required:

| Injected failure | Required observable |
| --- | --- |
| Malformed JSON / missing fields / 25 hours / 4 notes | `400`, controlled body |
| LLM provider timeout or 5xx | controlled response, no 5xx, no key leaked |
| Model returns unsupported type or broken shape | guardrail rejects, nothing invented |
| LP infeasible | valid base-rules schedule, `200` |
| Repeated identical requests | stable, no drift, no leak |

## 16. Proof Package

| Claim | Evidence | Owner | What it does NOT prove |
| --- | --- | --- | --- |
| Service ready | `/health` → ok <60 s cold | M3 | sustained availability |
| Schema exact | all 7 top-level, 5 interpretation, 6 plan fields; `scenario_id` echoed | M3 | hidden schema edges |
| Interpretation correct | 10/10 public cases match expected semantics | M2 | hidden paraphrases |
| All 6 types + `no_op` | one passing assertion per type | M2 | unseen phrasings |
| Paraphrase robustness | ≥3 paraphrases per type resolve identically | M2 | organizer wording |
| Guardrails reject | injected malformed outputs rejected, not applied | M2 | every adversarial shape |
| Energy balance | every hour, all cases, within 0.01 | M3 | hidden numeric combinations |
| Battery transitions/bounds/rates | hour-by-hour replay | M3 | — |
| Each directive obeyed | per-type assertion against the plan | M3 | — |
| Neutrality | `E[23] == initial` within 0.01 | M3 | — |
| Totals consistent | recomputed from `hourly_plan` | M1 | — |
| Optimization quality | cost vs the 10 reference optima, ratio logged | M1 | hidden optimality |
| Latency | p50/p95 over ≥20 calls against the **public URL** | M3 | judge's network |
| Controlled failure | the five injected failures | M3 | — |
| Docker fallback | `pull` + documented `run` → `/health`, clean machine | M3 | — |
| Reproducibility | teammate follows README on a clean environment | M3 | — |

## 17. Realization Boundary

```text
Target real system:   A live campus energy management system — real meters, utility tariff
                      feeds, a physical battery with round-trip losses and degradation,
                      safety interlocks, operators on an operational channel.

Hackathon realization: A stateless HTTP service over synthetic 24-hour scenarios. One LLM
                      call interprets supplied note strings. A linear program schedules a
                      lossless, instantaneous battery model. No hardware, no telemetry,
                      no persistence, no forecasting.

Evidence available:   Public-sample conformance, independent replay validation, latency
                      measurement, controlled-failure behaviour, containerized clean start.

Claims supported:     Given a well-formed synthetic scenario and 1-3 operator notes, the
                      service produces a deterministically-validated structured
                      interpretation and a feasible 24-hour schedule minimizing grid cost
                      under the stated GridWise rules and all applicable directives.

Claims NOT supported: Real-campus deployment. Utility or BMS integration. Forecast accuracy.
                      Battery efficiency, degradation or thermal behaviour. Safety
                      certification. Reliability beyond the judging window. Correctness on
                      note phrasings outside the tested distribution. Cost savings in BDT
                      for any real facility.
```

All challenge data is synthetic by the Problem Statement's own declaration. The
README and video must not overclaim.

## 18. Out Of Scope

Frontend · database · persistence · auth · dashboards · message queues ·
background workers · WebSockets · vector stores · multi-day horizons · battery
efficiency or degradation modelling · anything in `AGENTS.md §10`'s premature-
infrastructure list.

## 19. Public Sample Corpus

Ten worked cases. **Validation reference only.** Note wording, case IDs, numeric
values and reference schedules must never be hard-coded. Equivalent optimal
schedules are explicitly accepted; compare recalculated cost, not the plan.

| Case | Notes | Ground truth | Tests |
| --- | --- | --- | --- |
| 01 | 2 | `solar_reduction [12,13] f=0.25` + `no_op` | end-exclusive; fraction-remaining; distractor |
| 02 | 1 | `no_charge_window [2,3,4]` | hard charge block in cheap hours |
| 03 | 1 | `minimum_battery_reserve [18,19,20] 100` | percentage → absolute via capacity |
| 04 | 1 | `no_discharge_window [18,19]` | hard block during the expensive peak |
| 05 | 1 | `max_grid_window [18,19,20] 155` | per-hour grid cap |
| 06 | 3 | `solar_reduction [10,11] f=0.5` + `no_charge_window [14,15]` + `no_op` | two reals + distractor |
| 07 | 2 | `reserve [18,19,20,21] 90` + `max_grid [19,20] 180` | overlapping interacting constraints |
| 08 | 2 | `no_charge [11,12]` + `no_discharge [17,18]` | charge vs discharge kept distinct |
| 09 | 2 | `solar_reduction [11,12,13] f=0.2` + `no_op` | "80% reduction" wording |
| 10 | 3 | `reserve [18,19,20,21] 80` + `max_grid [19,20,21] 190` + `no_op` | three-way evening interaction |

### Coverage gaps the hidden set may probe

Write tests for these; the public corpus does not cover them.

- three simultaneous **real** directives (public maximum is 2 real + 1 `no_op`)
- `solar_reduction` combined with `minimum_battery_reserve` (never co-occur publicly)
- single-hour windows
- `factor` at exactly 0 and exactly 1
- windows crossing midnight
- ≥3 paraphrases per directive type
- relative phrasings: "half the capacity", "a fifth of normal solar"
- distractors using energy vocabulary that change nothing today
