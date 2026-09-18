# Git Mental Model

A repository is the shared project history. A branch is an isolated line of proposed change. A worktree is an additional local checkout of a branch. A commit records a checked change, a push shares it, a PR asks for review, and a merge changes shared source.

`origin/main` is shared source state. Local work is not shared truth until it is merged. A merge does not prove runtime integration.

Use [branch workflow](BRANCH_WORKFLOW.md), [worktree workflow](WORKTREE_WORKFLOW.md), and [PR workflow](PULL_REQUEST_WORKFLOW.md) together.
