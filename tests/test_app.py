from fastapi.testclient import TestClient

from backend.main import app


def test_app_imports() -> None:
    assert app.title == "Generic Hackathon Starter"


def test_root_health_response() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_schema_builds() -> None:
    schema = app.openapi()

    assert schema["info"]["title"] == "Generic Hackathon Starter"
    assert "/" in schema["paths"]
