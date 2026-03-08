"""Tests for app.core.middleware: anonymize_ip and request logging."""

from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.middleware import anonymize_ip

# ---------------------------------------------------------------------------
# anonymize_ip — pure unit tests, no fixtures needed
# ---------------------------------------------------------------------------


def test_anonymize_ip_v4() -> None:
    assert anonymize_ip("192.168.1.100") == "192.168.1.0"


def test_anonymize_ip_v4_first_octet_preserved() -> None:
    assert anonymize_ip("10.0.5.255") == "10.0.5.0"


def test_anonymize_ip_v6() -> None:
    # /48 zeros everything after the first 48 bits (3 groups).
    result = anonymize_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
    assert result == "2001:db8:85a3::"


def test_anonymize_ip_v6_trailing_bits_cleared() -> None:
    # Any address in the same /48 prefix should map to the same network address.
    result = anonymize_ip("2001:db8:1:ffff:ffff:ffff:ffff:ffff")
    assert result == "2001:db8:1::"


def test_anonymize_ip_none() -> None:
    assert anonymize_ip(None) is None


def test_anonymize_ip_invalid() -> None:
    assert anonymize_ip("not-an-ip") is None


def test_anonymize_ip_empty_string() -> None:
    assert anonymize_ip("") is None


# ---------------------------------------------------------------------------
# RequestLoggingMiddleware — integration tests via TestClient
# ---------------------------------------------------------------------------


def test_request_log_enriched_fields(client: TestClient) -> None:
    """logger.info is called with referrer, user_agent, client_ip, content_length."""
    mock_logger = MagicMock()

    with (
        patch("app.core.middleware._SKIP_LOG_PATHS", frozenset()),
        patch("app.core.middleware.logger", mock_logger),
    ):
        client.get(
            "/api/v1/utils/health-check/",
            headers={
                "Referer": "https://example.com/page",
                "User-Agent": "TestAgent/1.0",
            },
        )

    mock_logger.info.assert_called_once()
    call_kwargs = mock_logger.info.call_args.kwargs

    assert call_kwargs.get("referrer") == "https://example.com/page"
    assert call_kwargs.get("user_agent") == "TestAgent/1.0"
    # client_ip is derived from test client; None is acceptable in test env
    assert "client_ip" in call_kwargs
    assert "content_length" in call_kwargs


def test_request_log_event_name(client: TestClient) -> None:
    """The log event name is 'request_finished'."""
    mock_logger = MagicMock()

    with (
        patch("app.core.middleware._SKIP_LOG_PATHS", frozenset()),
        patch("app.core.middleware.logger", mock_logger),
    ):
        client.get("/api/v1/utils/health-check/")

    mock_logger.info.assert_called_once()
    event = mock_logger.info.call_args.args[0]
    assert event == "request_finished"


def test_request_log_method_path_status(client: TestClient) -> None:
    """method, path, status, and duration_ms are all present in the log call."""
    mock_logger = MagicMock()

    with (
        patch("app.core.middleware._SKIP_LOG_PATHS", frozenset()),
        patch("app.core.middleware.logger", mock_logger),
    ):
        client.get("/api/v1/utils/health-check/")

    call_kwargs = mock_logger.info.call_args.kwargs
    assert call_kwargs.get("method") == "GET"
    assert call_kwargs.get("path") == "/api/v1/utils/health-check/"
    assert call_kwargs.get("status") == 200
    assert isinstance(call_kwargs.get("duration_ms"), float)


def test_health_endpoint_skipped(client: TestClient) -> None:
    """Requests to skip-listed paths produce no 'request_finished' log."""
    mock_logger = MagicMock()

    with patch("app.core.middleware.logger", mock_logger):
        # /health is in _SKIP_LOG_PATHS; the route does not exist (404) but
        # the middleware short-circuits before logging.
        client.get("/health")

    mock_logger.info.assert_not_called()


def test_health_variants_skipped(client: TestClient) -> None:
    """All health/readiness probe paths are skipped."""
    skip_paths = ["/healthz", "/ready", "/readiness", "/api/v1/utils/health-check/"]
    mock_logger = MagicMock()

    with patch("app.core.middleware.logger", mock_logger):
        for path in skip_paths:
            client.get(path)

    mock_logger.info.assert_not_called()


def test_x_forwarded_for_used_for_client_ip(client: TestClient) -> None:
    """X-Forwarded-For header is anonymized and used as client_ip."""
    mock_logger = MagicMock()

    with (
        patch("app.core.middleware._SKIP_LOG_PATHS", frozenset()),
        patch("app.core.middleware.logger", mock_logger),
    ):
        client.get(
            "/api/v1/utils/health-check/",
            headers={"X-Forwarded-For": "203.0.113.195, 70.41.3.18"},
        )

    call_kwargs = mock_logger.info.call_args.kwargs
    # First IP in the list (203.0.113.195) → /24 → 203.0.113.0
    assert call_kwargs.get("client_ip") == "203.0.113.0"


# ---------------------------------------------------------------------------
# SecurityHeadersMiddleware — integration tests via TestClient
# ---------------------------------------------------------------------------


def test_security_headers_present(client: TestClient) -> None:
    """All static security headers are set on every response."""
    response = client.get("/api/v1/utils/health-check/")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert (
        response.headers["Permissions-Policy"]
        == "camera=(), microphone=(), geolocation=()"
    )


def test_csp_header_contains_nonce(client: TestClient) -> None:
    """CSP header includes a nonce in script-src."""
    response = client.get("/api/v1/utils/health-check/")
    csp = response.headers.get("Content-Security-Policy-Report-Only", "")
    assert "nonce-" in csp
    assert "script-src 'self' 'nonce-" in csp


def test_csp_nonce_unique_per_request(client: TestClient) -> None:
    """Each request gets a different nonce."""
    r1 = client.get("/api/v1/utils/health-check/")
    r2 = client.get("/api/v1/utils/health-check/")
    csp1 = r1.headers.get("Content-Security-Policy-Report-Only", "")
    csp2 = r2.headers.get("Content-Security-Policy-Report-Only", "")
    nonces = [re.search(r"nonce-([A-Za-z0-9_-]+)", csp) for csp in [csp1, csp2]]
    assert nonces[0] and nonces[1]
    assert nonces[0].group(1) != nonces[1].group(1)


def test_no_hsts_in_local(client: TestClient) -> None:
    """HSTS is not set when ENVIRONMENT is 'local' (test default)."""
    response = client.get("/api/v1/utils/health-check/")
    assert "Strict-Transport-Security" not in response.headers
