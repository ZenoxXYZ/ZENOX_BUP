# ⚡ GridWise — LLM-Assisted Energy Optimization API

GridWise is a stateless backend service that converts natural-language energy-operation instructions into validated machine-readable constraints and computes an optimized 24-hour campus energy schedule.

The repository implements a complete pipeline for:

- receiving a 24-hour energy scenario;
- interpreting natural-language operator notes with an LLM;
- validating the interpreted directives;
- compiling those directives into deterministic constraints;
- solving the resulting optimization problem with linear programming;
- materializing a valid hourly dispatch plan;
- independently replaying the plan against the system rules.

The design separates probabilistic language interpretation from deterministic energy scheduling and verification.

---

# 1. Problem

The system receives:

- a scenario identifier;
- 1–3 natural-language operator notes;
- exactly 24 hourly records;
- hourly demand;
- hourly available solar generation;
- hourly electricity tariffs;
- battery capacity;
- initial battery energy;
- minimum battery energy;
- maximum hourly charge rate;
- maximum hourly discharge rate.

The required output is:

1. a structured interpretation of every operator note; and
2. a complete 24-hour energy plan.

The main technical challenge is that the input combines two very different forms of computation:

```text
unstructured natural language
        +
deterministic constrained optimization

GridWise solves this by inserting a strict validation boundary between the LLM and the optimizer.

2. Solution Overview

The complete request pipeline is:

Client
  │
  ▼
FastAPI Request Boundary
  │
  ▼
Pydantic Validation
  │
  ▼
LLM Interpreter
  │
  ▼
Structured Provider Output
  │
  ▼
Deterministic Guardrails
  │
  ▼
Constraint Compiler
  │
  ▼
SciPy HiGHS Linear Program
  │
  ▼
Plan Materializer
  │
  ▼
Independent Replay Validator
  │
  ▼
JSON Response

Each layer has a single responsibility.

3. API Surface
GET /health

Health/readiness endpoint.

GET /health

Response:

{
  "status": "ok"
}
POST /optimize-energy

Main optimization endpoint.

POST /optimize-energy
Content-Type: application/json

It accepts one full daily scenario and returns the interpreted directives together with the optimized hourly dispatch plan.

4. Request Model

The request model is defined in:

backend/schemas/scenario.py

Structure:

{
  "scenario_id": "string",
  "operator_notes": [
    "string"
  ],
  "hours": [
    {
      "hour": 0,
      "demand_kwh": 0.0,
      "solar_kwh": 0.0,
      "tariff_bdt_per_kwh": 0.0
    }
  ],
  "battery": {
    "capacity_kwh": 0.0,
    "initial_energy_kwh": 0.0,
    "minimum_energy_kwh": 0.0,
    "max_charge_kwh_per_hour": 0.0,
    "max_discharge_kwh_per_hour": 0.0
  }
}

Validation guarantees:

operator_notes contains 1–3 entries;
every note is non-empty;
hours contains exactly 24 entries;
hour identifiers are exactly 0..23;
hourly numeric values are finite and non-negative;
all required battery fields are present.
5. Supported Directives

The interpreter and guardrail system supports exactly six directive types.

Directive	Meaning
solar_reduction	reduce usable solar during selected hours
minimum_battery_reserve	enforce a minimum battery energy level
no_charge_window	disable battery charging
no_discharge_window	disable battery discharge
max_grid_window	cap grid import
no_op	the note has no operational effect

The structured invariant is:

directive_type == "no_op"
⇔ applies == false
⇔ structured_adjustment == null

All other directive types use:

applies == true

with a directive-specific adjustment object.

6. Natural-Language Interpretation

The interpreter is implemented in:

backend/services/interpreter.py
backend/services/interpreter_prompt.py

The current provider flow is:

Google Gemini
gemini-3.1-flash-lite
        │
        ▼
strict Gemini retry
        │
        ▼
Groq
openai/gpt-oss-120b
        │
        ▼
canonical no_op degradation

Timeouts:

Gemini normal       8 seconds
Gemini strict       8 seconds
Groq fallback       6 seconds

The interpreter processes all operator notes in a single batch.

It provides battery context to the model so relative instructions can be converted into absolute values.

Example:

"maintain at least 50% of battery capacity"

with:

capacity_kwh = 200

becomes:

{
  "minimum_energy_kwh": 100
}
7. Structured LLM Output

Provider output is constrained using Pydantic models.

The directive type is a closed enum:

solar_reduction
minimum_battery_reserve
no_charge_window
no_discharge_window
max_grid_window
no_op

The system does not accept arbitrary provider-defined type names.

The provider output is still treated as untrusted after schema validation.

It must pass through the deterministic guardrail layer before it can influence optimization.

8. Interpretation Semantics
Time windows

Time windows are interpreted as start-inclusive and end-exclusive.

"1 PM to 3 PM"
→ [13, 14]

The prompt requires the model to return every affected hour explicitly.

The guardrail does not infer missing range values.

Solar reduction factor

The factor represents the fraction of solar generation that remains.

80% reduction
→ factor = 0.2
reduced by half
→ factor = 0.5
Relative reserve values

Percentage-based battery reserve instructions are converted using the actual battery capacity included in the request context.

9. Guardrail Layer

Implemented in:

backend/logic/guardrails.py

The guardrail converts untrusted model output into trusted internal directives.

It validates:

exact directive type;
note index;
duplicate indexes;
missing entries;
applies;
adjustment structure;
exact adjustment fields;
hour values;
factor values;
reserve values;
grid caps;
finite numeric values.

Safe normalization includes:

sorting valid hours;
deduplicating valid hours;
normalizing no_op;
repairing unambiguous applies inconsistencies.

Malformed directives degrade independently instead of invalidating unrelated valid directives.

10. Constraint Compilation

Implemented in:

backend/logic/constraints.py

The compiler produces a ConstraintSet containing five 24-hour arrays:

eff_solar
charge_ub
discharge_ub
grid_ub
energy_lb

Baseline values come from the original scenario.

Directive overlap rules are deterministic.

Solar reductions
minimum factor wins

Factors are not multiplied.

Battery reserves
maximum reserve wins
Grid caps
minimum grid cap wins
Charge restrictions

All affected hours are combined.

Discharge restrictions

All affected hours are combined.

11. Optimization Model

Implemented in:

backend/logic/optimizer.py

The optimization problem is a continuous linear program.

For 24 hours, the solver uses 96 variables:

24 grid import variables
24 solar-used variables
24 battery-charge variables
24 battery-discharge variables

The objective is:

minimize

Σ grid_kwh[h] × tariff_bdt_per_kwh[h]

for:

h = 0 ... 23
12. Energy Constraints

For each hour:

grid
+ solar
+ battery discharge
=
demand
+ battery charge

Battery state evolves as:

E_after = E_before + charge - discharge

with:

energy_lb[h]
≤ E_after[h]
≤ capacity_kwh

Charge and discharge are additionally bounded by the hourly rate limits.

13. End-of-Day Neutrality

The battery must finish the day at the same energy level at which it started.

E_after[23] = initial_energy_kwh

This ensures the optimizer cannot reduce cost by permanently consuming the initial stored energy.

14. Solver

The optimization layer uses:

scipy.optimize.linprog(
    ...,
    method="highs"
)

This uses the HiGHS linear optimization backend through SciPy.

The optimization problem is purely continuous and linear.

No integer or mixed-integer variables are required.

15. Plan Materialization

Implemented in:

backend/logic/materializer.py

The solver returns numeric vectors.

The materializer converts them into the API's hourly plan.

It handles:

charge/discharge netting;
battery action labeling;
battery state tracking;
grid derivation from the balance equation;
floating-point cleanup;
fixed rounding;
total calculation.

The plan contains exactly one record for every hour.

16. Independent Replay Validation

Implemented in:

backend/logic/replay.py

The replay validator is intentionally independent from the production optimizer and constraint compiler.

It re-derives the system rules from the specification and checks the returned plan hour by hour.

This allows production logic and verification logic to fail independently rather than sharing the same implementation.

Two replay modes exist.

Mode A

Validates the returned plan against the system's own interpreted directives.

Mode B

Validates the plan against externally supplied directive ground truth.

The same replay engine is used by the local harness.

17. Failure Handling

GridWise uses controlled degradation rather than allowing provider or optimizer failures to crash the request path.

Interpreter
Gemini
→ strict Gemini retry
→ Groq
→ no_op
Solver
directive-constrained solve
→ base-constraint solve
→ deterministic fallback plan
Fallback plan

The final fallback:

keeps the battery idle;
uses available solar;
imports remaining demand from the grid.
18. Response Model

Defined in:

backend/schemas/plan.py

The response contains:

scenario_id
directive_interpretation
hourly_plan
total_grid_kwh
total_cost_bdt
peak_grid_kwh
plan_summary

Each hourly plan entry contains:

hour
grid_kwh
solar_used_kwh
battery_action
battery_kwh
battery_energy_after_kwh
19. Verification

The repository contains unit, integration, replay, mutation, and end-to-end tests.

Important verification components include:

tests/test_interpreter.py
tests/test_guardrails.py
tests/test_constraints.py
tests/test_optimizer.py
tests/test_replay.py
tests/harness.py
tests/latency.py

Recorded integrated verification includes:

Mode A replay: 10/10
Mode B replay: 10/10
Reference cost ratio: 1.0000
P4 paraphrase checks: 6/6 semantic passes

The full test count may change as tests are added, so the repository should be treated as the source of truth rather than documenting a fixed permanent number.

20. Technology Stack
Language

Python

Primary language for the API, optimization, validation, testing, and tooling.

FastAPI

Used for:

HTTP API routing;
request processing;
exception handling;
OpenAPI generation.

https://fastapi.tiangolo.com/

Pydantic

Used for:

request validation;
response validation;
provider DTOs;
runtime invariants.

https://docs.pydantic.dev/

NumPy

Used for numerical matrix and vector construction.

https://numpy.org/

SciPy

Used for the optimization layer through:

scipy.optimize.linprog

https://scipy.org/

HiGHS

Linear optimization backend used through SciPy.

https://highs.dev/

Google Gemini

Primary language-model provider.

Model:

gemini-3.1-flash-lite

SDK:

google-genai

https://ai.google.dev/

Groq

Secondary inference provider.

Model:

openai/gpt-oss-120b

SDK:

groq

https://groq.com/

OpenAI gpt-oss-120b

Fallback language model accessed through Groq.

Model creator:

OpenAI

Uvicorn

ASGI runtime for FastAPI.

https://www.uvicorn.org/

pytest

Automated testing framework.

https://pytest.org/

HTTPX

HTTP client/testing dependency used by the development test stack.

https://www.python-httpx.org/

Docker

Used to package the service into a reproducible container.

Base image:

python:3.12-slim

https://www.docker.com/

GitHub Actions

Used for automated testing and container publishing.

https://github.com/features/actions

GitHub Container Registry

Used for publishing Docker images.

https://ghcr.io/

Hugging Face Spaces

Docker-compatible deployment target.

https://huggingface.co/spaces

21. Repository Structure
ZENOX_BUP/
│
├── backend/
│   ├── main.py
│   │
│   ├── routes/
│   │   ├── optimize.py
│   │   └── seams.py
│   │
│   ├── schemas/
│   │   ├── scenario.py
│   │   ├── constraints.py
│   │   └── plan.py
│   │
│   ├── services/
│   │   ├── interpreter.py
│   │   └── interpreter_prompt.py
│   │
│   └── logic/
│       ├── guardrails.py
│       ├── constraints.py
│       ├── optimizer.py
│       ├── materializer.py
│       └── replay.py
│
├── tests/
│   ├── fixtures/
│   ├── test_interpreter.py
│   ├── test_guardrails.py
│   ├── test_constraints.py
│   ├── test_optimizer.py
│   ├── test_replay.py
│   ├── harness.py
│   └── latency.py
│
├── docs/
│
├── problem.md
├── plan.md
├── execute.md
├── review.md
│
├── Dockerfile
├── .dockerignore
├── .env.example
├── requirements.txt
├── requirements-dev.txt
│
└── .github/
    └── workflows/
        ├── ci.yml
        └── ghcr.yml
22. Local Setup
Clone
git clone https://github.com/ZenoxXYZ/ZENOX_BUP.git
cd ZENOX_BUP
Create a virtual environment

Windows:

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

or:

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

Linux/macOS:

python3 -m venv .venv
source .venv/bin/activate
Install dependencies

Runtime:

python -m pip install -r requirements.txt

Development:

python -m pip install -r requirements-dev.txt
23. Environment Configuration

Create:

.env

using:

.env.example

Example:

GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite

GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

Do not commit live credentials.

24. Start the Service
uvicorn backend.main:app --host 0.0.0.0 --port 7860

Health check:

curl http://127.0.0.1:7860/health

Expected:

{"status":"ok"}

FastAPI documentation:

http://127.0.0.1:7860/docs
25. Run Tests
pytest tests/ -q
26. Run the Evaluation Harness

Start the API:

uvicorn backend.main:app --host 127.0.0.1 --port 8124

Then:

python tests/harness.py \
  --url http://127.0.0.1:8124 \
  --cases tests/fixtures/public_cases.json

The harness checks:

endpoint availability;
interpretation structure;
plan consistency;
ground-truth replay;
optimization cost;
latency.
27. Docker

Build:

docker build -t gridwise .

Run:

docker run --rm \
  -p 7860:7860 \
  --env-file .env \
  gridwise

Health:

curl http://localhost:7860/health
28. CI

GitHub Actions CI is configured in:

.github/workflows/ci.yml

It performs:

checkout
→ Python 3.12
→ install requirements
→ run pytest

The project has no database dependency.

There is no:

PostgreSQL
SQLAlchemy
Alembic
Redis
persistent storage

in the application architecture.

29. Container Publishing

Container publishing is configured in:

.github/workflows/ghcr.yml

Images are built from the repository Dockerfile and published to GitHub Container Registry.

30. Project Design

The implementation is divided into independent capabilities:

Workstream	Responsibility
WS-01	API boundary and schemas
WS-02	LLM interpretation
WS-03	guardrails and constraint compilation
WS-04	optimizer and materializer
WS-05	replay validator and test harness
WS-06	CI, containerization and deployment

Shared contracts are defined in the schema and planning layers so each component can be implemented and tested independently.

31. Security

The project avoids storing live credentials in source control.

Key practices:

.env is ignored;
API keys are provided at runtime;
Docker receives secrets only through environment variables;
provider failures are sanitized;
raw provider exceptions are not returned to API clients;
fallback behavior is deterministic;
no persistent user data is stored.
32. Limitations

GridWise implements the mathematical model defined by the repository's problem specification.

It does not model:

battery efficiency loss;
battery degradation;
inverter efficiency;
thermal behavior;
AC power flow;
stochastic forecasting;
grid export;
multi-day optimization;
live telemetry;
persistent state.

All scenarios are processed independently.

33. Credits
AI and Model Providers
Google — Gemini models and Google GenAI SDK
Groq — hosted inference platform
OpenAI — gpt-oss-120b
Backend
FastAPI
Pydantic
Uvicorn
Numerical Computing and Optimization
NumPy
SciPy
HiGHS
Testing
pytest
HTTPX
Starlette / FastAPI test infrastructure
Infrastructure
Docker
GitHub
GitHub Actions
GitHub Container Registry
Hugging Face Spaces
34. Team

Developed by the ZENOX team for BUP CSE FEST 2026.

@abidhasan9538

Worked on:

API contracts;
request/response schemas;
optimizer;
plan materialization.
@ZenoxXYZ

Worked on:

LLM interpretation;
prompt design;
provider integration;
deterministic guardrails;
constraint compilation.
@FMAmax

Worked on:

replay validation;
QA;
integration harness;
CI/CD;
containerization;
deployment integration.
35. Summary

GridWise is a hybrid natural-language and mathematical optimization system.

The architecture separates responsibilities clearly:

Natural-language interpretation
        ↓
Structured representation
        ↓
Deterministic validation
        ↓
Constraint compilation
        ↓
Linear optimization
        ↓
Plan materialization
        ↓
Independent replay verification

The LLM is responsible only for interpreting human language.

The deterministic backend is responsible for:

validating that interpretation;
converting it into numerical constraints;
computing the schedule;
validating the resulting plan.

This separation keeps probabilistic language processing isolated from the deterministic energy model.
