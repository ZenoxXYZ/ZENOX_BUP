# Team Execution

Use this runbook when an actual challenge repository has instantiated a
lightweight member-routing file at `docs/team/MEMBER_N.md`. It complements the
canonical [Workstreams](../core/WORKSTREAMS.md), [Definition of Done](../core/DEFINITION_OF_DONE.md),
and [Decision Authority](../core/DECISION_AUTHORITY.md); it does not replace them.

## Authority and Routing

```text
AGENTS.md     -> operating policy
problem.md    -> approved requirements
plan.md       -> approved design
execute.md    -> canonical live execution state
review.md     -> verification and findings
MEMBER_N.md   -> personalized routing only
```

`Member N` means: reconstruct this member's current assignment, teach the
task, decompose it, and produce a Task Plan. It is not approval to edit or
implement.

Resolve `Member N` to `docs/team/MEMBER_N.md` for the actual team size. The
generic repository supplies a template, not live assignments. If the selected
file does not exist, stop and report that member routing has not been
instantiated. If routing conflicts with `execute.md`, `execute.md` wins:
report routing drift and do not guess or silently reconcile it.

## Optional Relay and Dedicated QA

Teams may use the optional [Supervisor–Builder Relay](SUPERVISOR_BUILDER_RELAY.md)
when a separate Supervisor Agent prepares and reconciles a Builder handoff. It
does not change `Member N`, planning or approval gates, `execute.md` authority,
or the canonical completion model. A Builder still independently inspects
repository and Git reality before final branch or workspace actions.

For independent PR discovery, review, QA-queue reconstruction, or post-merge
integration requests, use the [Dedicated QA Reviewer prompt](../prompts/QA_REVIEWER.md)
with the canonical Reviewer workflow. A QA/review responsibility may be
cross-cutting; member reassignment still updates `execute.md` and routing before
a fresh `Member N` reconstruction.

## Activation and Context

On activation, read:

1. `AGENTS.md`
2. `problem.md`
3. `plan.md`
4. `execute.md`
5. `review.md`
6. this runbook
7. the selected `docs/team/MEMBER_N.md`

Then inspect only the relevant branch/status, assigned artifacts, tests or
verification assets, dependencies, and recent history where useful.

Reconstruct at context boundaries, not at every message: fresh Builder
session, member activation, assignment change, material shared-state or branch
change, relevant contract change, or possible stale context. In an unchanged
workstream session, reuse established relevant context rather than rereading
unrelated repository material.

## Task Orientation and Planning

Before planning, explain the workstream's **What**, **Why**, optional accurate
analogy, **System Connection** (what comes before -> this workstream -> what
comes after), **Boundary**, **Dependencies**, **Interfaces / Assumptions**,
**Risks**, and **Success** evidence. Keep teaching task-local.

Decompose at two levels. First, use only applicable conceptual responsibilities
such as input, core behavior, state, output, failure behavior, artifact
production, integration, and verification. Then translate the approved concept
into concrete realization work appropriate to the artifact; do not require
software-only vocabulary.

### Task Plan

The Task Plan answers **what are we building and why?** Include purpose,
analogy where useful, system flow, owned boundary, dependencies,
contracts/assumptions, conceptual decomposition, proposed approach,
verification and rendezvous strategies, risks, and decisions needed. End with
exactly one status:

```text
TASK PLAN STATUS:
READY FOR HUMAN REVIEW
NEEDS CLARIFICATION
BLOCKED
```

Then stop without editing. Only explicit approval such as `Task plan approved.`
permits an Implementation Plan; it does not permit implementation.

### Implementation Plan

The Implementation Plan answers **exactly how will the approved solution be
realized?** Include the approved approach summary, verified current state,
artifacts/interfaces to inspect, likely changes, exclusions, realization
sequence, contract impact, verification and rendezvous sequences, applicable
commands/procedures, expected evidence, escalation conditions, and exit
criteria. Do not repeat the Task Plan. End with exactly one status:

```text
IMPLEMENTATION PLAN STATUS:
READY FOR HUMAN APPROVAL
NEEDS CLARIFICATION
BLOCKED
```

Then stop. Only explicit implementation approval, such as `Implementation plan
approved. Implement.`, permits edits. `Member N`, `go on`, discussion,
questions, or Task Plan approval do not.

A combined Task + Implementation Plan is allowed only when the human explicitly
authorizes it for a genuinely tiny, low-risk task with no material architecture,
contract, dependency, or integration ambiguity.

## Execution, Report, and Reconstruction

After approval, follow:

```text
INSPECT -> IMPLEMENT / REALIZE -> FOCUSED VERIFY -> SELF-REVIEW
-> INTEGRATION CHECK -> REPORT
```

Stop for a human decision before any material architecture, shared-contract,
other-member-scope, critical-assumption, invariant, or evaluation-critical
change.

The Implementation Report records member, workstream, branch/context, changed
artifacts, implemented reality, verification/evidence, contract adherence,
integration state, blockers, remaining work, divergence, and a suggested
evidence-backed `execute.md` update. It does not claim Workstream Complete
automatically.

Feature Reconstruction follows the report. It concisely explains the
implemented reality: member, workstream, what and why, final artifact flow,
implementation structure, inputs/outputs/interfaces, contracts/assumptions,
state or physical effects (or N/A), failure behavior, verification/evidence,
integration points, handoff information, divergence, limitations, current
completion gate, suggested execution-state update, and recommended next action.

Feature Reconstruction describes one workstream's implemented reality. Project
Reconstruction describes the final assembled solution; Feature Reconstruction
may feed it but does not replace it.

Assess only `NOT LOCAL COMPLETE`, `LOCAL COMPLETE`, or `MERGE READY` after
reconstruction. Claim Workstream Complete only when the canonical completion
conditions hold: artifact, contracts/assumptions, applicable rendezvous,
verification, evidence, and exit criteria. Merge alone is insufficient.

Where applicable after merge: synchronize, exercise the real boundary, remove
temporary assumptions or mocks, verify integrated behavior, collect evidence,
and update canonical workstream state.

## Reassignment and Efficiency

For reassignment: Control Room updates `execute.md`, the routing file is updated,
the repository checkpoint is recorded, and a later `Member N` activation
reconstructs the new assignment. Do not use a giant context-transfer prompt.

Keep routing files small, reference canonical sources, inspect only relevant
state, avoid repeating a Task Plan in an Implementation Plan or either plan in
Feature Reconstruction, and keep task teaching concise.
