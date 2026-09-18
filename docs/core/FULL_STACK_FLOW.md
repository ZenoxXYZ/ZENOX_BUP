# Full-Stack Flow

> **Product Build specialization.** This concrete UI-to-persistence flow is a
> Product Build application of universal Interface / Assumption Contracts and
> rendezvous. See the [Product Build playbook](../playbooks/product-build.md).

This repository does not choose a frontend framework. Select the smallest UI stack consistent with official event rules, approved requirements, team skills, and available time.

## Contract-First Delivery

The policy for ownership and material contract change lives in [API And Data Contracts](API_CONTRACTS.md). A full-stack capability applies that policy through this path:

```text
requirement -> frontend page/component -> event handler -> API client
-> HTTP contract -> route -> validation -> service/logic -> persistence
-> response -> frontend state/refetch -> rerender -> visible result
```

Not every workstream needs every layer. Backend-only, frontend-only, verification, integration, and deployment workstreams may mark irrelevant layers `N/A`.

## Integration Evidence

1. Contract integration — frontend expectations and backend design agree.
2. Feature/slice integration — a real frontend capability reaches the real backend capability.
3. Systematic full-stack integration — the assembled Golden Path is hardened across boundaries.
4. E2E verification — a real user journey produces the intended result through required runtime layers.

Focused slice verification proves one capability. Systematic integration proves assembled boundaries cooperate. Golden-Path E2E proves the critical journey. Manual E2E is acceptable under time constraints when its evidence is clear.

## User-State Expectations

For every real interaction, define and verify loading, successful result, validation feedback, request/server error, and empty or unavailable state. Keep core business and decision logic in the backend.

See the [rendezvous](../runbooks/RENDEZVOUS.md), [QA](../runbooks/QA_VERIFICATION.md), and [E2E](../runbooks/E2E.md) runbooks.
