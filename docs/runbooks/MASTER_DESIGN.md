# Master Design

Use this runbook after `problem.md` is approved to shape the work that is
necessary to prove the challenge's central claim. Apply the canonical
[HADF Overview](../core/HADF_OVERVIEW.md), [Challenge Classification](../core/CHALLENGE_CLASSIFICATION.md),
[Proof Model](../core/PROOF_MODEL.md), [Workstreams](../core/WORKSTREAMS.md),
[Definition of Done](../core/DEFINITION_OF_DONE.md), and [Decision Authority](../core/DECISION_AUTHORITY.md).

Material implementation begins when the active workstream has enough approved
design stability. Do not require every challenge-wide decision to be finalized
before a bounded workstream can start.

## Universal Master Design Flow

1. Start from official rules, challenge evidence, and approved `problem.md`.
2. Record the Challenge Profile, Minimum Winning Scope, Critical Proof Path,
   Proof Package, and Realization Boundary.
3. Answer: what claim must be proven, what observable evidence demonstrates
   it, what realization boundary applies, and what limitations remain?
4. Select a solution shape appropriate to the challenge: software/service,
   data/model pipeline, benchmark/optimization system, security repair
   boundary, physical/embedded system, simulation/design artifact, or hybrid.
5. Define bounded workstreams, their dependencies, required evidence, exit
   criteria, and applicable rendezvous before the proof is claimed.
6. Record relevant Interface / Assumption Contracts and their owners. Examples
   may include a model input/output boundary, benchmark interface,
   hardware/protocol interface, or simulation assumption.
7. Select verification from the evaluation contract and create the delivery /
   submission strategy. Use [Timebox and Lifecycle Guidance](TIME_COMPRESSION.md)
   to choose an appropriate freeze zone.

Solution Freeze is universal. Demo Freeze applies only when a live demo or
presentation is required. Material architecture, important assumptions, and
contracts require human approval; do not silently drift them during bounded
implementation.

## When Product Build Applies

Use the [Product Build playbook](../playbooks/product-build.md) when the
Challenge Profile and evaluation contract support a user-facing product or
service. Then additionally define:

- MVP as the Product Build application of Minimum Winning Scope, and Golden
  Path as the Product Build application of Critical Proof Path.
- API, schema, UI/backend, and persistence contracts as specialized Interface
  / Assumption Contracts.
- The frontend -> API -> backend -> persistence flow and a browser E2E
  strategy where the selected runtime requires it.
- Feature Freeze as the Product Build specialization of Solution Freeze.
- Deployment only when official rules, the evaluation contract, or the chosen
  delivery strategy justifies it; hosted APIs, browser runtimes, cloud
  deployment, and production environments are not universal requirements.

Stop for human design approval before material implementation. Escalate a
material architecture, contract, assumption, scope, dependency, or proof-plan
change instead of silently changing the approved design.
