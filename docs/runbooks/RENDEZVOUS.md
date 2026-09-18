# Rendezvous

Use the canonical [rendezvous definition](../core/WORKSTREAMS.md). A rendezvous
is not satisfied by a merge alone.

For an applicable rendezvous:

- [ ] Identify the independently developed boundary and accountable owners.
- [ ] Confirm governing Interface / Assumption Contracts and any provisional assumptions.
- [ ] Exercise the real artifact, interface, physical boundary, dataset, model, protocol, or dependency together.
- [ ] Record the observed result, evidence, limitations, and required retest or follow-up.

Record `N/A` only when no independently developed boundary exists, with a short
rationale in `execute.md`.

## Product Build Extension

See the [Product Build playbook](../playbooks/product-build.md) for when this
frontend/API specialization applies.

For frontend-to-API work, also confirm endpoint path and HTTP method, request
and response shapes, validation and error behavior, client configuration,
visible loading/success/empty/error states, mutation or refresh behavior, mock
removal, and Browser Network evidence where a browser exists. Use the
[Full-Stack Flow](../core/FULL_STACK_FLOW.md) and [API And Data Contracts](../core/API_CONTRACTS.md) guides.
