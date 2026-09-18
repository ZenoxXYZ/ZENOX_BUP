from sqlalchemy import text

from backend.database import engine


def test_configured_database_engine_connects() -> None:
    """Use the configured engine under SQLite fallback or PostgreSQL."""
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
