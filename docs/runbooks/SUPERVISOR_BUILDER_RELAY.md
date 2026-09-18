# Supervisor–Builder Relay

Use this optional, model-agnostic runbook when a team chooses a separate
Supervisor Agent and Builder Agent for a member-aware workstream. It adds an
operational relay; it is not a universal HADF lifecycle stage, completion gate,
or replacement for the canonical [Team Execution](TEAM_EXECUTION.md),
[Workstreams](../core/WORKSTREAMS.md), [Definition of Done](../core/DEFINITION_OF_DONE.md),
or [Decision Authority](../core/DECISION_AUTHORITY.md) guides.

## Authority and Assignment

```text
Official rules / organizer clarifications
-> official challenge / problem statement
-> problem.md
-> plan.md
-> execute.md
-> MEMBER_N.md routing
```

Repository evidence—artifacts, tests, migrations where applicable, Git and PR
state, and safe runtime or equivalent verification—establishes implemented
reality. `execute.md` is the canonical live execution state. `MEMBER_N.md` is
routing only: if it conflicts with `execute.md`, use `execute.md`, report the
routing drift, and do not guess or silently reconcile it.

No Supervisor Agent chooses a member's next workstream. If no active assignment
exists, stop and report that the member awaits Control Room or human assignment.

The normal pattern is one member, one primary active mutable assignment,
completion or handoff, repository reassignment, and fresh supervisory context.
It is a default, not global sequencing: different humans may work in parallel,
and explicit contributors may assist another workstream. Primary Owner means
accountability, not exclusive implementation. Reviewer/QA work may be
cross-cutting while a member has one primary mutable workstream; simultaneous
mutable work by one human requires explicit routing and appropriate workspace
isolation.

## Optional Relay

```text
Control Room / human assignment
-> execute.md + MEMBER_N.md routing
-> fresh Supervisor Agent -> "Member N" -> assignment reconstruction
-> Task Orientation -> Task Plan -> human Task Plan approval
-> Builder Plan-Mode Handoff -> Builder independent inspection
-> Builder Implementation Plan -> Supervisor reconciliation
-> Final Builder Implementation Handoff -> human implementation approval
-> Builder implementation -> focused verification -> self-review
-> Implementation Report -> Feature Reconstruction
-> Supervisor evidence check -> PR / independent QA handoff
-> merge / applicable integration and rendezvous
-> execute.md + routing update -> fresh Member N recovery
```

Task Orientation and the Task Plan retain their [Team Execution](TEAM_EXECUTION.md)
meaning: what and why, fit, ownership and exclusions, dependencies, applicable
Interface / Assumption Contracts, evidence, rendezvous, risks, and decisions.
After the Task Plan, stop. Only explicit approval such as `Task plan approved.`
permits the next relay step; it does not permit implementation.

## Builder Plan-Mode Handoff

After Task Plan approval, the Supervisor may provide expected scope and Git
topology, but labels it provisional. The Builder must make no edits and must
independently inspect relevant repository state, current status and branch,
remote branches, artifacts, tests, configuration, dependencies, recent history,
merged dependencies, shared-workstream-branch existence, required
synchronization, and expected PR target.

The Builder returns its own repository-grounded Implementation Plan. Where
applicable it records verified repository and Git state; clean or dirty state;
likely artifacts; realization sequence and exclusions; contracts and
dependencies; verification and rendezvous; actual base, working, optional shared
workstream branch, and PR target; synchronization; escalation conditions; and
exit criteria. Supervisor assumptions are not repository truth. No mutation is
authorized by this plan.

## Reconciliation and Final Handoff

The Supervisor reconciles the approved Task Plan, Master Design, `execute.md`,
member routing, Builder-observed repository and Git evidence, dependencies,
contracts, verification, and rendezvous requirements. The final handoff states
the approved scope and boundary, dependencies and contracts, verification,
rendezvous, escalation conditions, and verified Git procedure.

When Git actions apply, record only observed, approved facts:

```text
Base branch: <approved actual base>
Shared workstream branch: <existing / create / N/A>
Working branch: <feature/subpart branch>
PR target: <approved target>
Required synchronization: <approved procedure>
Branch retirement: <when the old bounded-change branch is no longer used>
```

Shared workstream branches are optional. Preserve one bounded change per feature
branch, conditional worktrees, separate clones for different humans, and the
existing no-destructive-Git rule. A completed subpart branch is not reused for a
later subpart: start the next bounded change from the current approved shared
state. For example, a feature branch may merge into an optional workstream
branch, be retired when authorized, and a later feature branch begins from the
latest shared workstream state.

Only explicit approval such as `Implementation plan approved. Implement.`
permits implementation. Commit, push, PR, merge, deletion, or history mutation
still requires its own required explicit authorization.

## Evidence Check and Handoff

After implementation, the Builder provides the canonical Implementation Report
and concise Feature Reconstruction: member, workstream, branch/context, changed
artifacts, implemented reality, verification, contract and dependency handling,
integration state, blockers, remaining work, divergence, current Git state, and
an evidence-backed proposed `execute.md` update.

The Supervisor checks plan adherence and evidence. It may return only:

```text
READY FOR PR / QA HANDOFF
NEEDS ADDITIONAL BUILDER VERIFICATION
NEEDS CORRECTIVE BUILDER WORK
NEEDS CONTROL ROOM DECISION
```

These are relay decisions, not completion states or new gates. Builder
self-review, supervisory evidence checking, and independent Reviewer/QA review
remain distinct. Use [QA Reviewer](../prompts/QA_REVIEWER.md) for an optional
dedicated QA, PR-review, or integration session. Review success never itself
authorizes merge; merge never proves integration or Workstream Complete.

## Reassignment and Recovery

For a new assignment, complete or hand off the old assignment, update
`execute.md`, update member routing, and record a useful checkpoint when needed.
Close a meaningful old Supervisor context where appropriate, then begin a fresh
Supervisor session with `Member N`. The Builder re-inspects repository and Git
reality before creating or switching to the new work branch. Do not use a giant
context-transfer prompt or continue the old feature branch into a new
workstream.
