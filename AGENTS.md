AGENTS.md
Stable engineering rules for this repository.
1. Repository Purpose
This is a reusable hackathon engineering repository intended to be adapted to an authoritative problem statement.
- Official event rules and organizer clarifications define competition constraints.
- The official challenge or problem statement defines what must be solved.
- problem.md captures the approved interpretation of that problem.
- The repository must not inherit domain assumptions from previous projects.
- Design choices must remain distinguishable from problem requirements.
Reusable/prebuilt infrastructure, challenge-specific implementation, AI-assisted development, deployment, and submission/code-freeze behavior must comply with the official event rules and organizer clarifications.
2. Requirements and Implemented-State Evidence
Use two separate axes. Do not treat a project-state summary as requirements authority or as more authoritative than contradictory repository evidence.
Requirements / Design Authority
1. Official event rules / official clarifications
2. Official challenge / problem statement
3. Approved problem.md interpretation
4. Approved plan.md design decisions
Official event rules and clarifications outrank the template workflow for competition constraints. The official challenge or problem statement defines what the project must solve. problem.md is the repository's approved interpretation of those requirements. plan.md records approved engineering and design choices for satisfying them. A design choice must not be presented as a problem requirement.
Implemented-State Evidence
Determine implemented state from repository evidence, including:
- Actual code
- Automated tests
- Migrations and schema evidence
- Git history and status
- Safe runtime or API verification, where applicable
execute.md, review.md, docs/phases/, and docs/reviews/ summarize implemented state and verified engineering history. Reconcile them to repository evidence; they must not override contradictory code, tests, migrations, or Git evidence.
If implementation evidence conflicts with project-state documentation:
1. Do not silently choose either side.
2. Verify the repository evidence.
3. Report the inconsistency.
4. Correct stale documentation only after the actual state is understood.
Human / Supervisor / Builder / Reviewer responsibility split:
- Human / Project Owner - approves, understands, prioritizes, decides, and explains.
- Control / Supervisor - requirements reasoning, architecture supervision, Builder task/prompt preparation where agents are used, Builder-plan critique, teaching, workstream reconstruction, debugging supervision, scope/time control, and judge readiness.
- Builder - repository reconstruction, workstream planning, implementation, tests, debugging, execute.md/evidence updates, and concise implementation reports.
- Reviewer - independent verification, classified findings, severity, and verdict.
- Repository evidence - engineering truth.
This repository should not imply that any specific tool is the primary long-form teaching agent. The Builder records evidence and performs bounded implementation work, the Reviewer performs independent checks, and the Control / Supervisor may supervise and reconstruct understanding for the human.
3. Optional Product Build Starter Direction
When Product Build applies and the included software starter fits the approved
design, the preferred default stack is:
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Alembic
- Uvicorn
- Isolated automated testing
These are starter design choices, not problem requirements or universal HADF
infrastructure. If official event rules, the official challenge/problem
statement, or the approved plan justifies a different technology, follow that
decision. No frontend framework is mandatory.
4. Universal Workstream Gate And Product Build Architecture
Material implementation begins when the active workstream has enough approved
design stability, including:
- Challenge Profile
- Minimum Winning Scope
- Critical Proof Path relevance
- relevant Interface / Assumption Contracts
- dependencies
- required evidence
- exit criteria

Do not require every challenge-wide detail to be finalized before a bounded
workstream can start. Use the canonical core guides for these definitions.

When Product Build applies and a modular monolith fits the approved design,
common responsibilities are:
- backend/main.py — application composition and app entry point
- backend/routes/ — HTTP concerns
- backend/schemas/ — request and response validation contracts
- backend/services/ — application operations and orchestration
- backend/models/ — SQLAlchemy persistence mappings
- backend/logic/ — pure reusable decision or business algorithms when separation is useful
- backend/database.py — database engine, session, base, and dependency setup
- backend/config.py — environment-based configuration
- tests/ — automated verification
- migrations/ — database schema evolution
- frontend/ — user interface when the problem requires one
Do not create unnecessary layers merely because they are theoretically clean.
Workstreams are capability-oriented. They may be software, model/pipeline,
benchmark, security, physical, simulation, design, integration, verification,
or delivery work. They are not automatically folders, roles, or fixed layers.

When Product Build applies, MVP is the Product Build application of Minimum
Winning Scope, and Golden Path is the Product Build application of Critical
Proof Path. API, schema, UI/backend, and persistence behavior are specialized
Interface / Assumption Contracts. Backend-first does not mean
backend-complete-first: frontend work may begin once the relevant approved
contract or capability is stable enough. Material contract changes require
approval, propagation to affected work, updated verification, and an
execution-state record.
5. Coding Principles
- Inspect the real repository before making assumptions.
- Read before editing.
- Do not invent requirements.
- Clearly label conclusions as appropriate:
  - [PROBLEM REQUIREMENT]
  - [DESIGN DECISION]
  - [IMPLEMENTATION]
- Prefer minimal, focused, reversible changes.
- Preserve verified behavior unless the approved plan intentionally changes it.
- Favor readable, explicit code over clever abstractions.
- Solve root causes rather than symptoms.
- Avoid unrelated refactoring during feature work.
- Keep the application runnable whenever practical.
6. API Layer Rules
- Routes handle paths, HTTP methods, dependencies, status codes, request and response wiring, and translation of application outcomes into HTTP behavior.
- Routes should delegate application and business work to services or logic modules.
- Routes must not contain major business or decision algorithms.
- Avoid duplicate endpoints.
- Use stable response contracts.
- Handle validation failures through schemas where appropriate.
7. Schema Rules
- Pydantic schemas own request and response contracts.
- Distinguish required, optional, nullable, and omitted values carefully.
- PATCH semantics must distinguish omitted fields from explicit null.
- Use validation constraints where they are part of the API contract.
- Do not duplicate schema definitions in route or app modules.
- Response schemas should support serialization from ORM objects when needed.
8. Service and Business Logic Rules
- Services own application operations, persistence orchestration, and transactional workflow.
- Reusable pure algorithms may live in logic/.
- Services should not depend on FastAPI request or response objects.
- Services may use SQLAlchemy sessions and models.
- Business and decision logic must not be buried in routes.
- Transaction failures must roll back appropriately.
- Make deterministic behavior explicit when ordering or ranking matters.
9. Database Rules
- SQLAlchemy models represent persistence.
- Alembic is the default schema-evolution mechanism.
- Do not casually use create_all() as a replacement for versioned schema changes after migrations exist.
- Do not run migrations automatically at app startup unless explicitly approved.
- Database credentials must come from environment-based configuration.
- Do not hardcode secrets.
- Automated tests must not mutate production or externally important databases.
- Use isolated temporary databases when appropriate.
- Do not modify real PostgreSQL data without explicit approval.
10. Dependency Rules
- Prefer the existing stack.
- Do not install dependencies without a concrete approved need.
- Explain what problem a new dependency solves.
- Update the dependency manifest.
- Avoid infrastructure complexity unless required.
Do not add the following prematurely unless actual requirements or an approved design decision justify them:
- Microservices
- Kafka
- RabbitMQ
- Celery
- Kubernetes
- Service meshes
- Distributed caches
- Vector databases
- ML systems
- Background workers
- WebSockets
External/cloud/third-party services must be justified by approved requirements or design, have credentials/access verified before reliance, have failure modes understood, avoid unnecessary single points of failure, and preserve a local or degraded fallback where practical.
11. Security and Configuration Rules
- Never commit credentials, tokens, passwords, private keys, or .env files.
- Provide safe .env.example placeholders.
- Validate external inputs.
- Avoid sensitive logging.
- Treat local database and administrative scripts as potentially destructive.
- Use environment-based configuration.
- Do not disable security checks merely to make tests pass.
12. Testing Requirements
A task is not complete because code was generated. Relevant behavior must be verified.
Prefer:
- Unit tests for pure logic
- Service tests
- Schema validation tests
- HTTP/API tests
- Migration tests when persistence changes
- Integration tests for important user flows
- Regression tests for verified bugs
Test:
- Normal behavior
- Important invalid inputs
- Missing entities
- Boundary conditions
- Failure cases relevant to the feature
Existing tests must not be deleted merely to obtain a green suite.
13. Debugging Requirements
Use this debugging workflow:
1. Reproduce or verify the failure when feasible.
2. Record the observed symptom.
3. Determine expected behavior.
4. Inspect actual evidence.
5. Locate the responsible architectural layer.
6. Identify the root cause.
7. Make the smallest appropriate fix.
8. Run focused verification.
9. Run relevant regression verification.
10. Record meaningful bug history.
Do not repeatedly change unrelated code based on guesses.
Use disciplined bug classification:
- A missing future feature is not automatically a bug.
- An optional improvement is not automatically a bug.
- A design limitation is not automatically a bug.
For verified bugs, use stable BUG-IDs and record:
- Component
- Symptom
- Expected behavior
- Actual behavior
- Root cause
- Fix
- Focused verification
- Regression verification
- Status
14. Verification and Task Completion
Use these execution markers:
- [ ] Pending
- [~] In progress
- [x] Completed and verified
- [!] Blocked by a known issue or bug
- [?] Requires clarification or an engineering/design decision
Rules:
- Generated code alone never qualifies for [x].
- Mark [x] only after relevant verification passes.
- If verification is impossible, mark the task incomplete or not verified.
- Never hide known failures.
After implementation, report:
- Files changed
- Verification performed
- What passed
- What failed
- What was not verified
- What remains incomplete
For meaningful workstreams, verified implementation should also be reconstructed for the human operator before handoff is considered complete. The reconstruction should be proportional and time-bounded, especially in strict hackathon mode, and should cover the requirement solved, design approach, important files and layers, runtime and data flow, dependencies, persistent state touched, verification evidence, and connection to the wider system. The purpose is not line-by-line memorization; it is to make the human able to supervise, debug, modify, and explain the system.
Use progressively stronger evidence appropriate to the evaluation contract:
1. Contract integration - relevant independently developed interfaces or assumptions agree.
2. Feature / artifact integration - real dependent components, artifacts, or boundaries are exercised together.
3. Systematic integration - the assembled Critical Proof Path is checked and hardened across applicable boundaries.
4. End-to-end or equivalent proof - the required runtime, checker, benchmark, measurement, simulation, inspection, or other selected evidence proves the intended claim.

For Product Build, this may be frontend expectations and backend design,
real frontend-to-backend slices, systematic full-stack Golden-Path hardening,
and browser E2E. Focused verification, systematic integration, and final proof
are distinct. Do not mark a workstream complete merely because files exist.
15. Git and Change Safety
- Inspect git status before significant work when the repository has Git metadata.
- Do not reset, discard, or revert unrelated user changes.
- Do not rewrite unrelated files.
- Do not delete files unless justified.
- Keep logical changes reviewable.
- Do not create commits unless explicitly requested.
- Do not push unless explicitly requested.
- Before a commit, report what changed and what was verified.
- Prefer clear logical commit boundaries.
16. Anti-Overengineering Rules
- Build the smallest solution satisfying verified requirements.
- Optimize for the smallest working, explainable solution that proves the
  approved Minimum Winning Scope under hackathon constraints.
- Do not introduce architecture only for hypothetical future scale.
- Prefer a modular monolith by default.
- Avoid unnecessary factories, wrappers, and layers.
- Do not prematurely optimize.
- Distinguish demo-critical requirements from polish.
17. Builder Agent Operating Rules
Builder Agents must:
- Read docs/AGENT_WORKFLOW.md.
- Reconstruct project state from repository evidence, not previous-chat memory.
- Read problem.md, plan.md, execute.md, review.md, relevant phase and review documents, Git history, tests, migrations, and code.
- Begin meaningful new workstreams with planning.
- Plan workstreams around the approved capability/objective, Critical-Proof-Path relevance, relevant Interface / Assumption Contracts, dependencies, verification, and exit criteria. Add Golden-Path relevance, layers, and API/data contracts only when Product Build applies.
- Require human approval before implementing major plans.
- Stop for approval if implementation requires a material architecture, schema, API, or policy change.
- Create phase documentation under docs/phases/ appropriate to the workstream's complexity and available time.
- Update project-state summaries at workstream closeout to match verified repository evidence.
Meaningful Builder chats should normally close only after implementation, debugging, verification, documentation, relevant review handling, post-implementation reconstruction, and a human understanding checkpoint. Multiple small tasks may form one meaningful workstream.
18. Independent Reviewer Agent Rules
Reviewer Agents must:
- Read docs/REPO_REVIEW_WORKFLOW.md.
- Use a fresh, independent repository-evidence review.
- Perform the initial review read-only.
- Distinguish bugs, design issues, contract drift, integration failures, missing verification, doc drift, deferred work, and improvements.
- Distinguish implementation bugs, contract drift, integration failures, missing verification, unfinished planned capabilities, intentional backend-only/frontend-only workstreams, and deferred future features.
- Avoid treating a missing layer as a finding when that layer was legitimately N/A for the approved workstream scope.
- Not automatically fix review findings before human approval.
- Allow approved local, design-preserving fixes in the review chat.
- Escalate major architecture, schema, API, or policy corrections to a dedicated corrective workstream.
- Never commit or push without explicit approval.
19. Documentation Responsibilities
- problem.md — authoritative approved problem interpretation
- plan.md — high-level system design and engineering roadmap
- execute.md — summary execution and checkpoint tracker
- review.md — concise summary of verified engineering and bug history
- docs/AGENT_WORKFLOW.md — Builder Agent workflow
- docs/REPO_REVIEW_WORKFLOW.md — Reviewer Agent workflow
- docs/phases/ — detailed implementation and learning documentation
- docs/reviews/ — detailed independent repository-review evidence
Avoid duplicating full phase documentation into review.md.
Document responsibilities:
- problem.md - normalized WHAT the challenge requires: Challenge Profile, scope, inputs/outputs, assumptions, constraints, evaluation contract, proof, realization boundary, and applicable domain requirements. Product Build may additionally record MVP and Golden Path.
- plan.md - approved HOW / Master System Design: workstreams, dependencies, Interface / Assumption Contracts, integration, verification, delivery strategy, risks, and approved architecture. Product Build may additionally record frontend/backend structure, entities, persistence, and API contracts.
- execute.md - live workstream and checkpoint state: objective, Critical-Proof-Path relevance, owners, dependencies, contracts, integration applicability, verification, evidence, status, blockers, next actions, and deferrals. N/A fields are valid. Product Build may add Golden-Path and layer detail.
- review.md - verified review findings/history, not a duplicate implementation tracker.
- README.md - project-facing explanation and usage guide for the actual repository; it does not replace problem.md, plan.md, or execute.md.
- Actual code, migrations, tests, Git evidence, and safe runtime verification - implemented truth.
20. Hackathon Priority Rule
When time is constrained, prioritize in this order:
1. Critical Proof Path and required artifact work
2. Core decision or required behavior is correct
3. Required state, interfaces, and assumptions hold
4. Important failure cases are handled
5. Evidence protects the central claim
6. Product Build integration and user journey work where applicable
7. Explainability
8. Maintainability
9. Polish
Near Solution Freeze, submission, or an applicable Demo Freeze, do not add speculative scope.
Keep documentation concise enough that it does not delay required behavior, integration, verification, evidence, or delivery readiness.
Solution Freeze is universal. Demo Freeze is conditional on a live demo or presentation requirement; official Code Freeze or submission deadlines take precedence.
The intended lifecycle is: official rules/challenge -> requirements extraction -> problem.md -> Challenge Profile -> Minimum Winning Scope -> Critical Proof Path, Proof Package, and Realization Boundary -> Master System Design -> plan.md -> initialize execute.md -> bounded workstream loop -> applicable rendezvous and integration -> focused verification and evidence -> repeat -> systematic proof/hardening -> Solution Freeze -> delivery/submission decision -> final verification -> review -> reconstruction/judge readiness -> optional Demo Freeze -> Git/source checkpoint -> official freeze.

When Product Build applies, use its concrete extension: MVP and Golden Path -> relevant API/data contracts and stable backend/frontend boundaries -> incremental full-stack integration -> Golden-Path E2E where the selected runtime requires it -> Feature Freeze, the Product Build specialization of Solution Freeze -> local or deployed release verification. Deployment is conditional on event rules, the evaluation contract, and the selected delivery strategy. Do not add containers, queues, cloud infrastructure, or deployment complexity unless approved requirements or the chosen provider require them.

Before final delivery, reconstruct enough for the human to explain the problem, requirements, architecture, artifact or runtime, important interfaces, logic, state where applicable, verification, limitations, and tradeoffs. For Product Build, this may additionally cover data model, API, services, frontend, dynamic updates, and deployment. Under strict hackathon timing, keep learning focused on major decisions, critical flows, and judge readiness rather than exhaustive theory.
README lifecycle:
1. Early challenge transition - after problem.md is approved, plan.md is approved, and execute.md is initialized, README.md should transition from generic-starter orientation into a challenge-specific project README. It may include the challenge summary, approved scope, selected artifact or runtime, verification, delivery path, and current implementation status. Add Product Build architecture, setup, API, migrations, and frontend details only when selected. Do not claim planned but unimplemented behavior as completed.
2. Final README reconciliation - once the Critical Proof Path is stable, reconcile README.md against actual verified evidence. Update implemented behavior, selected architecture, setup where used, tests, delivery evidence, limitations, and deferrals. For Product Build, also reconcile Golden Path, API, migrations, runtime, and deployment where used. Remove stale generic-starter wording and inaccurate claims.
21. Final Role Rule
The objective of any Builder, Reviewer, or supporting agent is not to generate the most code.
The objective is to produce the smallest correct, verified, understandable, demonstrable solution consistent with official event rules, the official challenge/problem statement, approved problem.md, and approved plan.md.
This workflow supports AI-assisted engineering when official rules permit it. Actual AI allowance and restrictions come from the official event rules and organizer clarifications; the human remains responsible for understanding and explaining important architecture, code, database behavior, algorithms, decisions, and tradeoffs.
22. HADF Git and Workspace Isolation
The repository-held HADF model is documented in docs/core/, docs/git/, docs/modes/, docs/runbooks/, and docs/prompts/. These documents complement this stable policy; they do not replace official rules, approved requirements, approved design, code, tests, migrations, or Git evidence.

For an instantiated member-aware session, use the [Team Execution runbook](docs/runbooks/TEAM_EXECUTION.md) and [Member-Aware Builder prompt](docs/prompts/TEAM_BUILDER.md). `Member N` activates assignment reconstruction and planning only; it never grants implementation authority. `execute.md` remains canonical live execution state if it conflicts with a member-routing file.

For normal implementation work:
- One bounded change uses one feature branch and one PR.
- One concurrent implementation agent uses one mutable workspace.
- One human with one active mutable task normally uses a feature branch in the current checkout.
- One human running multiple concurrent mutable tasks uses separate branches and separate worktrees.
- Different humans normally use separate clones.
- Agents must inspect the current repository and approved scope before modifying files.
- Agents must stop and escalate before silently changing architecture, shared Interface / Assumption Contracts, invariants, major dependencies, Minimum Winning Scope, Critical Proof Path, another owner's scope, or approved design. Public API, shared schema, MVP, and Golden Path are Product Build examples where applicable.

Merge changes shared source. It does not prove integration. After a dependency merges, affected owners must synchronize, retest, remove temporary substitutes when the real dependency is available, and arrange required cross-owner rendezvous and QA. Frontend/API/backend integration is a Product Build example. CI is configured automated checking; PR Review is scope, architecture, contract, and code judgment; QA is behavioral/risk verification; E2E or equivalent evidence proves the required assembled claim.

No destructive Git operation, history rewrite, force push, branch deletion, worktree deletion, commit, push, merge, or PR action occurs without explicit human approval.
