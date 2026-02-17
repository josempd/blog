"""Request middleware: trace IDs, structured request logging, OTEL metrics.

Middleware are added to the app in ``main.py``.  Last-added executes first,
so the add order is: Metrics → RequestLogging → TraceId (TraceId runs first).
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)

# Paths to skip for request logging (health/readiness probes)
_SKIP_LOG_PATHS = frozenset({"/health", "/healthz", "/ready", "/readiness"})


# ---------------------------------------------------------------------------
# 1. Trace ID
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
# 2. Request Logging
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
        )
        return response


# ---------------------------------------------------------------------------
# 3. Metrics (OTEL)
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

        attrs = {
            "http.method": request.method,
            "http.route": request.url.path,
            "http.status_code": response.status_code,
        }
        metrics["request_count"].add(1, attrs)
        metrics["request_duration"].record(duration_s, attrs)
        if response.status_code >= 500:
            metrics["error_count"].add(1, attrs)

        return response
