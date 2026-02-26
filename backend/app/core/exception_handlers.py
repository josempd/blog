"""Centralized exception handlers producing RFC 9457 Problem Details.

Call ``register_exception_handlers(app)`` during startup to install all
handlers on the FastAPI application.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.core.exceptions import AppError, ProblemDetail

logger = structlog.get_logger(__name__)

_PROBLEM_CONTENT_TYPE = "application/problem+json"

_HTML_SKIP_PREFIXES = ("/api/", "/docs", "/redoc", "/openapi.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _trace_id_from_request(request: Request) -> str | None:
    return getattr(request.state, "trace_id", None)


def _wants_html(request: Request) -> bool:
    path = request.url.path
    return not any(path.startswith(prefix) for prefix in _HTML_SKIP_PREFIXES)


def _problem_response(
    problem: ProblemDetail, headers: dict[str, str] | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(exclude_none=True),
        media_type=_PROBLEM_CONTENT_TYPE,
        headers=headers,
    )


def _html_error_response(request: Request, status_code: int) -> Response:
    from app.pages.deps import templates

    template = "errors/404.html" if status_code == 404 else "errors/500.html"
    return templates.TemplateResponse(request, template, status_code=status_code)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def _handle_app_error(request: Request, exc: AppError) -> Response:
    trace_id = _trace_id_from_request(request)
    problem = exc.to_problem_detail(trace_id=trace_id)
    logger.warning(
        "app_error",
        status=exc.status_code,
        detail=exc.detail,
        trace_id=trace_id,
        exc_type=type(exc).__name__,
    )
    if _wants_html(request):
        return _html_error_response(request, exc.status_code)
    return _problem_response(problem, headers=exc.headers)


async def _handle_starlette_http(
    request: Request, exc: StarletteHTTPException
) -> Response:
    trace_id = _trace_id_from_request(request)
    problem = ProblemDetail(
        title=exc.detail if isinstance(exc.detail, str) else "HTTP Error",
        status=exc.status_code,
        detail=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        trace_id=trace_id,
    )
    logger.warning(
        "http_error",
        status=exc.status_code,
        detail=exc.detail,
        trace_id=trace_id,
    )
    if _wants_html(request):
        return _html_error_response(request, exc.status_code)
    headers = getattr(exc, "headers", None)
    return _problem_response(problem, headers=headers)


async def _handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    trace_id = _trace_id_from_request(request)
    errors = exc.errors()
    problem = ProblemDetail(
        title="Validation Error",
        status=422,
        detail=f"{len(errors)} validation error(s)",
        trace_id=trace_id,
        errors=list(errors),
    )
    logger.warning(
        "validation_error",
        error_count=len(errors),
        trace_id=trace_id,
    )
    return _problem_response(problem)


async def _handle_unhandled(request: Request, exc: Exception) -> Response:
    trace_id = _trace_id_from_request(request)
    logger.exception(
        "unhandled_error",
        trace_id=trace_id,
        exc_type=type(exc).__name__,
    )
    problem = ProblemDetail(
        title="Internal Server Error",
        status=500,
        detail="An unexpected error occurred",
        trace_id=trace_id,
    )
    if _wants_html(request):
        return _html_error_response(request, 500)
    return _problem_response(problem)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _handle_starlette_http)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unhandled)
