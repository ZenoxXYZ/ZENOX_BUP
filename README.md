---
title: GridWise Energy Optimization API
emoji: ⚡
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# GridWise — LLM-Assisted Energy Optimization Service

[![CI](https://github.com/FMAmax/ZENOX_BUP/actions/workflows/ci.yml/badge.svg)](https://github.com/FMAmax/ZENOX_BUP/actions/workflows/ci.yml)
[![GHCR Container Publish](https://github.com/FMAmax/ZENOX_BUP/actions/workflows/ghcr.yml/badge.svg)](https://github.com/FMAmax/ZENOX_BUP/actions/workflows/ghcr.yml)

GridWise is an autonomous, deterministic, LLM-assisted microgrid energy dispatch service for 24-hour campus scenarios under time-of-use tariffs and natural-language operator notes, developed for the **BUP CSE FEST 2026 Hackathon**. The service receives a 24-hour campus scenario (battery parameters, solar capacity, grid connection limits, tariffs, and forecasts) together with 1–3 natural-language operator notes; translates the operator memos into validated structured directives using a generative language model backed by a robust fallback ladder; compiles these directives into physical constraints; and optimizes battery charging, discharging, and grid import using a continuous linear program (HiGHS via SciPy) to produce a cost-minimizing, physically feasible 24-hour dispatch schedule.

---

## POST /optimize-energy Contract & API Specification

The service exposes two HTTP endpoints:
- `GET /health` — Readiness and liveness probe returning `{"status":"ok"}` (guaranteed ready in <60 seconds cold).
- `POST /optimize-energy` — Main optimization endpoint returning validated directive interpretations and 24-hour hourly schedule.

### Request Payload Contract

The request requires 24 hourly intervals for `grid_tariff_bdt_per_kwh`, `hourly_demand_kwh`, and `hourly_solar_kwh`, along with 1–3 `operator_notes`:

```json
{
  "scenario_id": "SAMPLE-01",
  "battery": {
    "capacity_kwh": 200.0,
    "current_charge_kwh": 80.0,
    "max_charge_rate_kw": 50.0,
    "max_discharge_rate_kw": 50.0,
    "min_charge_pct": 20.0
  },
  "site_parameters": {
    "solar_capacity_kw": 250.0,
    "grid_connection_limit_kw": 400.0
  },
  "tariffs": {
    "grid_tariff_bdt_per_kwh": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 14.0, 14.0, 14.0, 14.0, 14.0, 8.0, 5.0]
  },
  "forecasts": {
    "hourly_demand_kwh": [60.0, 55.0, 50.0, 50.0, 52.0, 65.0, 90.0, 120.0, 150.0, 180.0, 200.0, 210.0, 215.0, 210.0, 195.0, 170.0, 140.0, 160.0, 180.0, 175.0, 150.0, 120.0, 90.0, 70.0],
    "hourly_solar_kwh": [0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 25.0, 60.0, 110.0, 155.0, 180.0, 195.0, 180.0, 150.0, 105.0, 55.0, 15.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  },
  "operator_notes": [
    "Peak hours tonight will face higher transmission stress; please keep battery reserve at or above 45% between 17:00 and 22:00.",
    "Cloud cover alert: expect solar output to drop to 25% of forecast between 11:00 and 14:00."
  ]
}
```

### Response Payload Contract

```json
{
  "scenario_id": "SAMPLE-01",
  "directive_interpretation": [
    {
      "note_index": 0,
      "applies": true,
      "directive_type": "minimum_battery_reserve",
      "structured_adjustment": {
        "minimum_energy_kwh": 90.0,
        "hours": [17, 18, 19, 20, 21]
      },
      "explanation": "Maintain at least 45% (90 kWh) battery reserve between 17:00 and 22:00."
    },
    {
      "note_index": 1,
      "applies": true,
      "directive_type": "solar_reduction",
      "structured_adjustment": {
        "factor": 0.25,
        "hours": [11, 12, 13]
      },
      "explanation": "Solar output reduced to 25% between 11:00 and 14:00."
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
  "plan_summary": "24-hour optimal dispatch generated with HiGHS LP solver."
}
```

### Copy-Pasteable cURL Example

```bash
curl -X POST http://localhost:7860/optimize-energy \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "SAMPLE-01",
    "battery": {
      "capacity_kwh": 200.0,
      "current_charge_kwh": 80.0,
      "max_charge_rate_kw": 50.0,
      "max_discharge_rate_kw": 50.0,
      "min_charge_pct": 20.0
    },
    "site_parameters": {
      "solar_capacity_kw": 250.0,
      "grid_connection_limit_kw": 400.0
    },
    "tariffs": {
      "grid_tariff_bdt_per_kwh": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 14.0, 14.0, 14.0, 14.0, 14.0, 8.0, 5.0]
    },
    "forecasts": {
      "hourly_demand_kwh": [60.0, 55.0, 50.0, 50.0, 52.0, 65.0, 90.0, 120.0, 150.0, 180.0, 200.0, 210.0, 215.0, 210.0, 195.0, 170.0, 140.0, 160.0, 180.0, 175.0, 150.0, 120.0, 90.0, 70.0],
      "hourly_solar_kwh": [0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 25.0, 60.0, 110.0, 155.0, 180.0, 195.0, 180.0, 150.0, 105.0, 55.0, 15.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    },
    "operator_notes": [
      "Peak hours tonight will face higher transmission stress; please keep battery reserve at or above 45% between 17:00 and 22:00.",
      "Cloud cover alert: expect solar output to drop to 25% of forecast between 11:00 and 14:00."
    ]
  }'
```

---

## Local Quickstart

Follow these steps to run GridWise locally on a clean machine:

### 1. Prerequisites
- Python 3.12+
- Git

### 2. Clone Repository
```bash
git clone https://github.com/FMAmax/ZENOX_BUP.git
cd ZENOX_BUP
```

### 3. Virtual Environment Setup
Create and activate an isolated virtual environment:
```bash
# Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Runtime Dependencies
Install the lean runtime dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API credentials:
```bash
cp .env.example .env
```
Set your `GEMINI_API_KEY` (and optionally `GROQ_API_KEY`). Note: never commit `.env` to Git.

### 6. Start the Service
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 7860
```

### 7. Verify Health Probe
```bash
curl http://127.0.0.1:7860/health
# Expected output: {"status":"ok"}
```

---

## Docker Build and Execution

GridWise runs as a single-stage, non-root container based on `python:3.12-slim`. **No secrets or keys are baked into any image layer**; API keys arrive exclusively as runtime environment variables.

### Build Local Image
```bash
docker build -t gridwise:latest .
```

### Run Container with Runtime Keys
Pass environment variables using `-e` flags or `--env-file`:

```bash
# Option A: Passing variables directly
docker run --rm -p 7860:7860 \
  -e GEMINI_API_KEY="your_gemini_api_key_here" \
  -e GEMINI_MODEL="gemini-3.1-flash-lite" \
  -e GROQ_API_KEY="your_groq_api_key_here" \
  -e GROQ_MODEL="qwen3.8-27b" \
  gridwise:latest

# Option B: Passing via .env file
docker run --rm -p 7860:7860 --env-file .env gridwise:latest
```

### Verify Container Health
```bash
curl http://localhost:7860/health
```

### Pulling from GitHub Container Registry (GHCR Fallback)
The automated GitHub Actions workflow pushes pre-built images to GHCR on each push to `main`:
```bash
docker pull ghcr.io/fmamax/zenox_bup:latest
docker run --rm -p 7860:7860 --env-file .env ghcr.io/fmamax/zenox_bup:latest
```

---

## Testing and Evaluation Harness

### 1. Install Development / Test Dependencies
Test-only dependencies (`pytest`, `httpx`) are decoupled from production and kept in `requirements-dev.txt`:
```bash
pip install -r requirements-dev.txt
```

### 2. Run the Unit & Replay Test Suite
Run the 181-test suite covering contract shapes, LP constraints, mutation Sabotage tests, and guardrail validations:
```bash
pytest tests/ -q
```

### 3. Run the Evaluation Harness against a URL
Execute the independent verification harness against a local server or deployed Hugging Face Space:

```bash
python tests/harness.py --url http://127.0.0.1:7860 --cases tests/fixtures/public_cases.json
```

The harness performs:
- **Readiness check**: Measures cold-start connectivity to `/health`.
- **Latency profiling**: Measures p50 and p95 latency over repeated queries.
- **Mode A verification (Self-consistency)**: Verifies that `hourly_plan` satisfies all directives returned in `directive_interpretation`.
- **Mode B verification (Ground truth)**: Verifies that `hourly_plan` satisfies the official organizer ground-truth directives from the public test set.
- **Cost ratio analysis**: Compares computed schedule cost against reference HiGHS LP optima (`our_cost / ref_cost`).
- **Rubric scorecard**: Emits a detailed 100-point evaluation breakdown.

---

## Environment Variables & Security Policy

GridWise requires no database. Configuration is supplied strictly through environment variables:

| Variable Name | Description | Required | Example / Default |
| --- | --- | --- | --- |
| `GEMINI_API_KEY` | Google AI Studio API Key | Yes (for primary LLM interpretation) | Placeholder only: `your_gemini_key` |
| `GEMINI_MODEL` | Google Gemini model name | No | `gemini-3.1-flash-lite` |
| `GROQ_API_KEY` | Groq Cloud API Key | Optional (for secondary fallback inference) | Placeholder only: `your_groq_key` |
| `GROQ_MODEL` | Groq model identifier | No | `qwen3.8-27b` |
| `PORT` | Web server listen port | No | Default `7860` (auto-configured on HF Spaces) |

### Security Policy
- **Zero Secrets in Repository & Image**: Secrets are strictly gitignored via `.gitignore` and excluded from containers via `.dockerignore`. Never commit `.env` or hardcode API keys.
- **Runtime-Only Injection**: In Docker, credentials are provided only via `--env-file` or `-e` environment injection at container run time.
- **Sanitized Wire Responses**: Exceptions log full stack traces internally to stderr, returning opaque `{"error": "internal_error", ...}` payloads to clients. No API key, token, or internal trace is ever leaked on the wire.
- **Controlled Degradation Ladder**: If both LLM providers fail or time out, directives safely degrade to `no_op` rather than crashing with HTTP 500, guaranteeing a valid base-rule schedule.

---

## Architecture Overview

GridWise implements a deterministic 7-stage sequential pipeline designed for correctness, safety, and sub-second execution:

1. **API Boundary & Schema Gate**: Strict Pydantic v2 validation enforcing contract C-1. Structurally malformed requests immediately receive HTTP 400 (never 422 or 500).
2. **Batched LLM Interpretation**: A single batched prompt passes all 1–3 operator notes to the LLM (primary: Google Gemini `gemini-3.1-flash-lite`; secondary: Groq `qwen3.8-27b`). Structured JSON schema enforcement ensures schema compliance.
3. **Deterministic Guardrails**: Normalizes LLM outputs (expanding hour ranges `[start, end]` into sequential hour arrays, validating `0 <= factor <= 1`, verifying reserve bounds) and rejects invented directive types.
4. **Constraint Compiler**: Merges normalized directives into per-hour lower/upper bounds (`min(factor)` for solar, `max(reserve)` for battery, set union for no-charge / no-discharge windows, `min(cap)` for grid imports).
5. **Continuous Linear Program (HiGHS LP)**: Uses `scipy.optimize.linprog` with the HiGHS solver to minimize 24-hour total grid energy cost subject to energy balance, battery capacity, maximum charge/discharge rates, and net-neutral end-of-day battery energy ($E_{23} = E_{\text{initial}}$).
6. **Materializer & Accounting**: Eliminates simultaneous charge and discharge, derives exact grid import, and enforces 2-decimal precision.
7. **Specification Replay Validator**: Independent oracle auditing the materialized plan against all physics and directive rules before returning HTTP 200.

---

## Limits & Known Gaps

In accordance with `problem.md §17` (Realization Boundary):
- **Synthetic 24-Hour Scope**: Evaluated exclusively over synthetic 24-hour discrete-hour scenarios. No live campus telemetry, real-time meter feeds, or dynamic multi-day forecasting.
- **Idealized Battery Physics**: The battery model is lossless and instantaneous. Physical efficiency curves (round-trip losses), inverter clipping, battery thermal dynamics, and cell degradation are out of scope.
- **Stateless Operation**: The service maintains zero state, databases, message queues, or persistent caches.
- **Language Boundaries**: The LLM prompt and guardrails are optimized for operational campus energy directives. Notes containing ambiguous text or non-operational commentary safely degrade to `no_op` rather than generating invalid dispatch constraints.
