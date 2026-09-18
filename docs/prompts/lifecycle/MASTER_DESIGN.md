# Master Design Prompt

## Use

After `problem.md` is approved.

```text
Read AGENTS.md, the Builder workflow, approved problem.md, current plan.md/execute.md/review.md, relevant evidence, code, tests, migrations, dependencies, configuration, and Git state. Reconstruct current state before designing.

Propose the smallest coherent strategy for the Minimum Winning Scope and Critical Proof Path. Select a timebox strategy from the Challenge Profile, event duration, mandatory checkpoints, evaluation contract, and dependency/risk structure. Identify proof requirements early, the first credible proof target, risky integration boundary, approximate Solution Freeze zone, and delivery requirements. Cover system boundary, actors, architecture, interfaces or assumptions, workstream order, integration, verification, release path where applicable, security requirements, official freeze constraints, risks, explicit deferrals, and unresolved decisions. Add MVP, Golden Path, API/data contracts, frontend, E2E, deployment, or demo preparation only for Product Build work. Mark non-obvious choices [DESIGN DECISION]. Do not implement or edit files. Stop for human approval.

Before implementation, independently review the proposed plan for rule compliance, coverage, invented requirements, Golden-Path clarity, contract/schema consistency, failure behavior, migration/deployment implications, fallback, testability, time feasibility, workstream order, overengineering, and unresolved decisions. Stop for human approval.
```
