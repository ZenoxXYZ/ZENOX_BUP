from backend.config import DEFAULT_DATABASE_URL, get_database_url


def test_database_url_uses_safe_default_when_unset(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert get_database_url() == DEFAULT_DATABASE_URL


def test_database_url_comes_from_environment(monkeypatch) -> None:
    url = "postgresql+psycopg://localhost:5432/app"
    monkeypatch.setenv("DATABASE_URL", url)

    assert get_database_url() == url
