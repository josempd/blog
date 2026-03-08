from fastapi.testclient import TestClient

from app.core.config import settings


def test_health_check_returns_200(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}


def test_health_check_response_schema(client: TestClient) -> None:
    data = client.get(f"{settings.API_V1_STR}/utils/health-check/").json()
    assert set(data.keys()) == {"status"}
    assert isinstance(data["status"], str)
