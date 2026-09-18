from __future__ import annotations

import os

DEFAULT_DATABASE_URL = "sqlite+pysqlite:///:memory:"


def get_database_url() -> str:
    """Return the configured database URL without requiring a live connection."""
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
