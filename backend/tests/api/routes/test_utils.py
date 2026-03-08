from collections.abc import Generator
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlmodel import Session

from app.api.deps import get_db
from app.core.config import settings
from app.main import app


def test_health_check_returns_200(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}


def test_health_check_db_unreachable_returns_503(client: TestClient) -> None:
    mock_session = MagicMock(spec=Session)
    mock_session.exec.side_effect = OperationalError("connection refused", None, None)

    def _broken_db() -> Generator[MagicMock, None, None]:
        yield mock_session

    app.dependency_overrides[get_db] = _broken_db
    try:
        r = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    finally:
        app.dependency_overrides.pop(get_db)

    assert r.status_code == 503
    body = r.json()
    assert body["title"] == "Service Unavailable"
    assert "Database is not reachable" in body["detail"]
