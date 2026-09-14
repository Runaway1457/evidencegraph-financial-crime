from fastapi.testclient import TestClient

from evidencegraph.api.main import app, repository


def setup_function() -> None:
    repository._cases.clear()


def test_health() -> None:
    response = TestClient(app).get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_get_case() -> None:
    client = TestClient(app)
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
    response = TestClient(app).get("/api/v1/cases/not-real")
    assert response.status_code == 404
    assert response.json() == {"detail": "case not found"}
