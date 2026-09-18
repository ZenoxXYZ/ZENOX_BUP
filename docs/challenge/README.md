# Official Challenge Sources

Organizer-supplied material for the BUP CSE Fest 2026 online preliminary, kept in
the repository so every member and every agent session reconstructs from the same
authority instead of from somebody's `~/Downloads`.

| File | Status |
| --- | --- |
| `BUP_CSE_FEST_2026_Preliminary_Problem_Statement_GridWise_LLM.pdf` | **Canonical.** Behaviour, endpoints, schemas, directive types, guardrails, battery and energy rules, time and factor semantics, tolerance. |
| `BUP_CSE_FEST_2026_Participant_Guide_&_Evaluation_Rubric_GridWise_LLM.pdf` | **Canonical.** Round timing, deliverables, deployment, Docker fallback, LLM policy, security, scoring weights, penalties, latency, submission, tie-breaks. |
| `BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json` | **Canonical.** Ten worked cases, each with `input`, `expected_output` and `rationale`. |
| `problem-statement.extracted.md`, `participant-guide.extracted.md` | **Lossy convenience copies.** Text extracted from the PDFs, with the line breaking mangled. Readable by tools that cannot open a PDF. Never cite them against the PDF. |

Conflict rule, stated by both documents: the **Problem Statement wins on
behaviour, the Guide wins on deployment and evaluation policy.**
`problem.md` holds our approved interpretation; where this material and
`problem.md` disagree, the source wins and `problem.md` is corrected.

## Using the sample pack

It is a **validation corpus only** (`problem.md §19`). Case ids, note wording,
numeric values and reference schedules must never be hard-coded, matched, or
shipped in the service. Equivalent optimal schedules are explicitly accepted, so
compare recalculated cost, never the plan itself.

Cost ratio per case is `min(1, reference_total_cost_bdt / our_total_cost_bdt)`.

**A ratio at or above 1.0 is a red flag, not a win.** It means our schedule came
in cheaper than the organizer's optimum, which in a correctly constrained model
means we violated something -- most often by applying a directive incompletely
and spending solar or grid we were not entitled to. Those cases score zero on
ground-truth replay. Investigate every ratio >= 1.0 as a validity failure.
