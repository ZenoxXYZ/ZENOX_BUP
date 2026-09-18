# WS-02 provider runtime — measured resolution of the M2 handoff

Owner: Member 3 (QA / Integration). Raised by: M2 handoff, `feat/ws-02-llm-interpreter`
(`06a7dad`). Every number here is a real call made against the team's live keys on
2026-09-18, not an estimate.

M2 is right that the local failure is **timeout configuration, not credentials**.
The measurements below say why, and give the exact values to change.

## Measurement

Full WS-02 shape: one batched request, three operator notes, six-type enum,
explicit hour lists, `temperature=0`. Three calls per model.

| Model | call 1 | call 2 | call 3 | All three directives correct? |
| --- | --- | --- | --- | --- |
| `gemini-3.6-flash` | 7.98s | **HTTP 503** | **HTTP 503** | yes, on the one call that returned |
| `gemini-3.1-flash-lite` | **1.36s** | 4.50s | 4.08s | **yes, 3/3** |
| `openai/gpt-oss-120b` (raw HTTP) | 0.89s | — | — | yes |

"Correct" means all three of: `solar_reduction` hours `[13,14]` (end-exclusive, not
`[13,15]` and not `[13,14,15]`), `factor` 0.2 (fraction remaining), and
`minimum_battery_reserve` hours `[18..23]` with value 100.

## Root cause of the local failure

The ladder on the branch budgets **5.0 seconds in total**:

| Step | `interpreter.py` | Configured | Measured need |
| --- | --- | --- | --- |
| Gemini normal | line 246 | **2.5s** | 1.36–4.50s on flash-lite; 7.98s on 3.6-flash |
| Gemini strict retry | line 250 | **1.0s** | same range — a retry cannot be faster than the first call |
| Groq secondary | line 257 | **1.5s** | 0.89s observed, but no headroom for a p95 |

Every configured timeout is below the measured latency of the model it guards.
The 2.5s primary expires mid-generation, the 1.0s retry cannot succeed at all, and
1.5s leaves Groq no margin. M2's observed ~3.33s elapsed against a 2.5s deadline
is exactly this.

## Fix 1 — change the default model (the larger problem)

`interpreter.py:329` defaults to `gemini-3.6-flash`. That model returned **HTTP 503
"experiencing high demand" on 2 of 3 calls** and took 7.98s on the one that
succeeded. It is not viable as a primary under a 30-second judge ceiling.

`gemini-3.1-flash-lite` answered 3/3, in 1.36–4.50s, and got every trap right.

    GEMINI_MODEL=gemini-3.1-flash-lite

Already set in `.env` and `.env.example`. Change the in-code default at
`interpreter.py:329` to match, so a missing env var does not silently select the
unreliable model. Note `gemini-2.5-flash` is HTTP 404 for this key
("no longer available to new users") — see F11.

## Fix 2 — widen the timeouts

Correctness outranks latency by a wide margin here: interpretation is 25 points and
cascades into 35 more, while latency is 3 points and Band 1 is anything at or under
5 seconds. A timeout that fires early does not save 3 points, it forfeits up to 60.

| Step | From | To | Why |
| --- | --- | --- | --- |
| Gemini normal | 2.5s | **8.0s** | covers the 4.50s worst case with margin, and a 7.98s outlier |
| Gemini strict retry | 1.0s | **8.0s** | a retry is not faster than the call it repeats |
| Groq secondary | 1.5s | **6.0s** | p95 headroom over the 0.89s observed |

Worst case 22.0s, inside the 30s ceiling with 8s to spare. The typical path is one
Gemini call at 1.4–4.5s, which stays in latency Band 1.

## Fix 3 — Groq default model

`interpreter.py:368` defaults to `openai/gpt-oss-20b`, which invented the directive
type `"solar"` in earlier testing. `openai/gpt-oss-120b` was equally fast and more
accurate. The strict enum in the provider DTO constrains both, so this is a
robustness preference rather than a defect.

    GROQ_MODEL=openai/gpt-oss-120b

## Fix 4 — Groq blocks the default Python User-Agent (new, F18)

A raw `urllib.request` call to Groq returns **HTTP 403 `error code: 1010`**, a
Cloudflare rejection of the default `Python-urllib/3.x` User-Agent. Setting any
User-Agent header fixes it: the identical request then succeeded in 0.89s.

    urllib default (no UA set)     0.07s  HTTP 403 b'error code: 1010\n'
    explicit UA                    0.89s  OK

This does **not** affect `interpreter.py`, which uses the official `groq` SDK and
sends its own User-Agent. It is recorded because the symptom is indistinguishable
from a revoked key, and any raw-HTTP fallback or diagnostic script must set a
User-Agent or it will produce a false credential alarm.

## D4 provider ordering — no change required

M2 correctly refused to reverse the ladder without a human decision. With the model
swap, no reversal is needed: `gemini-3.1-flash-lite` at 1.36–4.50s is comfortably
inside Band 1 and handled every semantic trap. **D4 stands as written** — Gemini
primary, Gemini strict retry, Groq secondary. F8 is resolved by changing the model,
not the architecture.

## Corrections to earlier QA findings

**F7 is resolved, and my original report overstated it.** I observed
`hours: [13, 15]` from Gemini using a weak single-note prompt with a free-form
`STRING` type and no instruction about hour expansion. Under WS-02's actual prompt —
six-type enum plus "explicit list of every affected hour integer" —
`gemini-3.1-flash-lite` returned `[13, 14]` on 3/3 calls. The trap was in my probe,
not in the provider. M2's prompt already handles it, and the guardrail cardinality
check remains worth keeping as defence in depth.

**F9 stands and M2's fix is right.** Providers do invent type names
(`solar_output_reduction`, `solar`). The strict enum in the provider DTO is the
correct remedy and should not be relaxed.

## Still unverified

- **End-to-end WS-02 to WS-03 to optimizer on a merged tree.** Once WS-02 merges and
  the `interpret` and `compiler` seams resolve, `tests/harness.py` must be re-run.
  The oracle already proves the downstream path is exactly optimal given true
  directives (verification log rows 33–36), so interpretation is the last variable.
- **p50/p95 against the public URL.** `tests/latency.py` exists; there is no
  deployed URL yet (blocker B2). Localhost numbers are a floor, not the submission
  figure.
- **Whether Gemini 503 rates worsen near the deadline.** Two of three calls to
  `gemini-3.6-flash` failed this way. If flash-lite starts returning 503s, the Groq
  secondary is what saves the round, so it must be kept warm and tested, not left as
  an untested code path.
