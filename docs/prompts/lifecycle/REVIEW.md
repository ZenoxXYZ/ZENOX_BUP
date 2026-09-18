# Review Prompt

## Use

For independent review or an approved local review fix.

```text
Read AGENTS.md, docs/REPO_REVIEW_WORKFLOW.md, relevant HADF guides, approved state files, code, tests, migrations, configuration, and Git evidence. Establish the exact [CHECKPOINT] and diff scope. Independently reconstruct requirements and implementation state; do not rely on Builder claims.

Trace requirements and inspect architecture, contracts, validation, logic, tests, regressions, configuration/security, documentation, integration, and deployed evidence when relevant. Classify each finding as BUG, DESIGN ISSUE, CONTRACT DRIFT, INTEGRATION FAILURE, MISSING VERIFICATION, DOC DRIFT, DEFERRED, or IMPROVEMENT; assign P0/P1/P2; end with PASS, PASS WITH NON-BLOCKING FINDINGS, or BLOCKED. The initial review is read-only: do not fix, commit, or push.

For human-approved local findings only: correct [FINDING IDs], reproduce them, identify root cause, make the smallest design-preserving correction, add regression evidence where appropriate, verify, update accepted review evidence, and stop before commit or push.
```
