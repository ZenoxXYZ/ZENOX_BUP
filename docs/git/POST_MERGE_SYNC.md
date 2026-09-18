# Post-Merge Synchronization

Merge means shared source changed. Integration means dependent pieces actually work together.

After a dependency merges, affected owners fetch and synchronize `main`, resolve relevant conflicts, retest their work, update contracts if approved, remove temporary mocks when the real dependency is available, and arrange a rendezvous when components must meet.

A merged backend PR does not alone prove:

```text
frontend -> API -> backend -> database -> response -> UI
```

Use the [operational checklist](../runbooks/POST_MERGE_SYNC.md) for a concrete handoff.
