# ⚡ GridWise — LLM-Assisted Energy Optimization API

GridWise is a stateless FastAPI service that turns natural-language energy-operation instructions into validated machine-readable constraints and computes an optimized 24-hour campus energy schedule.

The core design keeps probabilistic language interpretation separate from deterministic validation, optimization, and replay verification.

## Architecture

```text
Client
  ↓
FastAPI request boundary
  ↓
Pydantic validation
  ↓
LLM interpreter
  ↓
Structured provider output
  ↓
Deterministic guardrails
  ↓
Constraint compiler
  ↓
SciPy / HiGHS linear program
  ↓
Plan materializer
  ↓
Independent replay validator
  ↓
JSON response
```

## Problem Model

Each request contains:

- one scenario ID;
- 1–3 non-empty natural-language operator notes;
- exactly 24 hourly records for hours `0..23`;
- hourly demand, solar availability, and tariff;
- battery capacity, initial energy, minimum energy, and hourly charge/discharge limits.

The service returns:

1. one structured interpretation per operator note; and
2. a complete 24-hour energy dispatch plan.

The main challenge is combining:

```text
unstructured natural language
        +
deterministic constrained optimization
```

GridWise solves this by placing a strict validation boundary between the LLM and the optimizer.

## API

### `GET /health`

Readiness endpoint.

```json
{
  "status": "ok"
}
```

### `POST /optimize-energy`

Main optimization endpoint.

Example request shape:

```json
{
  "scenario_id": "sample-001",
  "operator_notes": [
    "Reduce solar by 80% from 1 PM to 3 PM."
  ],
  "hours": [
    {
      "hour": 0,
      "demand_kwh": 120.0,
      "solar_kwh": 0.0,
      "tariff_bdt_per_kwh": 6.0
    }
  ],
  "battery": {
    "capacity_kwh": 200.0,
    "initial_energy_kwh": 100.0,
    "minimum_energy_kwh": 40.0,
    "max_charge_kwh_per_hour": 50.0,
    "max_discharge_kwh_per_hour": 50.0
  }
}
```

The real request must contain all 24 hourly entries.

## Supported Directives

The interpreter and guardrail layer support exactly six directive types:

| Directive | Meaning |
| --- | --- |
| `solar_reduction` | Reduce usable solar during selected hours |
| `minimum_battery_reserve` | Enforce a minimum battery energy level |
| `no_charge_window` | Disable battery charging |
| `no_discharge_window` | Disable battery discharging |
| `max_grid_window` | Cap grid import |
| `no_op` | Note has no operational effect |

The core invariant is:

```text
directive_type == "no_op"
⇔ applies == false
⇔ structured_adjustment == null
```

All non-`no_op` directives use `applies == true` with a directive-specific adjustment.

## Interpretation Semantics

### Time windows

Time windows are start-inclusive and end-exclusive.

```text
"1 PM to 3 PM"
→ [13, 14]
```

The model is instructed to return every affected hour explicitly.

### Solar reduction factors

The factor represents the fraction of solar generation that remains.

```text
80% reduction  → factor = 0.2
reduced by half → factor = 0.5
```

### Relative battery reserve

Percentage-based reserve instructions are converted using the request's actual battery capacity.

```text
"maintain at least 50% of battery capacity"
capacity_kwh = 200
→ minimum_energy_kwh = 100
```

## LLM Interpretation and Fallback

The interpreter is implemented in:

- `backend/services/interpreter.py`
- `backend/services/interpreter_prompt.py`

The configured provider ladder is:

```text
Google Gemini
gemini-3.1-flash-lite
        ↓
strict Gemini retry
        ↓
Groq
openai/gpt-oss-120b
        ↓
canonical no_op degradation
```

Current timeout budgets in the interpreter are:

| Path | Timeout |
| --- | ---: |
| Gemini normal | 8 s |
| Gemini strict retry | 8 s |
| Groq fallback | 6 s |

All operator notes are interpreted in one batch.

Provider output is treated as untrusted even after schema validation. It must pass through deterministic guardrails before it can affect the optimizer.

## Guardrails

Implemented in `backend/logic/guardrails.py`.

The guardrail layer validates:

- directive type;
- note index coverage;
- duplicate indexes;
- `applies`;
- structured adjustment shape;
- exact adjustment fields;
- hour values;
- factors;
- reserve values;
- grid caps;
- finite numeric values.

Safe normalization includes sorting/deduplicating valid hours, normalizing `no_op`, and repairing only unambiguous inconsistencies.

Malformed entries degrade independently instead of invalidating unrelated valid entries.

## Constraint Compilation

Implemented in `backend/logic/constraints.py`.

The compiler produces a `ConstraintSet` with five 24-hour arrays:

```text
eff_solar
charge_ub
discharge_ub
grid_ub
energy_lb
```

Overlap rules are deterministic:

| Constraint family | Merge rule |
| --- | --- |
| Solar reductions | Minimum remaining factor |
| Battery reserves | Maximum reserve |
| Grid caps | Minimum cap |
| No-charge windows | Union of hours |
| No-discharge windows | Union of hours |

Solar-reduction factors are **not multiplied**.

## Optimization Model

Implemented in `backend/logic/optimizer.py`.

The optimization problem is a continuous linear program solved with:

```python
scipy.optimize.linprog(..., method="highs")
```

For 24 hours, the model uses 96 decision variables:

- 24 grid-import variables;
- 24 solar-used variables;
- 24 battery-charge variables;
- 24 battery-discharge variables.

Objective:

```text
minimize Σ grid_kwh[h] × tariff_bdt_per_kwh[h]
```

Subject to hourly energy balance:

```text
grid + solar + discharge = demand + charge
```

Battery state evolves as:

```text
E_after = E_before + charge - discharge
```

with:

```text
energy_lb[h] ≤ E_after[h] ≤ capacity_kwh
```

The battery must finish the day at its initial energy:

```text
E_after[23] = initial_energy_kwh
```

## Plan Materialization

Implemented in `backend/logic/materializer.py`.

The materializer converts solver vectors into the API response and handles:

- charge/discharge netting;
- battery action labels;
- battery state tracking;
- grid derivation;
- floating-point cleanup;
- fixed rounding;
- total recomputation.

## Independent Replay Validation

Implemented in `backend/logic/replay.py`.

The replay validator intentionally re-derives the rules independently from the production optimizer and compiler.

It supports two modes:

- **Mode A — self-consistency:** validates the plan against the service's own returned interpretation.
- **Mode B — ground truth:** validates the plan against externally supplied expected directives.

This distinction matters because an internally consistent plan can still be wrong if the original note was interpreted incorrectly.

## Failure Handling

GridWise prefers controlled degradation over uncontrolled request failure.

### Interpreter ladder

```text
designated primary
→ strict retry
→ secondary provider
→ no_op degradation
```

### Solver ladder

```text
directive-constrained solve
→ base-constraint solve
→ deterministic fallback plan
```

The final fallback plan keeps the battery idle, uses available solar first, and imports the remaining demand from the grid.

## Response Model

Defined in `backend/schemas/plan.py`.

Top-level response fields:

```text
scenario_id
directive_interpretation
hourly_plan
total_grid_kwh
total_cost_bdt
peak_grid_kwh
plan_summary
```

Each hourly plan entry contains:

```text
hour
grid_kwh
solar_used_kwh
battery_action
battery_kwh
battery_energy_after_kwh
```

## Verification

The repository includes focused, integration, replay, mutation, and end-to-end verification.

Key files:

- `tests/test_api.py`
- `tests/test_interpreter.py`
- `tests/test_guardrails.py`
- `tests/test_constraints.py`
- `tests/test_optimizer.py`
- `tests/test_replay.py`
- `tests/harness.py`
- `tests/latency.py`

Recorded integrated repository evidence includes:

- Mode A public replay: **10/10**
- Mode B public replay: **10/10**
- Public reference cost ratio: **1.0000**
- P4 paraphrase checks: **6/6 semantic passes**

Test counts change as the repository evolves, so the current repository and test run should remain the source of truth rather than a fixed count in this README.

## Technology Stack

| Area | Technology |
| --- | --- |
| Language | Python |
| API | FastAPI |
| Validation | Pydantic |
| Numerical computing | NumPy |
| Optimization | SciPy + HiGHS |
| LLM primary | Google Gemini via `google-genai` |
| LLM secondary | Groq via `groq` |
| ASGI server | Uvicorn |
| Testing | pytest + HTTPX |
| Containerization | Docker |
| CI | GitHub Actions |
| Image publishing | GitHub Container Registry |

The repository's approved deployment design uses a Docker-compatible public runtime, with Hugging Face Spaces documented in the project planning files and GHCR as the container publishing path.

## Repository Structure

```text
ZENOX_BUP/
├── backend/
│   ├── main.py
│   ├── routes/
│   │   ├── optimize.py
│   │   └── seams.py
│   ├── schemas/
│   │   ├── scenario.py
│   │   ├── constraints.py
│   │   └── plan.py
│   ├── services/
│   │   ├── interpreter.py
│   │   └── interpreter_prompt.py
│   └── logic/
│       ├── guardrails.py
│       ├── constraints.py
│       ├── optimizer.py
│       ├── materializer.py
│       └── replay.py
├── tests/
│   ├── fixtures/
│   ├── test_api.py
│   ├── test_interpreter.py
│   ├── test_guardrails.py
│   ├── test_constraints.py
│   ├── test_optimizer.py
│   ├── test_replay.py
│   ├── harness.py
│   └── latency.py
├── docs/
├── problem.md
├── plan.md
├── execute.md
├── review.md
├── Dockerfile
├── .dockerignore
├── .env.example
├── requirements.txt
├── requirements-dev.txt
└── .github/
    └── workflows/
        ├── ci.yml
        └── ghcr.yml
```

## Local Setup

### 1. Clone

```bash
git clone https://github.com/ZenoxXYZ/ZENOX_BUP.git
cd ZENOX_BUP
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

Runtime:

```bash
python -m pip install -r requirements.txt
```

Development:

```bash
python -m pip install -r requirements-dev.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and provide your own credentials.

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite

GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

Do not commit live credentials.

### 5. Start the service

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 7860
```

Health check:

```bash
curl http://127.0.0.1:7860/health
```

Expected response:

```json
{"status":"ok"}
```

FastAPI documentation is available at:

```text
http://127.0.0.1:7860/docs
```

## Run Tests

```bash
pytest tests/ -q
```

## Run the Evaluation Harness

Start the API locally:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8124
```

Then run:

```bash
python tests/harness.py \
  --url http://127.0.0.1:8124 \
  --cases tests/fixtures/public_cases.json
```

The harness checks:

- endpoint availability;
- interpretation structure;
- plan consistency;
- Mode A / Mode B replay;
- reference cost;
- latency.

## Docker

Build:

```bash
docker build -t gridwise .
```

Run:

```bash
docker run --rm \
  -p 7860:7860 \
  --env-file .env \
  gridwise
```

Check health:

```bash
curl http://localhost:7860/health
```

## CI and Container Publishing

GitHub Actions workflows are stored in:

- `.github/workflows/ci.yml`
- `.github/workflows/ghcr.yml`

The CI workflow installs dependencies and runs the test suite. The GHCR workflow builds and publishes the container image.

This project has no application database or persistent storage dependency.

## Workstreams

| Workstream | Responsibility |
| --- | --- |
| WS-01 | API boundary and schemas |
| WS-02 | LLM interpretation |
| WS-03 | Guardrails and constraint compilation |
| WS-04 | Optimizer and materializer |
| WS-05 | Replay validator and test harness |
| WS-06 | CI, containerization, and deployment |

Shared contracts are defined in the schema and planning layers so capabilities can be implemented and verified independently before integration.

## Security

Key practices:

- `.env` is ignored;
- API keys are supplied at runtime;
- Docker receives secrets through environment variables;
- raw provider exceptions are not returned to API clients;
- provider failures degrade through controlled paths;
- no persistent user data is stored.

## Limitations

GridWise implements the mathematical model defined by the challenge repository.

It does **not** model:

- battery efficiency loss;
- battery degradation;
- inverter efficiency;
- thermal behavior;
- AC power flow;
- stochastic forecasting;
- grid export;
- multi-day optimization;
- live telemetry;
- persistent state.

All scenarios are processed independently.

## Team

Developed by the **ZENOX** team for **BUP CSE FEST 2026**.

| Member | Main contributions |
| --- | --- |
| [@abidhasan9538](https://github.com/abidhasan9538) | API contracts, request/response schemas, optimizer, plan materialization |
| [@ZenoxXYZ](https://github.com/ZenoxXYZ) | LLM interpretation, prompt design, provider integration, deterministic guardrails, constraint compilation |
| [@FMAmax](https://github.com/FMAmax) | Replay validation, QA, integration harness, CI/CD, containerization, deployment integration |

## Design Principle

GridWise keeps the LLM responsible only for interpreting human language.

```text
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
```

The deterministic backend is responsible for validating the interpretation, compiling constraints, computing the schedule, and independently checking the final plan.
