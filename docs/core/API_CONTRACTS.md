# API And Data Contracts

> **Product Build specialization.** An API contract is one specialized form of
> an Interface / Assumption Contract. This guide preserves the concrete
> request/response, validation, schema, status, and frontend/backend agreement
> needed for Product Build work. See the [Product Build playbook](../playbooks/product-build.md).

Important API and data contracts belong in the approved Master System Design before dependent work begins. A contract records the producer, consumer, method/path or equivalent transport, parameters, fields/types, validation, success shape, status/error behavior, and ownership.

Frontend work can begin when the relevant contract is stable enough for its approved scope; it does not wait for every backend capability. Mocks are temporary and must be removed when the real dependency is available.

Material contract changes require approval, propagation to every affected producer and consumer, updated verification, and an execution-state record. Do not silently drift backend and frontend implementations apart. Use environment-aware client configuration for backend URLs when needed; never hardcode deployment credentials or deployment-specific public URLs into client code.

For an assembled flow, verify:

```text
user action -> frontend -> API -> validation -> service/logic
-> persistence or decision -> response -> visible frontend state
```

See the [full-stack flow](FULL_STACK_FLOW.md), [rendezvous runbook](../runbooks/RENDEZVOUS.md), and [full E2E runbook](../runbooks/E2E.md).
