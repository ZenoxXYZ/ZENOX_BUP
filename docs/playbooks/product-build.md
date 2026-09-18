# Product Build

## Use This Specialization When

Use Product Build when the Challenge Profile describes a user-facing software
product or service, with a user workflow, product behavior, human demo, or
similar service outcome. It may include an API-only SaaS or service when that
service itself is the product being evaluated.

Do not select Product Build merely because a challenge exposes HTTP endpoints.
A fixed-schema, constrained hidden-checker API task normally follows its own
evaluation contract rather than this specialization.

## Universal HADF Applied To Product Build

| Universal HADF | Product Build application |
| --- | --- |
| [Minimum Winning Scope](../core/PROOF_MODEL.md) | MVP |
| [Critical Proof Path](../core/PROOF_MODEL.md) | Golden Path |
| [Interface / Assumption Contract](../core/WORKSTREAMS.md) | API, schema, and UI/backend contracts |
| [Rendezvous](../core/WORKSTREAMS.md) | Frontend ↔ API ↔ service ↔ persistence integration |
| [Solution Freeze](../core/DEFINITION_OF_DONE.md) | Feature Freeze |
| Evidence-backed verification | API, persistence, browser/network, and applicable E2E evidence |
| [Realization Boundary](../core/PROOF_MODEL.md) | Local, demo, and deployed runtime boundaries |

MVP is the Product Build application of Minimum Winning Scope. Golden Path is
the Product Build application of Critical Proof Path.

## Product Build Route

1. Confirm the Challenge Profile and evaluation contract support Product Build.
2. Define the MVP and Golden Path using the [Golden Path](../core/GOLDEN_PATH.md) guide.
3. Establish concrete [API and data contracts](../core/API_CONTRACTS.md) before dependent work.
4. Build the required slices using the [Full-Stack Flow](../core/FULL_STACK_FLOW.md).
5. Exercise the Product Build [rendezvous](../runbooks/RENDEZVOUS.md), then record evidence appropriate to the workstream.
6. Use [E2E](../runbooks/E2E.md), [Feature Freeze](../runbooks/FEATURE_FREEZE.md), and [Deployment Readiness](../runbooks/DEPLOYMENT_READINESS.md) only when applicable.

The included FastAPI/PostgreSQL foundation is an optional Product Build starter
path. It is not a universal HADF requirement.

## Optional Software Starter

When the approved Product Build design fits the included stack, use the
[FastAPI/PostgreSQL starter guide](../starters/software-fastapi-postgres.md).
The starter is a convenience, not a methodology requirement or an automatic
choice for every Product Build challenge.
