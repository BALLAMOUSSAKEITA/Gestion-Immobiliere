from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_api_v1_root() -> None:
    response = client.get("/api/v1/")
    assert response.status_code == 200
    assert response.json()["message"] == "Gestion Immobilière API"
