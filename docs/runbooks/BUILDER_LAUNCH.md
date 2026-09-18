# Builder Launch

For an instantiated `Member N` session, begin with the [Team Execution](TEAM_EXECUTION.md)
runbook and [Member-Aware Builder prompt](../prompts/TEAM_BUILDER.md). Member
activation reconstructs routing and produces planning only; it is not
implementation approval.

The Builder first inspects `AGENTS.md`, approved state files, relevant code, tests, migrations, configuration, Git evidence, and applicable HADF guides. It proposes a bounded plan covering scope, Critical-Proof-Path relevance, governing Interface / Assumption Contracts, dependencies, risks, verification, evidence, deferrals, and exit criteria. Add Golden-Path relevance only for Product Build work.

After explicit approval, the Builder implements only that scope, self-verifies, records evidence, and escalates material architecture, interface or assumption, schema, invariant, dependency, or Product Build MVP/Golden-Path changes.

Use [Builder prompts](../prompts/BUILDER.md) and the detailed [Builder workflow](../AGENT_WORKFLOW.md).
