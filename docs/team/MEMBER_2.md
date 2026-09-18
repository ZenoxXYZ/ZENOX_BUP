# Member 2 — Routing

Routing only. Canonical sources: `AGENTS.md` (policy) · `problem.md`
(requirements) · `plan.md` (design + contracts) · `execute.md` (live state) ·
`review.md` (verification) · `docs/AGENT_WORKFLOW.md` (reconstruction procedure).

If this file conflicts with `execute.md`, **`execute.md` wins** — report the
drift, do not guess.

| | |
| --- | --- |
| Name / GitHub | [@abidhasan9538](https://github.com/abidhasan9538) |
| Role | Builder — highest-weighted seat on the team |
| Current assignment | **WS-02** — LLM interpreter: client, prompt, structured output, batching, timeout/retry/fallback, cache |
| Then | **WS-03** — deterministic guardrail validator + constraint compiler |
| Branch | `feat/ws-02-llm-interpreter`, then `feat/ws-03-guardrails-compiler` |

## Why this seat carries the most weight

The judge replays our schedule against the **organizer's** ground-truth
directives, not ours. One misread note therefore loses its interpretation credit
(25-pt pool), invalidates the case on replay (25-pt pool), and zeroes that case's
optimization credit (10-pt pool). **60 of 100 points cascade from extraction
quality.** Prompt work outranks solver work on this challenge.

## Owned

- `backend/services/interpreter.py` and the prompt module
- `backend/logic/guardrails.py`, `backend/logic/constraints.py`
- Contract shapes **C-2** (`Directive`) and **C-3** (`ConstraintSet`) — `plan.md §3`

You hold both sides of the untrusted boundary deliberately: it keeps the guardrail
honest about what the model actually emits rather than what you hoped it would.

## Do not touch

`backend/main.py`, `backend/routes/`, `backend/schemas/`,
`backend/logic/optimizer.py`, `backend/logic/materializer.py` (M1) ·
`backend/logic/replay.py`, `tests/`, `Dockerfile`, `README.md`,
`.github/workflows/ci.yml` (M3)

## Key references

- Mandatory LLM requirement and what fails it — `problem.md §4`
- Six directive types and exact shapes — `problem.md §5`
- **The three semantic traps** — `problem.md §6`: end-exclusive time,
  factor-as-fraction-remaining, and capacity-in-the-prompt for relative reserves
- Guardrail list — `problem.md §11`
- Interpretation regression targets (all 10 public cases) — `problem.md §19`
- Coverage gaps the hidden set will probe — `problem.md §19`
- Merge rules for overlapping directives — `plan.md §3` C-3
- Provider ladder — `execute.md` D4 · guardrail policy — `execute.md` D5

## Non-negotiables

1. **One batched call for all 1–3 notes**, not one per note. Latency is 3 points
   and a timeout counts as a failure.
2. **Send `battery.capacity_kwh` and `minimum_energy_kwh`**; do **not** send the
   24 hourly rows. Withholding them structurally enforces the no-invention
   guardrail and saves latency.
3. **No regex or phrase-matching interpreter at any tier** — named non-compliant,
   and it muddies eligibility for ~2 reliability points. Use the secondary
   provider for resilience instead.
4. **Repair-first guardrails** (D5). Repairing `[14,13]` earns hour credit;
   rejecting forfeits the note *and* invalidates the case. Log every repair — if
   you are repairing constantly, the prompt is wrong.
5. **Never log or return the API key, a secret-bearing prompt, or a stack trace.**

## Standing authorization

Combined Task + Implementation Plan is pre-authorized. Stop for a human decision
before changing C-1 … C-6 or touching another member's files. Do not commit or
push unless explicitly requested.

## First action — blocker B1

Before any planning: confirm a working LLM key and make **one live
structured-output call**. Nothing else matters until that works — it gates
eligibility and 60 points. If no key exists, create a Google AI Studio (Gemini)
key: free, instant, no card. Report the model name, observed latency, and whether
JSON-schema mode worked.

Then exercise the WS-02 ↔ WS-03 boundary early with a hand-written fake provider
response. It is the riskiest boundary in the system — do not discover it at 22:00.
