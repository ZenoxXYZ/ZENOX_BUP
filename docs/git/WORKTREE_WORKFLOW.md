# Worktree Workflow

Worktrees are optional local isolation, not a team-size ritual.

| Situation | Recommended workspace |
| --- | --- |
| Different humans | Normally separate clones. |
| One human, one active mutable task | Normal feature branch in the current checkout. |
| One human, multiple concurrent mutable tasks or agents | Separate branches and separate worktrees. |

One concurrent implementation agent must have one mutable workspace. Do not let multiple agents edit the same checkout concurrently. Each worktree must be on its own branch; synchronize and clean it after its task closes.
