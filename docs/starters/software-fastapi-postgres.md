# Included FastAPI/PostgreSQL Product Build Starter

This is the canonical onboarding and setup guide for the repository's included
software starter. It is a verified optional Product Build convenience, not
universal HADF infrastructure.

## When To Use It

Use this starter only when the approved Challenge Profile, evaluation contract,
official rules, and chosen Product Build design make its Python/FastAPI/
PostgreSQL direction useful. Do not select it merely because a challenge has
HTTP endpoints. It is not automatically suitable for every Product Build
challenge and is not required for non-Product work.

For methodology and Product Build selection, begin with [START_HERE](../../START_HERE.md)
and the [Product Build playbook](../playbooks/product-build.md).

## Included Verified Foundation

- FastAPI application entry with `GET /` health response `{"status":"ok"}`
- Environment-driven SQLAlchemy configuration with an in-memory SQLite fallback
- Alembic environment and an immutable infrastructure-only baseline revision
- pytest and httpx foundation tests
- Docker Compose PostgreSQL for local development
- Python 3.12 CI path: PostgreSQL readiness, Alembic upgrade, then pytest
- Empty frontend placeholder until an approved Product Build selects a UI stack

The starter contains no product-specific routers, services, mapped domain
models, tables, authentication, business rules, or real frontend behavior.

## Quick Setup

Use Python 3.12. Create and activate an isolated virtual environment.

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the declared dependencies and run the foundation tests:

```powershell
python -m pip install -r requirements.txt
python -m pytest
```

Without `DATABASE_URL`, the database-connectivity test uses the in-memory
SQLite fallback. Start the health-only application with:

```powershell
uvicorn backend.main:app --reload
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). The response should be
`{"status":"ok"}`.

## Optional Local PostgreSQL

FastAPI, Alembic, and pytest run on the host. Docker Compose runs PostgreSQL
only.

1. Copy [.env.example](../../.env.example) to `.env`. `POSTGRES_PORT` defaults
   to `5432` and is overridable. Keep `DATABASE_URL` aligned with its chosen
   host port.
2. Start PostgreSQL and wait for it to become healthy.

   ```powershell
   docker compose up -d
   docker compose ps
   ```

3. Set the matching URL in the host shell, then migrate, test, and run.

   ```powershell
   $env:DATABASE_URL = "postgresql+psycopg://hadf:hadf_local_password@127.0.0.1:5432/hadf_dev"
   python -m alembic upgrade head
   python -m pytest
   uvicorn backend.main:app --reload
   ```

If another service uses port `5432`, choose a different `POSTGRES_PORT` in
your local `.env` and update `DATABASE_URL` to match. When multiple worktrees
share one Docker host, `COMPOSE_PROJECT_NAME`, `POSTGRES_DB`, and
`POSTGRES_PORT` may be overridden per local `.env`. Separate developers on
separate machines can use the same defaults.

## Migrations And Safety

The initial Alembic revision is infrastructure-only: it creates no product
tables and is immutable after merge. It verifies migration execution on a
fresh database, not real-model autogeneration. Future challenge-specific
models must be registered in `backend.models` and added in new revisions.

`DATABASE_URL` remains optional for the health-only SQLite fallback. Never run
migrations against a real database without explicit approval, and never commit
local `.env` credentials.

## Starter Paths

```text
backend/          FastAPI application foundation and future backend layers
frontend/         Placeholder for a challenge-selected frontend
tests/            Isolated starter verification
migrations/       Alembic migration environment
compose.yaml      PostgreSQL-only local Compose service
.env.example      Safe local configuration template
requirements.txt  Declared Python dependencies
alembic.ini        Alembic configuration
.github/           PostgreSQL-backed CI workflow
```

The paths stay at repository root to preserve verified imports, migration
configuration, Compose behavior, CI behavior, and established onboarding.
