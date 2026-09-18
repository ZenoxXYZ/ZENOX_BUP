# PostgreSQL Foundation

## Objective

Add a reproducible local PostgreSQL and Alembic foundation without adding
challenge-specific models, tables, seed records, APIs, or frontend behavior.

## Design Decisions

- Compose runs PostgreSQL only; FastAPI, Alembic, and pytest remain host-run.
- `DATABASE_URL` remains environment-driven. Compose reads local `.env`, while
  host Python commands receive the URL from their shell environment.
- `0001_foundation_baseline` is infrastructure-only, creates no schema, and is
  immutable after merge. Future challenge migrations must depend on it.
- `backend.models` is the explicit future mapped-model registration point for
  Alembic metadata discovery.
- CI is configured for PostgreSQL readiness, migration upgrade, then pytest.

## Verification At This Checkpoint

- `python -m pytest` passed: 6 tests, including shared configured-engine
  connectivity under the SQLite fallback.
- `python -m pip check` passed.
- Isolated SQLite migration upgrade and downgrade passed; the version table
  recorded `0001_foundation_baseline` before downgrade.
- Supervisor-verified local PostgreSQL execution passed using an alternate
  host port because native Windows PostgreSQL occupied `5432`: container
  startup/health, host connectivity, Alembic upgrade/current, version
  tracking, and all 6 pytest tests against PostgreSQL passed.
- `docker-compose config` validated the Compose file. This agent environment
  cannot access the Docker daemon, so it did not independently repeat that
  successful local PostgreSQL run.
- Draft PR #3 CI passed its PostgreSQL readiness, Alembic upgrade, and pytest
  job.

## Explicit Deferrals

- Real-model Alembic autogeneration, non-trivial schema migrations, and a
  seed-data workflow remain unverified.
- No seed convention, domain models, product migrations, Dockerfiles,
  lockfiles, or application containers were introduced.
