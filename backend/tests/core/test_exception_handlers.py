"""Tests for app.core.exception_handlers — uncovered handler paths."""

import asyncio
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.exception_handlers import _handle_rate_limit, _handle_unhandled

# ---------------------------------------------------------------------------
# _handle_unhandled — JSON path (lines 148-156)
# ---------------------------------------------------------------------------


def test_unhandled_exception_json() -> None:
    """_handle_unhandled returns 500 problem+json for an API-prefixed path."""

    async def _run() -> None:
        mock_request = MagicMock()
        mock_request.url.path = "/api/v1/utils/health-check/"
        mock_request.state.trace_id = "abc123"

        response = await _handle_unhandled(mock_request, RuntimeError("boom"))
        assert response.status_code == 500
        assert response.media_type == "application/problem+json"

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# _handle_unhandled — HTML path (lines 154-155)
# ---------------------------------------------------------------------------


def test_unhandled_exception_html() -> None:
    """_handle_unhandled returns 500 HTML for a non-API page path."""

    async def _run() -> None:
        mock_request = MagicMock()
        mock_request.url.path = "/blog"
        mock_request.state.trace_id = "abc123"

        response = await _handle_unhandled(mock_request, RuntimeError("boom"))
        assert response.status_code == 500
        assert "text/html" in response.media_type

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# _handle_starlette_http — HTML path (lines 115-116)
# ---------------------------------------------------------------------------


def test_unknown_page_route_404_html(client: TestClient) -> None:
    """A request to an unknown page route returns 404 HTML."""
    response = client.get("/unknown-page-xyz")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# _handle_starlette_http — JSON path (lines 117-118)
# ---------------------------------------------------------------------------


def test_unknown_api_route_404_problem_json(client: TestClient) -> None:
    """A request to an unknown API route returns 404 problem+json."""
    response = client.get(f"{settings.API_V1_STR}/nonexistent-route-xyz")
    assert response.status_code == 404
    assert "application/problem+json" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# _handle_validation_error (lines 124-138)
# ---------------------------------------------------------------------------


def test_validation_error_problem_detail(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Malformed request body returns 422 problem+json with errors list."""
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json={},
    )
    assert response.status_code == 422
    assert "application/problem+json" in response.headers["content-type"]
    body = response.json()
    assert body["title"] == "Validation Error"
    assert "errors" in body
    assert isinstance(body["errors"], list)
    assert len(body["errors"]) > 0


# ---------------------------------------------------------------------------
# _handle_rate_limit — HTML path (lines 79-80) — direct async call
# ---------------------------------------------------------------------------


def test_rate_limit_html_path() -> None:
    """_handle_rate_limit returns 429 HTML for a non-API path."""

    async def _run() -> None:
        mock_request = MagicMock()
        mock_request.url.path = "/blog"
        mock_request.state.trace_id = "abc123"
        mock_request.headers.get.return_value = None
        mock_request.client.host = "127.0.0.1"

        mock_limit = MagicMock()
        exc = RateLimitExceeded(mock_limit)

        response = await _handle_rate_limit(mock_request, exc)
        assert response.status_code == 429
        assert "text/html" in response.media_type

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# _handle_app_error — HTML path (lines 94-95)
# ---------------------------------------------------------------------------


def test_app_error_html_path(client: TestClient) -> None:
    """Requesting a nonexistent blog slug returns 404 HTML."""
    response = client.get("/blog/nonexistent-slug-xyz")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# trace_id in problem+json responses (line 32)
# ---------------------------------------------------------------------------


def test_problem_response_includes_trace_id(client: TestClient) -> None:
    """Error responses that return problem+json include a trace_id field."""
    response = client.get(f"{settings.API_V1_STR}/nonexistent-route-xyz")
    assert response.status_code == 404
    body = response.json()
    assert "trace_id" in body
    # trace_id is a 32-char hex string (UUID without hyphens) set by TraceIdMiddleware
    trace_id = body["trace_id"]
    assert isinstance(trace_id, str) and len(trace_id) == 32
