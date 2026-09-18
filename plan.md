# Solution Strategy

## Status

[?] Requires approved `problem.md` before challenge-specific design.

## Challenge Profile

Copy the approved profile from `problem.md` using [Challenge Classification](docs/core/CHALLENGE_CLASSIFICATION.md).

## Timebox Strategy

Record available time, official deadlines and mandatory checkpoints, evaluation
contract, dependency/risk structure, first credible proof target, risky
integration boundary, approximate Solution Freeze zone, and required
submission or live-demo format. Select guidance from [Timebox And Lifecycle
Guidance](docs/runbooks/TIME_COMPRESSION.md); official event rules override it.

## Primary Playbook Candidate

Record `TBD` or a provisional candidate only; playbooks are not selected by this template yet.

## Minimum Winning Scope

Reference the approved record in `problem.md` and [Proof Model](docs/core/PROOF_MODEL.md).

## Critical Proof Path

Reference the approved record in `problem.md` and [Proof Model](docs/core/PROOF_MODEL.md).

## Proof Package

Describe the evidence strategy for approved claims. Do not duplicate the full evidence registry.

## Architecture / Engineering Strategy

Record approved components, technology choices, construction boundaries, and reasons for each design decision. Use `N/A` for irrelevant software, physical, or simulation concerns.

## Realization Boundary

Record engineering implications of the approved realization boundary when relevant.

## Interfaces / Assumption Contracts

| Producer / consumer | Interface or assumption | Inputs / constraints | Expected result | Owner |
| --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD |

Material interface or assumption changes require explicit approval, propagation to affected work, updated verification, and an execution-state record.

## Invariants

## Workstreams

| ID | Objective | Critical-Proof-Path relevance | Primary owner | Dependencies | Governing interfaces / assumptions | Required evidence | Exit criteria |
| --- | --- | --- | --- | --- | --- | --- |
| WS-XX | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Dependency Graph

Use a concise diagram or list when dependencies are non-trivial; otherwise record `N/A`.

## Integration Strategy

State which interfaces, physical connections, simulations, datasets, or assembled runtime boundaries require exercise; use `N/A` when no integration boundary applies.

## Verification Strategy

Select evidence methods required by the evaluation contract. Do not assume tests, browsers, APIs, or deployment are applicable.

## Submission Strategy

Record required deliverables, proof presentation, freeze requirements, and final checks.

## Risks

## Major Decisions

## Parallel Execution Policy

Parallelize approved implementation, not architecture. One bounded change uses one branch. One concurrent implementation agent uses one mutable workspace.

- Use a normal feature branch when one human has one active mutable task.
- Use separate branches and worktrees only when that same human has multiple concurrent mutable tasks.
- Different humans normally use separate clones.

## Explicit Deferrals And Assumptions

Record intentionally postponed work and unverified assumptions so they are not mistaken for bugs or requirements. Use `N/A` for sections that do not apply.
