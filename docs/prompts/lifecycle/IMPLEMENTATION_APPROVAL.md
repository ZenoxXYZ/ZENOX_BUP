# Implementation Approval Prompt

## Use

Only after a Builder plan is explicitly approved.

```text
Exit Plan Mode and implement exactly the approved [WORKSTREAM NAME] scope. Follow AGENTS.md and the Builder workflow. Preserve layer boundaries and compatible behavior. Use approved contracts; if a material contract change is required, stop for approval and propagate it to affected consumers. Create migrations only for approved persistence changes; do not migrate automatically at startup or mutate real databases.

Reproduce and fix design-preserving implementation bugs with evidence, add regression coverage, run focused and broader closeout verification, create proportional phase evidence, and update execute.md/review.md only from verified facts. Report files, data/request flow, verification, deferrals, reconstruction summary, and unverified items. Stop before commit or push.
```
