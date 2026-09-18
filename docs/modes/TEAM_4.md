# Team Of Four

## Coordination Pattern

Adapt responsibilities to the Challenge Profile, workstreams, dependencies,
risk, and available humans. A typical four-person pattern is lead/integration,
capability A, capability B, and verification/quality. Each bounded workstream
has one accountable Primary Owner; contributors and specialist roles remain
optional.

The integrator coordinates shared boundaries and dependency order. Different
humans normally use separate clones. Worktrees are only for one human's
multiple simultaneous mutable tasks or agents; worktrees are not mandatory
and are not a team-size practice.

After allocation, instantiate one lightweight member-routing file per actual
member from the [Member Execution template](../templates/MEMBER_EXECUTION_TEMPLATE.md)
when fresh-session assignment recovery is useful. Follow [Team Execution](../runbooks/TEAM_EXECUTION.md).

## Product Build Example

Typical allocation: Member A is technical lead/integrator; B owns backend/data/core logic; C owns frontend/UX/client integration; D owns QA/reliability. All remain responsible for reviewing shared decisions.

The integrator controls architecture and dependency order. QA owns risk-based verification and evidence, while each Builder remains responsible for local verification. Separate clones are normal for separate humans; worktrees remain per-human concurrency isolation.
