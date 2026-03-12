from collections.abc import Generator
from unittest.mock import MagicMock, patch

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

    def _broken_db() -> Generator[MagicMock]:
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


def test_test_email_success(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    with patch("app.api.routes.utils.send_email"):
        r = client.post(
            f"{settings.API_V1_STR}/utils/test-email/",
            params={"email_to": "test@example.com"},
            headers=superuser_token_headers,
        )
    assert r.status_code == 201
    assert r.json() == {"message": "Test email sent"}


def test_test_email_requires_superuser(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    with patch("app.api.routes.utils.send_email"):
        r = client.post(
            f"{settings.API_V1_STR}/utils/test-email/",
            params={"email_to": "test@example.com"},
            headers=normal_user_token_headers,
        )
    assert r.status_code == 403


def test_test_email_rejects_unauthenticated(client: TestClient) -> None:
    with patch("app.api.routes.utils.send_email"):
        r = client.post(
            f"{settings.API_V1_STR}/utils/test-email/",
            params={"email_to": "test@example.com"},
        )
    assert r.status_code == 401
