# Solo Mode

The human is architecture, integration, and release authority, and may hold
the Primary Owner, Builder, verification, and integration responsibilities for
the workstreams in scope. Agents may provide bounded assistance; they do not
replace human accountability.

When independent humans are unavailable, do not claim true independent review
from the same person. Separate Builder, review, and verification into distinct
temporal or cognitive passes where practical, using repository evidence and
explicit acceptance criteria.

Use a normal branch for one human with one active mutable task. Use separate
branches and worktrees only for one human's multiple simultaneous mutable
tasks or agents; worktrees are not mandatory. Different humans normally use
separate clones. Keep one integration owner: the human. Use short rendezvous
checkpoints after contract or dependency merges.

Member routing is optional in Solo Mode. Instantiate a routing file only when
it materially improves fresh-session recovery or mutable-work isolation; use
the [Team Execution](../runbooks/TEAM_EXECUTION.md) runbook when it does.
