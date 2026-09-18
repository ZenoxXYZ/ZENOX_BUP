Builder Role Engineering Workstream Workflow
1. Purpose
This workflow enables a fresh Builder session or agent to reconstruct project state from repository evidence and safely continue the next engineering workstream without depending on previous chat context. It defines the procedure for planning, implementing, debugging, verifying, documenting, reconstructing, and handing off work. Stable repository rules remain in AGENTS.md.

2. Repository State Reconstruction
Every fresh Builder workstream begins by reading or inspecting the following when present and relevant:
- Official event rules and organizer clarifications
- Official challenge or problem statement
- AGENTS.md
- docs/AGENT_WORKFLOW.md
- problem.md
- plan.md
- execute.md
- review.md
- Relevant docs/phases/
- Relevant docs/reviews/
- Current Git status
- Recent Git history
- Actual repository structure
- Implementation
- Tests
- Migrations
- Dependency and configuration files

Apply the two-axis model in AGENTS.md: use official event rules/clarifications, the official challenge/problem statement, approved problem.md, and approved plan.md for competition constraints, requirements, and design authority; use code, tests, migrations, Git history/status, and safe runtime verification for implemented-state evidence. execute.md, review.md, phase documentation, and review documentation are summaries, not overriding evidence.

Do not trust execute.md or other documentation blindly. Cross-check important completion claims against code, tests, migrations, Git history, and review evidence.

If repository evidence conflicts with project-state files, do not silently choose either side. Verify the repository evidence, report the inconsistency, and correct stale documentation only after the actual state is understood. Stop before starting a new workstream when the inconsistency affects its prerequisites or scope.

### Member-Aware Launch

When an actual challenge repository instantiates `docs/team/MEMBER_N.md`, follow
the [Team Execution](runbooks/TEAM_EXECUTION.md) runbook and
[Member-Aware Builder prompt](prompts/TEAM_BUILDER.md). `Member N` activates
assignment reconstruction, task orientation, and a Task Plan; it never permits
editing. Read the selected routing file after the canonical project-state files.
If it conflicts with `execute.md`, report routing drift and use `execute.md`.

Reconstruct at context boundaries, not every message. After explicit Task Plan
approval, prepare a separate Implementation Plan; after explicit implementation
approval, work only within approved scope. The human may explicitly authorize a
combined plan only for a genuinely tiny, low-risk task. Use Feature
Reconstruction after the implementation report to explain one workstream's
verified reality; it is not whole-project reconstruction.

Teams that choose a separate Supervisor Agent may use the optional
[Supervisor–Builder Relay](runbooks/SUPERVISOR_BUILDER_RELAY.md). It adds
handoff and reconciliation mechanics without changing the Builder's independent
repository inspection, human approval gates, `execute.md` authority, or the
canonical completion model.

3. Determine the Next Engineering Workstream
Use the repository sources for their distinct purposes:
- Official event rules and organizer clarifications - competition constraints, including starter, AI, deployment, and submission/code-freeze policy
- The official challenge/problem statement, problem.md, and approved plan.md - requirements and approved design direction
- execute.md, review.md, and phase/review documentation - implementation-state summaries
- Git, code, tests, migrations, and safe verification - implementation-state evidence

Determine the next incomplete, meaningful workstream and verify its prerequisites. Do not blindly implement whatever text appears next in a stale checklist.

4. Workstream Size
A workstream represents one bounded engineering objective that creates or strengthens meaningful system behavior, not one tiny checkbox and not one technology folder. Generic workstream types may include:
- Backend-only foundation or API capability
- Backend-heavy decision or persistence work
- Frontend-only interface or UX capability
- Frontend-heavy capability against stable contracts
- Full-stack vertical slice
- Business or decision-logic capability
- Integration or hardening pass
- Specialized verification when justified
- Release or deployment work

They may also concern a model or data pipeline, benchmark harness, security
repair, physical interface, simulation, CAD/design artifact, or hybrid
boundary. This is not a challenge-type catalog; select only what the approved
Challenge Profile requires.

Group tightly related subtasks when they belong to one coherent engineering objective. Multiple small tasks may form one workstream and should normally receive one reconstruction. Do not make every file edit its own workstream.

A vertical slice is a meaningful capability implemented and verified through every layer required for that capability. Not every slice requires every layer. A decision engine workstream may have frontend N/A. A frontend UX workstream may have backend N/A.

5. Standard Builder Lifecycle
A meaningful Builder workstream normally follows:

```text
repository reconstruction
-> Plan Mode
-> human approval
-> implementation
-> implementation-time debugging
-> focused verification
-> broader closeout verification
-> phase/state documentation
-> independent review where appropriate
-> post-implementation workstream reconstruction
-> human understanding checkpoint
-> Builder chat closure
```

Do not force independent review after every tiny workstream. Do not force a long teaching session after every small edit. Use proportionality.

6. Planning Phase
Meaningful workstreams begin in the Builder Planning Phase / Plan Mode. This planning phase is read-only.

Distinguish persistent design from workstream planning:
- `plan.md` is the approved whole-system Master Design.
- Builder Planning Phase / Plan Mode is a repo-grounded implementation plan for one bounded workstream.
- If the selected Builder tool has a dedicated planning mode, use it. If it does not, the Builder must still stop before implementation and return a bounded implementation plan for review.

Before proposing a plan:
- Inspect official event rules or organizer clarifications when supplied.
- Inspect the current architecture.
- Verify existing behavior.
- Inspect related tests and migrations.
- Derive requirements from problem.md.
- Identify relevant design decisions.
- Confirm the active workstream has enough approved design stability: Challenge
  Profile, Minimum Winning Scope, Critical Proof Path relevance, relevant
  Interface / Assumption Contracts, dependencies, required evidence, and exit
  criteria. Do not require every challenge-wide detail to be finalized before a
  bounded workstream can start.
- Identify applicable artifacts, layers, boundaries, dependencies, and
  contracts or assumptions affected by the capability.

When Product Build applies, also identify the MVP and Golden-Path relationship,
relevant API/data contracts, frontend/backend boundaries, and persistence
assumptions.

The plan must contain the following sections:
Verified Current State
What actually exists and works?

Requirements Addressed
Which official rule, official challenge requirement, or [PROBLEM REQUIREMENT] does this workstream address?

Design Decisions
Which choices are ours?

Scope
What this workstream will implement.

Critical-Proof-Path Relationship
Whether this workstream creates, strengthens, verifies, or does not affect the Critical Proof Path.

Explicit Deferrals
What it will not implement.

Contract Impact
Relevant Interface / Assumption Contracts, whether they are implementation-ready, and whether any material change requires approval, propagation, and updated verification.

Service/Business/Decision Logic
Computation or workflow introduced.

Artifact / State / Data Impact
Relevant model, dataset, physical, simulation, benchmark, persistence, or other artifact impact.

Integration / Rendezvous
Applicable independently developed boundary, or N/A with rationale.

Failure Behavior
Important invalid, missing, and error cases.

Product Build Extension
When Product Build applies, record MVP and Golden-Path relevance, entity/data changes, API and schema changes, persistence/migration changes, validation semantics, request/data/UI flow, and frontend/backend contract impact.

Implementation Sequence
Meaningful engineering subtasks.

Testing Strategy
How correctness will be proven.

Verification Strategy
Commands and checks needed.

Files Likely To Change
Expected repository scope.

Commit Boundaries
Logical change groups, if commits are later requested.

Risks / Open Decisions
Questions, dependencies, assumptions, and decision points.

Event Rule Constraints
Starter/prebuilt infrastructure, AI assistance, challenge-specific implementation boundary, deployment, official Code Freeze, and submission constraints that affect this workstream.

External Services
Any cloud or third-party service dependency, why it is needed, access verification, failure modes, single-point-of-failure risk, and local or degraded fallback where practical.

Do not implement before human approval.

7. Human Plan Approval Gate
A produced plan is not automatically approved. Wait for explicit human approval before implementation.

If the human adds clarifications, incorporate them as approved constraints. Only after approval should Plan Mode be exited.

The Control / Supervisor may critique the Builder plan, generate follow-up tasks/prompts, supervise debugging strategy, and teach/reconstruct the completed workstream. The Builder remains responsible for bounded implementation, tests, evidence updates, and concise implementation reporting.

8. Implementation Phase
After approval:
- Re-check Git status when Git metadata exists.
- Verify the repository has not materially changed.
- Implement only the approved scope.
- Preserve verified existing behavior.
- Make minimal, focused changes.
- Follow the architecture responsibilities in AGENTS.md.

Work through meaningful implementation subtasks efficiently. Prefer vertical slices where practical, for example:

```text
requirement
-> user interaction
-> frontend component
-> event handler
-> frontend API client
-> HTTP/API contract
-> backend router
-> request schema
-> service
-> business/decision logic
-> ORM/persistence
-> database
-> response
-> frontend state/refetch
-> rerender
-> visible result
-> focused verification
```

or:

```text
input state -> filter/eligibility -> score/rank/decision -> explanation -> API response -> test
```

Backend-only, frontend-only, persistence-only, deployment, or verification workstreams may mark irrelevant layers N/A. Do not force every workstream through every layer.

Do not add unrelated functionality.

9. Execution Tracker
Maintain execute.md as a live capability/workstream tracker derived from approved plan.md. It should answer what capability exists, which workstream is active, what blocks the Critical Proof Path, which applicable tasks remain, whether integration occurred, what evidence proves completion, what happens next, and what was deferred. Add Golden-Path and layer detail only when Product Build applies.

Use:
- [ ] Pending
- [~] In progress
- [x] Completed and verified
- [!] Blocked
- [?] Requires decision

Rules:
- Never mark generated-but-unverified work [x].
- Keep low-level tasks under their capability/workstream.
- Support arbitrary workstreams from plan.md; do not hardcode a fixed count or folder sequence.
- Use N/A explicitly for layers outside the approved scope.
- Track completion with DESIGNED, PLANNED, APPROVED, IMPLEMENTED, INTEGRATED where relevant, VERIFIED, EVIDENCE RECORDED, EXIT CRITERIA SATISFIED, and CLOSED when useful.
- Use meaningful checkpoint updates, not constant edits after every line.
- Final workstream closeout must update execution state accurately.
- Treat execute.md as a summary and reconcile it to verified repository evidence before updating it.

10. Implementation-Time Debugging
The Builder Agent owns implementation-time bugs discovered while building its approved workstream when they can be fixed without materially changing the approved design.

For every failure:
1. Reproduce or verify it.
2. Record expected versus actual behavior.
3. Inspect evidence.
4. Locate the architectural layer.
5. Identify root cause.
6. Make the smallest appropriate fix.
7. Add or update a regression test.
8. Run focused verification.
9. Run broader relevant regression verification.

Record meaningful verified Builder bugs in review.md during workstream closeout using stable BUG-IDs. Do not invent bugs or treat missing deferred functionality as a bug.

11. Design-Change Escalation
Stop before implementing a material unapproved change to:
- Architecture
- Persisted data model
- Migration strategy
- Public API contract
- Major business or decision policy
- Workstream scope
- Major dependency or infrastructure
- Phase ordering

Report:
1. What was discovered
2. Why the approved plan is affected
3. Options
4. Tradeoffs
5. Recommendation
6. Decision required

Return to planning and obtain human approval before proceeding. Small implementation corrections that preserve the approved design do not require re-planning.

12. Verification Ladder
After implementation, run relevant checks such as:
1. Targeted tests
2. Full automated test suite
3. Migration upgrade or check, when applicable
4. Import or application-startup check
5. API smoke tests
6. Compile or static sanity checks
7. Dependency consistency check
8. Applicable integration or rendezvous verification
9. Evaluation-contract-appropriate end-to-end, checker, benchmark, measurement, simulation, inspection, or equivalent proof
10. Deployed verification when deployment is selected
11. git diff --check
12. git status

For integration, distinguish:
1. Contract integration - relevant independently developed interfaces or assumptions agree.
2. Feature / artifact integration - real dependent components, artifacts, or boundaries are exercised together.
3. Systematic integration - the assembled Critical Proof Path is checked and hardened across applicable boundaries.
4. End-to-end or equivalent proof - the selected runtime, checker, benchmark, measurement, simulation, inspection, or other evidence proves the required claim.

For Product Build, these may be frontend/backend contract integration, real
full-stack slices, systematic Golden-Path hardening, and browser E2E where the
selected runtime requires it. Focused verification, systematic integration,
and final proof remain distinct.

Only run checks relevant to the repository. Do not claim unperformed verification. Clearly classify results as:
- VERIFIED
- FAILED
- NOT VERIFIED
- DEFERRED

13. Product Build Full-Stack Verification
When Product Build applies and a frontend exists, verify the selected primary user journey:

```text
User
-> frontend interaction
-> HTTP request
-> route
-> schema validation
-> service/business logic
-> persistence/decision logic
-> response
-> frontend rendering
```

Test at minimum:
- Golden successful flow
- Important invalid input
- Missing or empty state
- Important boundary condition
- Major state-changing operation
- Backend/frontend schema compatibility

Systematic full-stack integration is a later Product Build hardening/reconciliation pass, not the first time frontend and backend meet. It should inspect endpoint/path mismatch, HTTP method mismatch, request-field mismatch, response-field mismatch, status/error handling, frontend API base URL, CORS, environment configuration, loading state, empty state, error state, success state, mutation/refetch behavior, stale frontend state, backend validation, persistent state, refresh/reload correctness, cross-page continuity, and Golden-Path continuity.

14. Delivery And Deployment Workstream
Select deployment only when event rules, the evaluation contract, or the
selected delivery strategy require it. Public server deployment, browser
runtime, hosted API, and production environment are not universal HADF
requirements. A delivery workstream may instead package a checker submission,
benchmark result, model, physical artifact, simulation, design, patch, or other
required evidence.

When Product Build deployment applies, public deployment is a first-class
Builder workstream when official rules require it, the demo needs it, or it is
a reliable and valuable use of remaining time. Feature Freeze is the Product
Build specialization of universal Solution Freeze. Local integration is not
deployed verification.

The release lifecycle is:

```text
local Golden-Path E2E
-> Feature Freeze
-> release / deployment decision
-> local final E2E
```

or:

```text
local Golden-Path E2E
-> Feature Freeze
-> release / deployment decision
-> deployment configuration
-> production database and migrations when approved
-> production CORS and environment
-> deployed E2E
```

Product Build deployment workstream inputs:
- Locally verified backend
- Locally verified frontend, if present
- Migrations
- Dependencies
- Environment requirements
- Approved deployment design

Product Build deployment workstream outputs:
- Public backend URL
- Public frontend URL, if applicable
- Hosted database
- Applied migrations
- Verified golden path

Product Build completion criteria:
- Backend starts in production-like mode.
- Health endpoint works publicly.
- Frontend loads publicly, if present.
- Frontend calls the deployed backend, not localhost.
- DATABASE_URL is configured in the host environment.
- Migrations are applied.
- CORS works for real deployed origins.
- Critical request/response contracts work.
- State persists in the hosted database.
- Golden demo flow passes end to end.

Do not add Docker, containers, queues, cloud infrastructure, or deployment complexity unless official rules, the selected provider, the approved problem, or an approved foundation decision requires it. An approved local database Compose service is a host-run development dependency; it does not require containerizing the application or selecting a deployment architecture. Deploy the smallest architecture that reliably demonstrates the critical path.

If Product Build deployment is not required or is not a good tradeoff, use the local release path:

```text
local Golden-Path E2E
-> Feature Freeze
-> release / deployment decision
-> local final E2E
-> final review
-> whole-project reconstruction
-> optional internal Demo Freeze where a live presentation is required
-> official event freeze/submission
```

15. Phase Documentation
After successful verification of a meaningful workstream, document it under:
docs/phases/<workstream-slug>/

In normal or learning mode, create:
- README.md
- Numbered .md documents for meaningful implementation subtasks when useful

Do not create separate documents for trivial edits.

Strict Hackathon / Time-Constrained Mode
By default, create only docs/phases/<workstream-slug>/README.md with a concise record of the objective, requirements addressed, important design decisions, key files and architecture, API or data flow, core logic or algorithm, verification, important bugs, deferred work, and a concise study or demo explanation.

Create numbered subtask documents only when a non-obvious engineering decision, complex algorithm, meaningful bug/debugging story, migration or integration issue needs preservation, or the human explicitly requests detailed learning documentation. Do not require empty or irrelevant sections; omit them or mark them not applicable.

The detailed README and subtask guidance below applies in normal or learning mode, or when the workstream's risk or complexity justifies it.

Phase README Must Explain
- Objective
- Starting state
- Ending state
- Problem requirements addressed
- Design decisions
- Actual implementation subtasks
- Architecture after the phase
- Files added, modified, or deleted
- API behavior
- Request and data flow
- Database and migration changes
- Validation
- Service, business, or decision logic
- Formulas or algorithms when relevant
- Tests
- Verification results
- Meaningful bugs and fixes
- Explicit deferrals
- Remaining limitations
- Concepts the learner should understand
- VS Code code-reading order
- Concise hackathon or judge explanation

Subtask Docs
For meaningful subtasks, explain:
- Problem solved
- Files changed
- Important code
- Why it changed
- Backend flow
- Database impact
- Validation and failure behavior
- Tests
- Bugs
- Remaining work
- Concepts
- VS Code study guide
- Judge explanation

Clearly distinguish:
- [PROBLEM REQUIREMENT]
- [DESIGN DECISION]
- [IMPLEMENTATION]

Phase documentation must describe actual verified implementation, not merely repeat the plan.

16. Post-Implementation Workstream Reconstruction
Purpose: convert verified implementation into human engineering understanding. AI can produce working code faster than a human can internalize it; reconstruction bridges that gap after verification, using the real implementation rather than a hypothetical design.

Normal teaching/reconstruction happens after Builder completion:

```text
Builder
-> focused verification
-> implementation report/evidence
-> Control / Supervisor workstream reconstruction
-> human understanding
-> optional Reviewer
```

Reviewer is not required before every reconstruction. If a Reviewer causes a meaningful corrective change, use: Reviewer finding -> corrective Builder -> verification -> short delta reconstruction.

For a meaningful workstream, reconstruct:
1. Requirement - what approved requirement does this solve?
2. Design - what design was selected, why, and what important alternative was rejected?
3. Files / Layers - which repository files implement the workstream, and what responsibility does each layer have?
4. Runtime Flow - what happens when the feature is executed?
5. Data Flow - what enters, what changes, what persists, and what returns?
6. Dependencies - which earlier modules or workstreams does this depend on?
7. Downstream Impact - which later modules or workstreams depend on this?
8. Verification - which tests and checks prove it, and which meaningful bugs were found and fixed?
9. Judge Explanation - how could the human explain this workstream in 30-60 seconds?

When relevant full-stack slices exist, trace the actual vertical slice through the real repository:

```text
requirement
-> user action
-> frontend
-> API route
-> Pydantic schema
-> service
-> business/decision logic
-> SQLAlchemy
-> database
-> response
-> frontend update
-> visible outcome
-> verification
```

For backend-only or frontend-only workstreams, explain only the relevant layers and state why other layers were N/A.

Do not turn reconstruction into a generic lecture unrelated to the current repository.

Strict hackathon timing guidance:
- Tiny or simple workstream: 2-3 minutes, or merge explanation into the next checkpoint.
- Meaningful workstream: about 5-8 minutes.
- Core business or decision workstream: up to about 8-10 minutes if justified.
- Whole-project reconstruction before demo: about 10-15 minutes.
- Do not teach after every microscopic file edit.

These are guidance, not rigid timers.

17. Human Understanding Checkpoint
Before a Builder chat is closed, the human should be able to explain at least:
- What was built
- Why it exists
- Where it lives
- How it executes
- What state it touches
- What it depends on
- What depends on it
- How it was verified

Do not require exhaustive memorization. The purpose is to make the human capable of supervising, debugging, modifying, and explaining the system.

18. review.md Closeout
Keep review.md concise. Record:
- Workstream status
- Implemented behavior
- Verification performed
- Test results
- Meaningful bug history
- Deferred work
- Not-verified items
- Important limitations

Do not duplicate entire phase documentation into review.md.

Builder closeout records Builder-owned, verified implementation-time bugs. Reviewer findings remain in the review report until human review; accepted or verified review findings are recorded by the Reviewer only after the applicable human approval.

19. plan.md Closeout
Update plan.md only if:
- Workstream completion status needs reflecting.
- The high-level roadmap changed.
- An approved design change materially affects future phases.

Do not rewrite the plan after every implementation detail.

20. Human Review Gate
After implementation, debugging, verification, phase documentation, project-state updates, post-implementation reconstruction, and the human understanding checkpoint, stop for human review. Do not automatically commit or push.

Report:
- IMPLEMENTATION
- VERIFICATION
- BUGS
- DOCUMENTATION
- PROJECT STATE
- RECONSTRUCTION / UNDERSTANDING
- GIT STATUS
- REMAINING / DEFERRED

21. Commit and Push
Commits happen only when explicitly requested. Prefer logical boundaries such as:
- Implementation and tests
- Documentation and project state
- Review or corrective fixes

Before committing:
- Inspect the staged diff.
- Confirm intended scope.
- Confirm tests and verification.

Push only when explicitly requested.

22. Independent Repository Review Handoff
Independent review is selective and risk-driven, not mandatory after every tiny change. It is useful for complex business/decision logic, concurrency/integrity, critical state transitions, important DB constraints, major API changes, significant integration, deployment, and final product checkpoints. After a meaningful executable, deployment, or cross-domain workstream is implemented, debugged, verified, documented, human-reviewed, and normally committed and pushed, an independent Reviewer Agent may run the quality gate in docs/REPO_REVIEW_WORKFLOW.md when practical before dependent major development continues. A human may explicitly authorize review of a clean, identified uncommitted checkpoint under that workflow.

Tiny documentation-only changes do not automatically require a full independent review.

23. Builder vs Reviewer Ownership
Builder:
- Plans
- Implements
- Fixes implementation-time bugs
- Verifies
- Documents
- Updates project state
- Performs workstream reconstruction
- Prepares commits

Reviewer:
- Independently audits stable committed work
- Starts read-only
- Classifies findings
- May fix approved local, design-preserving bugs
- Does not silently redesign architecture

Major review-discovered corrective design changes become a separate corrective Builder workstream.

24. Review Result Handling
If independent review returns:

PASS
Proceed to the next workstream.

PASS WITH NON-BLOCKING FINDINGS
Record or defer findings appropriately and proceed if no dependency risk exists.

BLOCKED
Do not begin dependent major development. P0 must be resolved. P1 should normally be resolved before dependent development when it creates material correctness or integration risk.

25. Next-Chat Handoff
A fresh Builder chat/session is normally responsible for one meaningful workstream. It normally closes after:
- Plan approved
- Implementation complete
- Verification complete
- Docs/state reconciled
- Relevant review findings handled
- Post-implementation reconstruction performed
- Human understanding checkpoint reached

The next meaningful workstream should normally begin in a fresh Builder context. The repository carries engineering memory across chats.

26. Whole-Project Engineering Reconstruction
After final independent review and required critical corrections, reconstruct the full project so the human can explain the approved challenge, Minimum Winning Scope, Critical Proof Path, Proof Package, realization boundary, workstreams, governing contracts or assumptions, artifact/runtime, verification, delivery requirements, limitations, and tradeoffs.

When Product Build applies, additionally reconstruct:

```text
problem
-> requirements
-> architecture
-> data model
-> API
-> services
-> business/decision logic
-> persistence
-> frontend
-> dynamic updates
-> deployment
-> verification
-> optional internal Demo Freeze where a live presentation is required
-> Git/source checkpoint
-> official Code Freeze / submission
-> limitations / tradeoffs
```

The goal is not memorizing every line. The goal is to understand what happens, why, where, what depends on what, what evidence proves it, and which official event rules governed starter use, AI assistance, deployment, and submission behavior.

27. Hackathon Time Compression
Under strict time limits, prioritize:
1. Problem understanding and event-rule constraints
2. Challenge Profile, Minimum Winning Scope, and Critical Proof Path
3. Master design and relevant Interface / Assumption Contracts
4. First credible artifact and required evidence
5. Risk-driven integration or rendezvous
6. Systematic proof, selected delivery-path readiness, verification, and demo readiness where required

When Product Build applies, MVP, Golden Path, backend foundation, frontend work,
and incremental full-stack integration are concrete ways to carry out those
priorities.

Compress workstreams when useful. Do not allow process documentation or long lectures to consume time needed for the smallest credible proof, correctness, integration, verification, and delivery readiness. Use the strict documentation and reconstruction modes above when appropriate.

Near Solution Freeze or an optional Demo Freeze:
- Stop speculative feature development.
- Fix only issues threatening the Critical Proof Path, required artifact, correctness, governing assumptions, integration, selected delivery path, official submission requirements, or critical validation. For Product Build, this includes startup, Golden Path, persistence, and selected runtime.

28. Final Principle
The Builder's job is not to maximize code volume.

It is to convert approved requirements and design decisions into the smallest correct, verified, understandable, demonstrable solution that proves the Minimum Winning Scope while leaving enough repository evidence for another fresh agent to continue safely.

29. HADF Operating References
Use docs/core/ for project truth, decision authority, classification, proof, workstreams, contracts, and completion gates. Use docs/git/ for branch, worktree, PR, post-merge sync, conflict, and cleanup rules. Use docs/runbooks/ for workstream start, Builder launch, rendezvous, QA, timebox, and delivery checkpoints. When Product Build applies, also use its playbook and detailed Golden Path, API/full-stack, E2E, Feature Freeze, and deployment guidance. Use docs/prompts/ only as reusable handoffs, not as authority over repository evidence.

One bounded implementation change uses one branch. One concurrent Builder uses one mutable workspace. The Builder must confirm whether the normal branch is sufficient or whether the same human's concurrent mutable work requires a dedicated worktree. Before an implementation PR is considered closed, follow the documented PR lifecycle and record post-merge synchronization, real-dependency/substitute status, rendezvous, and applicable QA/evaluation evidence. For Product Build, this may include browser E2E.
