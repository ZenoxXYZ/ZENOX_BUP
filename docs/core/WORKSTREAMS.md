# Workstreams

## Canonical Definition

A workstream is a bounded engineering objective with one accountable Primary
Owner, explicit dependencies, governing Interface / Assumption Contracts,
evidence requirements, and one integrated completion state. It is not a
folder, role, or fixed set of technical layers.

The Primary Owner is accountable for coordination, dependency tracking,
blocker tracking, contract adherence, evidence, exit criteria, and driving
completion. This does not mean exclusive implementation. Contributors and
specialist owners are optional where the approved challenge needs them.

## Role Allocation

Choose allocation from the Challenge Profile, Minimum Winning Scope,
workstreams, dependencies, risk, and available humans—not from team size or
fixed software titles. The universal model is:

```text
one capability / workstream
-> one accountable Primary Owner
-> multiple possible contributors / specialist owners
-> one integrated completion state
```

Optional specialist labels describe work that the challenge actually needs;
they are not mandatory universal roles. An Integration Owner or Verification
Owner may be named when that responsibility needs clear coordination, without
changing the Primary Owner's accountability or creating a separate completion
state.

## Required Workstream Record

Record the objective, Critical-Proof-Path relevance, Primary Owner,
contributors where useful, dependencies, governing contracts or assumptions,
required artifact, integration applicability, verification and evidence,
exit criteria, blockers, decisions needed, and deferrals in `plan.md` and
`execute.md`.

For a Product Build challenge, also record Golden-Path relevance where it is
useful. Product Build work may use the specialized [Golden Path](GOLDEN_PATH.md)
and [Full-Stack Flow](FULL_STACK_FLOW.md) guides.

## Interface / Assumption Contracts

An Interface / Assumption Contract is an agreed boundary, invariant, data or
physical interface, schema, protocol, dependency assumption, standard,
tolerance, model expectation, or other condition that independently developed
work relies on.

Where useful, distinguish only `APPROVED CONTRACT` from `PROVISIONAL
ASSUMPTION`. A material change requires approval, propagation to affected work,
updated verification, and an execution-state record. Do not silently drift
independently developed work apart.

API and data contracts remain a Product Build specialization of this universal
concept; see [API And Data Contracts](API_CONTRACTS.md).

## Rendezvous

A rendezvous is the first point where independently developed components,
assumptions, interfaces, artifacts, or physical/software boundaries are
exercised together. It is not satisfied by a merge alone.

Record a rendezvous as `N/A` only when no independently developed boundary
exists, with a short rationale. A frontend-to-API rendezvous is one Product
Build specialization.

## Change Safety

Parallelize implementation, not architecture. One bounded change normally uses
one branch. A Builder works only within approved scope; material changes to
architecture, contracts, assumptions, schemas, invariants, dependencies, or
another owner's scope require approval before change.

Use the [workstream start](../runbooks/WORKSTREAM_START.md) and [Builder launch](../runbooks/BUILDER_LAUNCH.md) runbooks.
