---
title: GridWise Energy Optimization API
emoji: ⚡
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# GridWise

[![CI](https://github.com/ZenoxXYZ/ZENOX_BUP/actions/workflows/ci.yml/badge.svg)](https://github.com/ZenoxXYZ/ZENOX_BUP/actions/workflows/ci.yml)
[![GHCR](https://github.com/ZenoxXYZ/ZENOX_BUP/actions/workflows/ghcr.yml/badge.svg)](https://github.com/ZenoxXYZ/ZENOX_BUP/actions/workflows/ghcr.yml)

**GridWise** is a stateless, LLM-assisted energy-dispatch API for the BUP CSE FEST 2026 Hackathon. Given a 24-hour campus-energy scenario and one to three operator notes, it interprets the notes into safe structured directives, compiles the resulting constraints, and returns a least-cost, physically feasible dispatch plan.

It is deliberately small: one FastAPI service, a deterministic optimization core, and no database, queue, cache, or persistent state.

## What it does

```text
24-hour scenario + operator notes
             │
             ▼
     LLM interpretation ladder
             │
             ▼
   deterministic guardrails
             │
             ▼
      constraint compiler
             │
             ▼
 SciPy / HiGHS linear optimizer
             │
             ▼
 independent replay validation
             │
             ▼
 validated 24-hour dispatch plan
```

The service supports these operator directives:

| Directive | Effect |
| --- | --- |
| `solar_reduction` | Reduces usable solar energy for selected hours. |
| `minimum_battery_reserve` | Raises the minimum battery energy for selected hours. |
| `no_charge_window` | Prevents charging in selected hours. |
| `no_discharge_window` | Prevents discharging in selected hours. |
| `max_grid_window` | Caps grid import for selected hours. |
| `no_op` | Represents a note with no applicable operational effect. |

Time windows are start-inclusive and end-exclusive. Solar factors represent the fraction of forecast energy that remains available.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Readiness probe. Returns `{"status":"ok"}`. |
| `POST` | `/optimize-energy` | Interprets notes and returns a 24-hour dispatch plan. |

Interactive OpenAPI documentation is available at `/docs` while the service is running.

### Request contract

`POST /optimize-energy` accepts:

```json
{
  "scenario_id": "string",
  "operator_notes": ["string"],
  "hours": [
    {
      "hour": 0,
      "demand_kwh": 0,
      "solar_kwh": 0,
      "tariff_bdt_per_kwh": 0
    }
  ],
  "battery": {
    "capacity_kwh": 0,
    "initial_energy_kwh": 0,
    "minimum_energy_kwh": 0,
    "max_charge_kwh_per_hour": 0,
    "max_discharge_kwh_per_hour": 0
  }
}
```

Rules enforced at the API boundary:

- `operator_notes` contains 1–3 non-blank strings.
- `hours` contains exactly one entry for every hour `0` through `23`; input order is accepted, but planning is performed chronologically.
- Energy, tariff, and battery values are finite, non-negative numbers.
- Structurally invalid requests return `400` with an `invalid_request` payload.

### Response contract

Every successful response has these top-level fields:

```json
{
  "scenario_id": "SAMPLE-01",
  "directive_interpretation": [
    {
      "note_index": 0,
      "applies": true,
      "directive_type": "minimum_battery_reserve",
      "structured_adjustment": {
        "hours": [17, 18, 19, 20, 21],
        "minimum_energy_kwh": 90.0
      },
      "explanation": "Maintain a 90 kWh reserve during the specified period."
    }
  ],
  "hourly_plan": [
    {
      "hour": 0,
      "grid_kwh": 60.0,
      "solar_used_kwh": 0.0,
      "battery_action": "idle",
      "battery_kwh": 0.0,
      "battery_energy_after_kwh": 80.0
    }
  ],
  "total_grid_kwh": 1820.0,
  "total_cost_bdt": 16450.0,
  "peak_grid_kwh": 215.0,
  "plan_summary": "Scheduled 24 hours against applicable operator directives."
}
```

`hourly_plan` always contains the hours `0`–`23` in ascending order. `no_op` is the only directive that may have `applies: false`, and it always has `structured_adjustment: null`.

## Quick start

### Prerequisites

- Python 3.12+
- Optional: Docker, for containerized execution
- A Gemini API key for the primary interpretation path; a Groq key is optional but recommended as the secondary provider

### Run locally

```powershell
git clone https://github.com/ZenoxXYZ/ZENOX_BUP.git
cd ZENOX_BUP
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env
uvicorn backend.main:app --host 0.0.0.0 --port 7860
```

On macOS or Linux, activate the environment with `source .venv/bin/activate`.

Set the provider keys in `.env` before starting the service:

```dotenv
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-3.1-flash-lite
GROQ_API_KEY=your_groq_key
GROQ_MODEL=openai/gpt-oss-120b
```

Never commit `.env` or paste live keys into issues, pull requests, logs, or screenshots.

Verify the service:

```powershell
Invoke-RestMethod http://127.0.0.1:7860/health
```

Expected result:

```json
{"status":"ok"}
```

### Send a sample request

The following PowerShell snippet creates a valid 24-hour request and posts it to the local service.

```powershell
$hours = 0..23 | ForEach-Object {
  [ordered]@{
    hour = $_
    demand_kwh = 100.0
    solar_kwh = $(if ($_ -ge 8 -and $_ -le 16) { 45.0 } else { 0.0 })
    tariff_bdt_per_kwh = $(if ($_ -ge 17 -and $_ -le 21) { 14.0 } else { 5.0 })
  }
}

$payload = @{
  scenario_id = "demo-001"
  operator_notes = @("Keep at least 45% battery reserve from 17:00 until 22:00.")
  hours = $hours
  battery = @{
    capacity_kwh = 200.0
    initial_energy_kwh = 100.0
    minimum_energy_kwh = 40.0
    max_charge_kwh_per_hour = 50.0
    max_discharge_kwh_per_hour = 50.0
  }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:7860/optimize-energy `
  -ContentType "application/json" `
  -Body $payload
```

## Architecture and safety

The pipeline is designed so that text interpretation cannot directly produce an unsafe schedule:

1. **Schema gate** validates the HTTP request with Pydantic.
2. **LLM interpreter** processes the complete note set in a batched request, using Gemini first, then a strict Gemini retry, then Groq.
3. **Guardrails** validate directive type, hour semantics, factors, reserve values, and the `no_op` invariant.
4. **Constraint compiler** turns valid directives into per-hour optimization bounds.
5. **HiGHS LP solver** minimizes grid cost while respecting energy balance, capacity, rate, grid-cap, and end-of-day neutrality constraints.
6. **Materializer** builds the public hourly plan and recomputes its totals.
7. **Replay validator** independently checks the returned plan before it is served.

If an external provider or a non-critical stage is unavailable, the service uses a controlled degradation path: affected notes become canonical `no_op` directives and a valid baseline schedule is returned. This keeps the API reliable, but a configured LLM path is required for the challenge's intended, directive-aware operation.

## Testing and evaluation

Install the development dependencies, then run the complete repository test suite:

```powershell
pytest tests/ -q
python -m compileall -q backend
```

The independent harness can score a running service against the public cases:

```powershell
python tests/harness.py --url http://127.0.0.1:7860 --cases tests/fixtures/public_cases.json
```

The harness checks readiness, response shape, replay validity, ground-truth directive compliance, optimization cost ratio, and observed latency. Its score is evidence, not a substitute for the organizer's evaluation.

## Docker

Build and run the service without baking secrets into the image:

```powershell
docker build -t gridwise:latest .
docker run --rm -p 7860:7860 --env-file .env gridwise:latest
```

Then browse to `http://127.0.0.1:7860/docs` or call `/health`.

## Constraints and scope

- The service is evaluated on synthetic, discrete 24-hour scenarios.
- Battery behavior is idealized: no efficiency curve, thermal model, degradation model, grid export, or multi-day state.
- It is intentionally stateless and has **no database**.
- Ambiguous or irrelevant notes safely degrade to `no_op`; they are not treated as implicit operational instructions.
- HTTP `500` responses are opaque and never intentionally include stack traces, provider keys, or environment values.

## Repository map

```text
backend/
  main.py                 FastAPI application and error boundaries
  routes/                 HTTP orchestration and optional-stage seams
  schemas/                Request, response, and constraint contracts
  services/               LLM interpreter and prompt construction
  logic/                  Guardrails, LP solver, materialization, replay
tests/                    API, interpreter, constraints, optimizer, replay, harness
docs/challenge/           Challenge sources and public sample cases
problem.md                Approved challenge interpretation
plan.md                   Approved system design and contracts
execute.md                Live execution and verification record
review.md                 Independent findings and verification history
```

## Development notes

The repository's implementation truth is code, tests, Git history, and verified runtime evidence. `problem.md` defines the approved challenge interpretation; `plan.md` records the design; `execute.md` and `review.md` record execution and review evidence.

No database migrations, SQLAlchemy models, PostgreSQL service, or Alembic workflow are required for GridWise.
