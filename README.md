# HADF — Hackathon Agentic Development Framework

> A human-governed, proof-first engineering framework for turning an approved
> challenge into a bounded, verified, explainable submission.

AI can accelerate implementation. It cannot replace challenge interpretation,
architecture, integration, verification, or human responsibility for the final
result. HADF coordinates those activities through repository-carried project
truth, bounded workstreams, evidence, and explicit decision gates.

```text
HADF methodology
!= Product Build specialization
!= optional FastAPI/PostgreSQL starter
!= historical implementation and review evidence
```

**Parallelize implementation, not architecture.**

**Generated code is not verified work.**

Carry execution state in the repository, not in chat memory.

## Why HADF Exists

Hackathon teams must turn incomplete challenge information into a credible
submission under time pressure. AI can make code fast, but it can also amplify
wrong assumptions, uncontrolled scope, incompatible parallel changes, and weak
claims of completion. HADF is a lightweight operating framework for keeping
requirements, design, work, integration, proof, and human authority connected.

It is not a required technology stack, product architecture, or a replacement
for official event rules. Official rules, organizer clarifications, and the
approved challenge always take precedence.

## Problems HADF Solves

| Common failure | HADF response |
| --- | --- |
| Coding starts before the challenge is understood | [Challenge Intake](docs/runbooks/CHALLENGE_INTAKE.md) and a [Challenge Profile](docs/core/CHALLENGE_CLASSIFICATION.md) |
| The wrong solution shape is assumed | Classification before stack or workflow selection |
| Scope grows beyond what can be demonstrated | [Minimum Winning Scope](docs/core/PROOF_MODEL.md) |
| A central claim has no credible proof | Critical Proof Path, Proof Package, and Realization Boundary |
| Contributors invent incompatible architectures | Approved `plan.md` and Interface / Assumption Contracts |
| Agents make unrelated changes | Bounded workstreams and [AGENTS.md](AGENTS.md) |
| Ownership is unclear | One accountable Primary Owner per workstream |
| Chat context disappears between sessions | Repository-carried project truth and optional member routing |
| Parallel work drifts | Dependencies, contracts, branches, and rendezvous |
| A merge is mistaken for integration | Exercise the real boundary and collect evidence |
| “The agent says it is done” | Evidence-based completion gates |
| Integration happens too late | Risk-driven applicable rendezvous |
| Teams polish past the useful deadline | Solution Freeze and event-rule precedence |
| Prototype claims exceed available evidence | Realization Boundary |
| Nobody can explain the finished system | Feature Reconstruction and Project Reconstruction |

## HADF 2.0 in One Diagram

```text
OFFICIAL CHALLENGE
        ↓
UNDERSTAND → CLASSIFY → CHOOSE → BOUND
        ↓
Challenge Profile
→ Minimum Winning Scope
→ Critical Proof Path
→ Workstreams + Interfaces / Assumptions
        ↓
BUILD → INTEGRATE → PROVE → SOLUTION FREEZE
        ↓
SUBMIT / DELIVER
```

The [Proof Package](docs/core/PROOF_MODEL.md) defines the evidence required for
the claim. The Realization Boundary keeps the target real system, hackathon
realization, available evidence, and supported claims honest.

## Universal HADF, Product Build, and the Optional Starter

HADF is the universal engineering framework. Product Build is one application
of it for user-facing software products and services. The included
FastAPI/PostgreSQL foundation is one optional verified Product Build starter.

| Layer | What it provides | What it does not require |
| --- | --- | --- |
| Universal HADF | Classification, proof, workstreams, contracts, evidence, governance, and delivery discipline | A frontend, backend, API, database, browser, deployment, or software artifact |
| Product Build | MVP, Golden Path, product contracts, full-stack integration, browser E2E, and Feature Freeze where relevant | Every HTTP, checker, hardware, model, or simulation challenge |
| Optional starter | A health-focused FastAPI/PostgreSQL development foundation | That HADF users adopt this stack or build a product |

Start with challenge shape and evaluation contract, not a technology choice.

## How HADF Works

The lifecycle is a set of functions, not rigid time blocks. Select timing from
the challenge, event duration, checkpoints, dependencies, risk, and evaluation
contract using [Timebox and Lifecycle Guidance](docs/runbooks/TIME_COMPRESSION.md).

| Function | Purpose |
| --- | --- |
| Understand | Extract official constraints, challenge requirements, supplied assets, and unknowns. |
| Classify | Record the challenge shape and evaluation contract before choosing a solution path. |
| Choose | Select only the methodology, specialization, artifact, and stack that the challenge justifies. |
| Bound | Define Minimum Winning Scope, Critical Proof Path, workstreams, contracts, evidence, and exit criteria. |
| Build | Realize bounded capabilities with one accountable owner and approved design stability. |
| Integrate | Exercise independently developed boundaries where applicable. |
| Prove | Gather the evidence the evaluation contract actually requires. |
| Freeze | Use Solution Freeze to protect proof, integration, submission, and critical fixes. |
| Submit / Deliver | Package the selected artifact, evidence, and explanation under official rules. |

## Classify, Bound, and Prove

### Challenge Profile

The Challenge Profile prevents treating every challenge as a web application.
It describes five dimensions:

- **Starting State** — what already exists and what must change or be shown.
- **Engineering Objective** — the kind of capability, repair, improvement, or
  artifact required.
- **Evaluation Contract** — how success will be judged.
- **Dominant Artifact** — the primary deliverable or system boundary.
- **Realization / Proof Mode** — how the claim can be exercised and evidenced.

A Product Build may need a user flow; a hidden-checker API needs exact required
behavior; an optimization challenge needs correctness and benchmark evidence;
a hardware challenge may need a physical interface and measurement. Read the
[Challenge Classification guide](docs/core/CHALLENGE_CLASSIFICATION.md) before
choosing a specialization or stack.

### Minimum Winning Scope

Minimum Winning Scope is the smallest scope strong enough to satisfy the
central evaluation contract and make the primary claim demonstrable. It protects
teams from building a large but weak solution.

For Product Build only:

```text
Minimum Winning Scope → MVP
```

### Critical Proof Path

Critical Proof Path is the shortest observable sequence that proves the central
claim. It is not universally a browser journey.

| Challenge shape | Example proof path |
| --- | --- |
| Product Build | User action → processing → state/result → visible outcome |
| Hidden-checker API | Startup → request → required reasoning → exact response → checker |
| Optimization | Baseline → algorithm → correctness → benchmark improvement |
| Hardware/IoT | Stimulus → physical system → measurement → expected result |
| Security repair | Reproduce failure → locate cause → patch → retest |

### Proof Package and Realization Boundary

A Proof Package is the minimum collection of observable evidence required to
demonstrate the central claim. The evidence may be tests, checker output,
benchmarks, measurements, simulation validation, inspection, or another
evaluation-appropriate mechanism.

The Realization Boundary records the target real system, hackathon realization,
available evidence, claims supported, and claims not supported. A prototype,
mock, synthetic dataset, or simulation must not silently become a production
claim. See the [Proof Model](docs/core/PROOF_MODEL.md).

## Workstreams, Contracts, and Integration

A workstream is a bounded engineering capability, not a folder, role, or fixed
technical layer.

```text
one capability / workstream
→ one accountable Primary Owner
→ multiple possible contributors / specialists
→ one integrated completion state
```

Primary Owner means accountability for coordination, dependencies, blockers,
contract adherence, evidence, and driving completion. It does not mean
exclusive implementation.

An Interface / Assumption Contract is any shared condition independently
developed work relies on: an API or schema, model input/output boundary,
benchmark interface, hardware protocol, simulation assumption, tolerance, or
other invariant. A rendezvous is the first real exercise of independently
developed components, assumptions, artifacts, or boundaries together.

Product Build may specialize a rendezvous into frontend ↔ API ↔ service ↔
persistence integration. That is one example, not a universal requirement.
Use [Workstreams](docs/core/WORKSTREAMS.md) and the
[Rendezvous runbook](docs/runbooks/RENDEZVOUS.md) for the detailed rules.

## Human-Agent Governance

```text
AI OUTPUT
   ↓
EVIDENCE
   ↓
REVIEW
   ↓
VERIFICATION
   ↓
HUMAN DECISION
```

Humans retain authority over challenge interpretation, requirements,
architecture, material assumptions, important contracts, acceptance, merge,
release, and submission. Agents can assist with inspection, planning,
implementation, testing, debugging, review, research, evidence, and
documentation.

An agent is a bounded assistant, not an autonomous project authority or human
teammate. Read [Decision Authority](docs/core/DECISION_AUTHORITY.md) and
[AGENTS.md](AGENTS.md) for the operating policy.

## Member-Aware Team Execution

HADF can carry team execution state in the repository rather than rely on a
long chat handoff. The generic repository provides a runbook, Builder prompt,
and lightweight routing template. An actual challenge team may instantiate
`docs/team/MEMBER_N.md` only when it is useful for its real members.

```text
shared project truth
→ lightweight member routing
→ Member N
→ Task Orientation
→ Task Plan
→ human review
→ Implementation Plan
→ human approval
→ implementation
→ Implementation Report
→ Feature Reconstruction
→ completion assessment
```

`execute.md` remains the canonical live execution state. A `MEMBER_N.md` file
is routing only. `Member N` means “reconstruct my current assignment, explain
and decompose it, then create a Task Plan”; it never means “start coding.”
Fresh Builder sessions recover the current assignment from repository state, and
reassignment does not require a giant context-transfer prompt.

```text
Member 2
→ reconstruct WS-03
→ explain and decompose the task
→ Task Plan → review
→ Implementation Plan → approval
→ implement → report → Feature Reconstruction
```

- **Task Plan:** What are we building and why?
- **Implementation Plan:** Exactly how will the approved approach be realized?

Feature Reconstruction records one workstream's implemented reality, evidence,
plan divergence, limitations, and downstream handoff needs. Project
Reconstruction explains the complete assembled solution near final delivery.

For the operating procedure, use [Team Execution](docs/runbooks/TEAM_EXECUTION.md),
the [Member-Aware Builder prompt](docs/prompts/TEAM_BUILDER.md), and the
[Member Execution Routing Template](docs/templates/MEMBER_EXECUTION_TEMPLATE.md).

## Evidence-Based Completion

```text
LOCAL COMPLETE
→ focused local evidence exists

MERGE READY
→ applicable repository / PR gate has passed

WORKSTREAM COMPLETE
→ artifact exists
+ interfaces / assumptions hold
+ applicable integration occurred
+ verification passed
+ evidence exists
+ exit criteria are satisfied
```

Merge Ready is a Git/PR workflow gate where branches and pull requests apply;
it does not prove integration. Workstream Complete is evidence-based and may
remain pending after a merge.

```text
Merge ≠ integration.
CI ≠ review.
Review ≠ QA.
Generated code ≠ verified work.
```

See the canonical [Definition of Done](docs/core/DEFINITION_OF_DONE.md).

## Git, PR, CI, and Integration

```text
branch
→ implementation
→ verification
→ PR
→ CI
→ merge
→ synchronize
→ applicable rendezvous
→ evidence-backed completion
```

- Different humans normally use separate clones.
- One human with one mutable task normally uses a normal branch.
- One human running concurrent mutable tasks or agents uses separate branches
  and worktrees.

Worktrees are conditional isolation, not a mandatory team-size practice. See
the [Git mental model](docs/git/GIT_MENTAL_MODEL.md),
[Pull Request workflow](docs/git/PULL_REQUEST_WORKFLOW.md), and
[Post-Merge Sync](docs/git/POST_MERGE_SYNC.md).

## Product Build Specialization

Product Build applies when the Challenge Profile and evaluation contract call
for a user-facing product or service. It may include an API-only service when
that service itself is the evaluated product. HTTP alone does not make a
fixed-schema hidden-checker task Product Build.

| Universal HADF | Product Build application |
| --- | --- |
| Minimum Winning Scope | MVP |
| Critical Proof Path | Golden Path |
| Interface / Assumption Contract | API/schema/UI/backend contract |
| Rendezvous | frontend/API/backend/persistence integration |
| Solution Freeze | Feature Freeze |
| Evaluation-driven verification | API, integration, or browser E2E where applicable |

Use the [Product Build playbook](docs/playbooks/product-build.md) when this
specialization fits. MVP, Golden Path, persistence design, browser E2E, Feature
Freeze, and deployment remain conditional Product Build guidance.

## Optional FastAPI/PostgreSQL Starter

The included software starter is a convenience, not a HADF requirement. Use it
only when the approved Product Build design, official rules, and selected
delivery path fit its Python/FastAPI/PostgreSQL direction.

| Area | Included starter |
| --- | --- |
| API | FastAPI |
| Validation | Pydantic |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Migrations | Alembic |
| Testing | pytest + httpx |
| Local PostgreSQL | Docker Compose |
| CI | GitHub Actions |
| Frontend | Intentionally unselected |

The foundation is deliberately health-focused. It does not include product
models, routes, business rules, authentication, seed data, or a real frontend.
It verifies migration execution, not real-model Alembic autogeneration,
non-trivial schema migration, or seed-data workflow.

Read the [FastAPI/PostgreSQL starter guide](docs/starters/software-fastapi-postgres.md)
for the verified setup, PostgreSQL, Docker Compose, Alembic, environment, port,
and database-safety instructions.

## Quick Start

This optional path verifies the included software starter on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
uvicorn backend.main:app --reload
```

Then open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). For macOS/Linux,
PostgreSQL, Alembic, Docker Compose, and port overrides, use the canonical
[starter guide](docs/starters/software-fastapi-postgres.md).

## Repository Map

```text
.
├── AGENTS.md                 Stable operating policy
├── problem.md                Approved challenge interpretation
├── plan.md                   Approved design and roadmap
├── execute.md                Canonical live workstream state
├── review.md                 Verification and findings state
│
├── docs/
│   ├── core/                 Canonical HADF concepts and authority
│   ├── playbooks/            Selected specializations, including Product Build
│   ├── modes/                Solo and team coordination patterns
│   ├── runbooks/             Operational procedures and checkpoints
│   ├── prompts/              Reusable agent handoffs
│   ├── templates/            Reusable templates, including member routing
│   ├── starters/             Setup guides for optional verified starters
│   ├── phases/               Historical implementation evidence
│   └── reviews/              Historical independent-review evidence
│
├── backend/                  Optional FastAPI starter foundation
├── frontend/                 Placeholder for a challenge-selected UI stack
├── migrations/               Optional starter schema-evolution environment
├── tests/                    Starter verification
└── .github/                  CI workflow
```

`docs/templates/` contains reusable templates. Live `docs/team/MEMBER_N.md`
routing files belong to challenge instances only when an actual team chooses to
instantiate them.

## Project Truth Model

| Artifact | Purpose |
| --- | --- |
| `AGENTS.md` | Operating policy for humans and agents |
| `problem.md` | What the approved challenge requires |
| `plan.md` | Approved engineering and design decisions |
| `execute.md` | Canonical live execution and workstream state |
| `review.md` | Verification, findings, risks, and quality state |
| Code, tests, migrations, runtime, and Git | What actually exists and works |
| `docs/team/MEMBER_N.md` | Optional routing for an instantiated challenge team |

Project truth has distinct states:

```text
DESIGN → IMPLEMENTATION → SHARED SOURCE → RUNTIME
```

Those states can disagree. Repository evidence must be checked before treating
a summary as fact. A member-routing file is never authority over `execute.md`.
Read the [Project Truth Model](docs/core/PROJECT_TRUTH_MODEL.md) for the full
authority and evidence boundaries.

## Team Modes

Allocate work from challenge shape, Minimum Winning Scope, workstreams,
dependencies, risk, and available humans—not fixed backend/frontend titles.

```text
Challenge Profile
→ Minimum Winning Scope
→ workstreams
→ dependencies and risk
→ available humans
→ role allocation
```

Use [Solo](docs/modes/SOLO.md), [Team 2](docs/modes/TEAM_2.md),
[Team 3](docs/modes/TEAM_3.md), or [Team 4](docs/modes/TEAM_4.md) as concise
coordination patterns. After real allocation, a team may instantiate lightweight
member-routing files when fresh-session assignment recovery is useful.

## Worked Example: Choosing the Right Path

Illustrative only: challenge shape determines workflow and technology, not the
reverse.

| Challenge shape | Likely HADF route | Evidence focus |
| --- | --- | --- |
| Product Build | Product Build playbook; optional starter only if suitable | Critical user/product outcome |
| Fixed-schema checker API | Universal HADF; Product Build is not the default | Required responses and checker result |
| Optimization benchmark | Universal HADF with benchmark-oriented workstreams | Correctness and measurable improvement |
| Hardware/IoT | Universal HADF with physical/interface workstreams | Measurement and Realization Boundary |

## Choose Your Path

| If you need to... | Start here |
| --- | --- |
| Understand HADF quickly | [START_HERE.md](START_HERE.md) |
| Classify a challenge | [Challenge Classification](docs/core/CHALLENGE_CLASSIFICATION.md) |
| Define proof and scope | [Proof Model](docs/core/PROOF_MODEL.md) |
| Shape the approved design | [Master Design](docs/runbooks/MASTER_DESIGN.md) |
| Start bounded workstreams | [Workstream Start](docs/runbooks/WORKSTREAM_START.md) |
| Run member-aware execution | [Team Execution](docs/runbooks/TEAM_EXECUTION.md) |
| Launch a member-aware Builder | [Team Builder prompt](docs/prompts/TEAM_BUILDER.md) |
| Use Product Build | [Product Build playbook](docs/playbooks/product-build.md) |
| Use the included starter | [FastAPI/PostgreSQL starter guide](docs/starters/software-fastapi-postgres.md) |
| Coordinate a team | [Solo and team modes](docs/modes/TEAM_2.md) |
| Review, debug, or verify | [Reviewer](docs/prompts/REVIEWER.md), [Debugger](docs/prompts/DEBUGGER.md), and [QA](docs/prompts/QA.md) prompts |
| Compress a timebox | [Timebox and Lifecycle Guidance](docs/runbooks/TIME_COMPRESSION.md) |

## What This Project Demonstrates

This repository demonstrates reusable engineering work rather than a finished
domain product:

- Software-process architecture for high-pressure challenge work.
- Human-in-the-loop AI engineering and bounded agent workflows.
- Repository-carried execution state and fresh-session recovery.
- Requirements normalization, proof-first scope control, and realization-boundary discipline.
- Multi-contributor ownership, contracts, rendezvous, Git/PR/CI, and integration design.
- Evidence-based verification and human reconstruction of implemented reality.
- A verified FastAPI, SQLAlchemy, PostgreSQL, Alembic, pytest, Docker Compose,
  and GitHub Actions foundation for suitable Product Build work.

## Design Principles

- Understand before building.
- Classify before selecting a stack.
- Bound claims with evidence.
- Parallelize implementation, not architecture.
- Carry execution state in the repository, not in chat memory.
- Generated code is not verified work.
- Merge is not integration.
- Compress scope, not required proof.
- Technology is not challenge type.
- Humans retain material decision authority.

## Current Foundation and Known Limitations

HADF 2.0 structural generalization is complete: WS1–WS8 are merged, and
Member-Aware Team Execution is merged.
The included FastAPI/PostgreSQL starter remains intentionally generic and
health-focused. It has no product-domain behavior, and it has not yet verified
real-model Alembic autogeneration, non-trivial schema migration, or seed-data
workflow.

## Project Status

The next phase is real-world validation: use HADF against actual challenges,
observe friction, collect evidence, and add playbooks, modules, examples, or
starters only when real use justifies them.
