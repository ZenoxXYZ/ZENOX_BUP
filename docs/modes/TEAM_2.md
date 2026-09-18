# Team Of Two

## Coordination Pattern

Adapt responsibilities to the Challenge Profile, workstreams, dependencies,
risk, and available humans. A typical two-person pattern is lead/integration
plus one capability, and another capability plus verification. Either member
may be the accountable Primary Owner for a bounded workstream; contributors
and specialist roles remain optional.

Agree on contract owners, PR reviewers, rendezvous timing, and who runs
assembled verification. Use separate clones for different humans. For one
human's concurrent mutable tasks, use separate branches and worktrees only
when needed; worktrees are not mandatory.

After allocation, instantiate one lightweight member-routing file per actual
member from the [Member Execution template](../templates/MEMBER_EXECUTION_TEMPLATE.md)
when fresh-session assignment recovery is useful. Follow [Team Execution](../runbooks/TEAM_EXECUTION.md).

## Product Build Example

Typical allocation: Member A leads architecture, backend/data, and integration; Member B leads frontend/UX and QA/E2E. Either member may own a different bounded workstream when contracts are clear.
