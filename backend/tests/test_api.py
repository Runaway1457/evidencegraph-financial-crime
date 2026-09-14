from fastapi.testclient import TestClient

from evidencegraph.api.main import create_app
from evidencegraph.config import Settings
from evidencegraph.infrastructure.memory import InMemoryCaseRepository

repository = InMemoryCaseRepository()
app = create_app(
    settings_override=Settings(environment="test"),
    repository_override=repository,
)
client = TestClient(app)


def setup_function() -> None:
    repository._cases.clear()


def test_health_and_readiness() -> None:
    live = client.get("/health/live")
    ready = client.get("/health/ready")
    assert live.status_code == 200
    assert live.json()["status"] == "ok"
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_create_and_get_case() -> None:
    created = client.post(
        "/api/v1/cases",
        headers={"X-Actor-ID": "analyst_1"},
        json={"title": "Project Meridian", "description": "Synthetic investigation"},
    )
    assert created.status_code == 201

    case_id = created.json()["id"]
    fetched = client.get(f"/api/v1/cases/{case_id}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Project Meridian"


def test_unknown_case_does_not_leak_details() -> None:
    response = client.get("/api/v1/cases/not-real")
    assert response.status_code == 404
    assert response.json() == {"detail": "case not found"}
