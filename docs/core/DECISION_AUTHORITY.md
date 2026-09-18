# Decision Authority

The Human / Project Owner remains accountable for requirements, priorities,
risk acceptance, material architecture and contract decisions, final
acceptance, merge, release, submission, and source-history actions.

| Role | Primary responsibility |
| --- | --- |
| Human / Project Owner | Approves, prioritizes, decides, and explains. |
| Control / Supervisor | Requirements reasoning, architecture supervision, scope/time control, and reconstruction. |
| Builder | Bounded implementation, debugging, verification, and evidence recording. |
| Reviewer | Independent evidence-based findings and verdict. |
| QA / Integration owner | Behavioral, cross-boundary, and assembled-flow verification. |

These are responsibility labels, not mandatory human job titles. A person may
hold multiple responsibilities, while a workstream still has one accountable
Primary Owner.

AI agents may assist as Builder, Reviewer, QA/Tester, Debugger, Integration
Assistant, or Research Assistant. Those labels describe bounded assistance,
not human accountability: an agent is not a human teammate and cannot
independently accept work or decide requirements, material architecture,
security acceptance, merge, release, or submission.

Agents must stop and escalate before materially changing architecture, public API, shared schema, invariants, MVP, Golden Path, major dependencies, execution order, or another owner's approved scope. See [AGENTS.md](../../AGENTS.md) and [decision runbooks](../runbooks/MASTER_DESIGN.md).
