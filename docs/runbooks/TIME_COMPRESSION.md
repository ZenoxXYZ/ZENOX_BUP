# Timebox And Lifecycle Guidance

This is HADF's single canonical source for timebox profiles and timing
heuristics. The lifecycle remains:

```text
UNDERSTAND -> CLASSIFY -> CHOOSE -> BOUND -> BUILD -> INTEGRATE -> PROVE -> FREEZE -> SUBMIT
```

These are functions, not fixed clock blocks. Compress scope, not required
proof or critical dependency order.

## Authority And Selection

Apply timing authority in this order:

```text
official event rules, deadlines, checkpoints, inspections, and upload windows
-> challenge-specific delivery constraints
-> selected HADF timebox strategy
-> generic guidance
```

Select a strategy from the Challenge Profile, event duration, mandatory
checkpoints, evaluation contract, and dependencies or risk. Duration alone
does not select the strategy.

## Optional Heuristics

These percentage bands are optional planning heuristics, never mandatory
targets. They may overlap and need not total exactly.

| Lifecycle function | Optional planning band |
| --- | --- |
| Understand / Classify | 10–15% |
| Choose / Bound | 10–15% |
| Build | 45–55% |
| Integrate / Prove | 15–20% |
| Freeze / Submit | 10–15% |

## Profiles

| Profile | Scope pressure | Integration and proof | Freeze and delivery |
| --- | --- | --- | --- |
| Short — 3–4h | Reduce immediately to the smallest credible Critical Proof Path. | Exercise the riskiest boundary and collect first evidence as soon as possible. | Freeze early; protect required evidence and delivery packaging. |
| Standard — 6–8h | Keep only a few core workstreams; cut optional work early. | Integrate risky boundaries during Build and accumulate evidence continuously. | Reserve a visible final zone for proof, critical fixes, and delivery. |
| Extended — 12–24h | Iterate only after a credible proof exists. | Use incremental integration and broader verification. | Choose a freeze zone before the final delivery period, not a fixed hour. |
| Multi-day | Use approved milestones without restoring deferred scope automatically. | Schedule integration and evidence checkpoints around dependency risk. | Align freeze with official milestones and final delivery. |
| Open-ended / async | Use approved milestones rather than elapsed-clock assumptions. | Integrate at dependency and review milestones. | Freeze only against an approved release or submission boundary. |

## Proof, Integration, And Freeze

Identify proof requirements during Understand and Classify. Accumulate evidence
during Build; do not defer it to final documentation. Integrate early enough
to expose the riskiest independently developed boundary while correction time
remains. That boundary may be software, model, physical, simulation, design,
or evaluation-harness work; record integration as `N/A` only with rationale.

Solution Freeze is universal: after its selected zone, reject non-critical
scope and concentrate on integration, verification, evidence, critical fixes,
and delivery. Feature Freeze remains the Product Build specialization. Demo
Freeze is used only where a live presentation or demonstration is required.

Keep reconstruction proportionate to remaining time and the delivery need.
