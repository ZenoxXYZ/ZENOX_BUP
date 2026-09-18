# Definition Of Done

Generated output is not complete work. Completion is evidence-driven and must
fit the approved [Challenge Profile](CHALLENGE_CLASSIFICATION.md), [Critical
Proof Path](PROOF_MODEL.md), [Proof Package](PROOF_MODEL.md), and [Realization
Boundary](PROOF_MODEL.md).

## Workstream Status

- **TODO** — approved work has not started.
- **IN PROGRESS** — construction or integration work is active.
- **VERIFYING** — required verification is actively being run or evidence is
  actively being gathered; it does not mean “almost done.”
- **BLOCKED** — a known dependency, failure, or unavailable resource prevents
  progress.
- **NEEDS CLARIFICATION** — a required human or design decision is missing.
- **VERIFIED** — the required verification and evidence currently pass for the
  stated claim. This is distinct from Workstream Complete.

## Completion Gates

### Local Complete

The approved artifact exists in the local workspace, relevant local
verification has passed, and evidence, limitations, and unverified items are
recorded. Required external integration may still be pending.

### Merge Ready

Where branches and pull requests apply, Merge Ready is a repository/Git
workflow gate: the change is Local Complete, the diff is reviewed, configured
CI passes, and required review findings are resolved or explicitly accepted. It
is not a universal engineering phase and does not prove integration.

### Workstream Complete

A workstream is complete if and only if:

```text
required artifact exists
+ governing interfaces / assumptions hold
+ integration has been exercised where applicable
+ required verification passes
+ required evidence exists
+ exit criteria are satisfied
```

For branch-governed work, an approved source-control checkpoint may be an exit
criterion. Merge does not equal integration; CI does not equal review; review
does not equal verification; and verification alone does not equal Workstream
Complete.

## Verification And Evidence

Select mechanisms from the evaluation contract and artifact: tests, checkers,
benchmarks, model metrics or error analysis, physical measurement, telemetry,
calibration, simulation validation, CAD inspection, security reproduction and
retest, standards conformance, manual review, or demo rehearsal. No mechanism
is universal.

## Solution Freeze

Solution Freeze is the point after which new scope is normally rejected and
effort shifts to verification, integration, evidence, submission, and critical
fixes. Its approximate zone is selected from the approved timebox strategy;
official Code Freeze, deadlines, and submission rules take precedence.

Feature Freeze remains the Product Build specialization of Solution Freeze;
see the [Feature Freeze runbook](../runbooks/FEATURE_FREEZE.md).

Demo Freeze is optional and applies only where a live demo or presentation is
required. It is a presentation-state freeze, not a replacement for universal
Solution Freeze or required submission packaging.
