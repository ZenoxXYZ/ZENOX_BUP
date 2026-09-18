# Team Of Three

## Coordination Pattern

Adapt responsibilities to the Challenge Profile, workstreams, dependencies,
risk, and available humans. A typical three-person pattern is lead/integration,
capability A, and capability B plus verification. Each bounded workstream has
one accountable Primary Owner; contributors and specialist roles remain
optional.

The lead protects shared contracts and schedules synchronization and
rendezvous. Different humans normally use separate clones. Worktrees are only
for one human's multiple simultaneous mutable tasks or agents; worktrees are
not mandatory and are not a team-size practice.

After allocation, instantiate one lightweight member-routing file per actual
member from the [Member Execution template](../templates/MEMBER_EXECUTION_TEMPLATE.md)
when fresh-session assignment recovery is useful. Follow [Team Execution](../runbooks/TEAM_EXECUTION.md).

## Product Build Example

Typical allocation: Member A leads architecture, integration, and selected backend work; Member B owns backend/data/core logic; Member C owns frontend and QA. Ownership is accountability, not a rigid wall.

The lead protects shared contracts and schedules synchronization and rendezvous. Backend/frontend owners coordinate on approved contracts; QA verifies behavior rather than acting as a substitute for PR review.
