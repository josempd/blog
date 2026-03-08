"""Request middleware: security headers, trace IDs, structured logging, metrics.

Middleware are added to the app in ``main.py``.  Last-added executes first,
so the add order is: Metrics → RequestLogging → TraceId → CORS → SecurityHeaders
(SecurityHeaders runs first).
"""

from __future__ import annotations

import ipaddress
import secrets
import time
import uuid
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Paths to skip for request logging (health/readiness probes)
_SKIP_LOG_PATHS = frozenset(
    {
        "/health",
        "/healthz",
        "/ready",
        "/readiness",
        "/api/v1/utils/health-check/",
    }
)


def anonymize_ip(ip: str | None) -> str | None:
    """Zero last octet (IPv4 /24) or last 80 bits (IPv6 /48)."""
    if not ip:
        return None
    try:
        addr = ipaddress.ip_address(ip)
        if isinstance(addr, ipaddress.IPv4Address):
            return str(ipaddress.IPv4Network(f"{ip}/24", strict=False).network_address)
        return str(ipaddress.IPv6Network(f"{ip}/48", strict=False).network_address)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# 1. Security Headers
# ---------------------------------------------------------------------------


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers (HSTS, CSP, X-Frame-Options, etc.) to all responses.

    Generates a per-request nonce for CSP and stores it in ``request.state.csp_nonce``
    so Jinja2 templates can reference it via ``{{ request.state.csp_nonce }}``.
    """

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self._static_headers: dict[str, str] = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        }
        if settings.ENVIRONMENT != "local":
            self._static_headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains"
            )

        # Build CSP template with {nonce} placeholder
        script_src = "'self' 'nonce-{nonce}'"
        connect_src = "'self'"
        if settings.UMAMI_ENABLED and settings.UMAMI_HOST:
            script_src += f" {settings.UMAMI_HOST}"
            connect_src += f" {settings.UMAMI_HOST}"

        self._csp_template = (
            f"default-src 'none'; "
            f"script-src {script_src}; "
            f"style-src 'self'; "
            f"img-src 'self'; "
            f"font-src 'self'; "
            f"connect-src {connect_src}; "
            f"base-uri 'self'; "
            f"form-action 'self'; "
            f"frame-ancestors 'none'"
        )
        self._csp_header_name = (
            "Content-Security-Policy-Report-Only"
            if settings.CSP_REPORT_ONLY
            else "Content-Security-Policy"
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce
        response = await call_next(request)
        for header, value in self._static_headers.items():
            response.headers[header] = value
        response.headers[self._csp_header_name] = self._csp_template.format(nonce=nonce)
        return response


# ---------------------------------------------------------------------------
# 2. Trace ID
# ---------------------------------------------------------------------------


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Extract trace ID from OTEL span or generate a UUID.

    Binds the trace_id to structlog contextvars so every log line in the
    request scope includes it.  Also sets ``request.state.trace_id`` and
    the ``X-Trace-ID`` response header.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        trace_id = _extract_otel_trace_id() or uuid.uuid4().hex
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(trace_id=trace_id)
        request.state.trace_id = trace_id

        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response


def _extract_otel_trace_id() -> str | None:
    """Try to read trace ID from the current OTEL span, if available."""
    try:
        from opentelemetry import trace  # noqa: PLC0415

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.trace_id:
            return format(ctx.trace_id, "032x")
    except Exception:  # noqa: BLE001
        pass
    return None


# ---------------------------------------------------------------------------
# 3. Request Logging
# ---------------------------------------------------------------------------


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log method, path, status code, and duration for every request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in _SKIP_LOG_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "request_finished",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
            referrer=request.headers.get("referer"),
            user_agent=request.headers.get("user-agent"),
            content_length=response.headers.get("content-length"),
            client_ip=anonymize_ip(
                request.headers.get("x-forwarded-for", "").split(",")[0].strip()
                or (request.client.host if request.client else None)
            ),
        )
        return response


# ---------------------------------------------------------------------------
# 4. Metrics (OTEL)
# ---------------------------------------------------------------------------


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record OTEL metrics per request.  No-op if OTEL is disabled.

    Expects ``app.state.otel_metrics`` to be set by ``setup_observability()``.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        metrics: Any = getattr(request.app.state, "otel_metrics", None)
        if metrics is None:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_s = time.perf_counter() - start

        route_pattern = request.url.path
        if hasattr(request, "scope") and "route" in request.scope:
            route_obj = request.scope["route"]
            if hasattr(route_obj, "path"):
                route_pattern = route_obj.path

        attrs = {
            "http.method": request.method,
            "http.route": route_pattern,
            "http.status_code": response.status_code,
        }
        metrics["request_count"].add(1, attrs)
        metrics["request_duration"].record(duration_s, attrs)
        if response.status_code >= 500:
            metrics["error_count"].add(1, attrs)

        if not request.url.path.startswith(("/api/", "/static/", "/favicon")):
            page_view = metrics.get("page_view_count")
            if page_view:
                page_view.add(1, attrs)

        return response
