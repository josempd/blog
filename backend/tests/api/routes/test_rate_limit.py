from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.deps import get_db
from app.core.config import settings
from app.main import app


@pytest.fixture()
def rate_limited_client(db: Session) -> Generator[TestClient]:
    """TestClient with rate limiting enabled."""

    def _override_get_db() -> Generator[Session]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    app.state.limiter.enabled = True
    with TestClient(app) as c:
        yield c
    app.state.limiter.enabled = False
    app.dependency_overrides.clear()


def test_login_rate_limit(rate_limited_client: TestClient) -> None:
    url = f"{settings.API_V1_STR}/login/access-token"
    form_data = {"username": "test@example.com", "password": "wrong"}
    headers = {"X-Forwarded-For": "10.0.0.1"}

    for _ in range(5):
        r = rate_limited_client.post(url, data=form_data, headers=headers)
        assert r.status_code != 429

    r = rate_limited_client.post(url, data=form_data, headers=headers)
    assert r.status_code == 429
    body = r.json()
    assert body["title"] == "Too Many Requests"
    assert body["status"] == 429
    assert r.headers["Retry-After"] == "60"


def test_password_recovery_rate_limit(rate_limited_client: TestClient) -> None:
    url = f"{settings.API_V1_STR}/password-recovery/test@example.com"
    headers = {"X-Forwarded-For": "10.0.0.2"}

    for _ in range(3):
        r = rate_limited_client.post(url, headers=headers)
        assert r.status_code != 429

    r = rate_limited_client.post(url, headers=headers)
    assert r.status_code == 429
    body = r.json()
    assert body["title"] == "Too Many Requests"
    assert body["status"] == 429
    assert r.headers["Retry-After"] == "60"


def test_reset_password_rate_limit(rate_limited_client: TestClient) -> None:
    url = f"{settings.API_V1_STR}/reset-password/"
    payload = {"token": "fake", "new_password": "fake12345"}
    headers = {"X-Forwarded-For": "10.0.0.3"}

    for _ in range(3):
        r = rate_limited_client.post(url, json=payload, headers=headers)
        assert r.status_code != 429

    r = rate_limited_client.post(url, json=payload, headers=headers)
    assert r.status_code == 429
    body = r.json()
    assert body["title"] == "Too Many Requests"
    assert body["status"] == 429
    assert r.headers["Retry-After"] == "60"


def test_rate_limit_independent_per_ip(rate_limited_client: TestClient) -> None:
    """Different IPs get independent rate limit counters."""
    url = f"{settings.API_V1_STR}/login/access-token"
    form_data = {"username": "test@example.com", "password": "wrong"}

    ip_a = {"X-Forwarded-For": "10.0.0.4"}
    ip_b = {"X-Forwarded-For": "10.0.0.5"}

    # Exhaust limit for IP A
    for _ in range(5):
        rate_limited_client.post(url, data=form_data, headers=ip_a)
    r = rate_limited_client.post(url, data=form_data, headers=ip_a)
    assert r.status_code == 429

    # IP B still has its own quota
    r = rate_limited_client.post(url, data=form_data, headers=ip_b)
    assert r.status_code != 429
