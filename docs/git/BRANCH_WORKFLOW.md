# Branch Workflow

Use one bounded change per feature branch. Start from a synchronized `main`, create a descriptive branch, keep its scope focused, verify locally, obtain human diff review, commit when authorized, push when authorized, and open a PR.

Do not modify `main` directly for normal work. Do not mix unrelated workstreams in one branch. Do not use destructive Git commands, force pushes, resets, or history rewrites without explicit human approval.

After merge, follow [post-merge synchronization](POST_MERGE_SYNC.md).
