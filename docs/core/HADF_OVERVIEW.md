# HADF Overview

HADF, the Hackathon Agentic Development Framework, is a lightweight operating model for turning an approved challenge into a bounded, correct, explainable submission with humans and agents working from repository evidence.

It is not a product architecture, a domain template, an AI product, or enterprise process overhead. Official event rules and the approved challenge always override this generic framework.

The repository holds durable engineering memory after a chat ends: requirements, design, live execution state, reviews, code, tests, migrations, and Git history. Builders implement and verify bounded work; Reviewers independently challenge evidence; the Human / Project Owner remains accountable for decisions and understanding. Post-implementation reconstruction turns verified repository evidence into the human understanding needed to supervise, debug, modify, and explain the system.

## Governing Principles

- Understand official sources before selecting a solution shape.
- Classify the challenge and evaluation contract before selecting technology or a specialized flow.
- Bound work around required claims, interfaces, assumptions, and evidence.
- Parallelize implementation, not architecture.
- One bounded change uses one branch.
- One concurrent implementation agent uses one mutable workspace.
- Inspect before modifying; generated code is not completed work.
- Do not silently change material architecture, interfaces, assumptions, invariants, major dependencies, or another owner's scope.
- Merge changes shared source; integration proves dependent components cooperate.
- CI, PR review, QA, and E2E are distinct forms of evidence; proof is the claim-specific evidence that the selected evaluation contract requires.

## Universal Lifecycle

**Understand → Classify → Choose → Bound → Build → Integrate → Prove → Freeze → Submit**

These are lifecycle functions, not fixed clock blocks. Select timing from the
challenge and event constraints using [Timebox And Lifecycle Guidance](../runbooks/TIME_COMPRESSION.md).

The classification and proof terms in this lifecycle are defined only in the canonical core guides below. Product Build is the first concrete specialization; use the [Product Build playbook](../playbooks/product-build.md) when the Challenge Profile and evaluation contract support it.

HADF does not require the included FastAPI/PostgreSQL stack. It is an optional
verified Product Build starter convenience when the approved design fits.

## Canonical Guides

- [Project truth and authority](PROJECT_TRUTH_MODEL.md)
- [Decision authority](DECISION_AUTHORITY.md)
- [Challenge classification](CHALLENGE_CLASSIFICATION.md)
- [Proof model](PROOF_MODEL.md)
- [Workstreams](WORKSTREAMS.md)
- [Definition of Done](DEFINITION_OF_DONE.md)
- [Git operating model](../git/GIT_MENTAL_MODEL.md)
- [Operational runbooks](../runbooks/CHALLENGE_INTAKE.md)
- [Timebox and lifecycle guidance](../runbooks/TIME_COMPRESSION.md)
