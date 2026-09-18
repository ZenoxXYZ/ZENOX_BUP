# Post-Merge Sync

1. Fetch and synchronize the affected branch with `main`.
2. Resolve relevant conflicts without silently changing approved design.
3. Retest affected local behavior.
4. Replace temporary mocks with the real dependency when available.
5. Update execution state and schedule a rendezvous if dependent components must meet.

See the [post-merge policy](../git/POST_MERGE_SYNC.md).
