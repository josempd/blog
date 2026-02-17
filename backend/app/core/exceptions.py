"""Domain exception hierarchy and RFC 9457 Problem Details schema.

All domain exceptions inherit from AppError and carry enough context for
the exception handlers to produce a Problem Details JSON response.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ProblemDetail(BaseModel):
    """RFC 9457 Problem Details for HTTP APIs."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str
    trace_id: str | None = None
    errors: list[dict[str, Any]] | None = None


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class AppError(Exception):
    """Base for all domain exceptions.

    Subclasses set class-level defaults for ``status_code``, ``problem_type``
    and ``title``.  Instances can override ``detail``, ``headers`` and carry
    arbitrary ``extras`` for the Problem Details response body.
    """

    status_code: int = 500
    problem_type: str = "about:blank"
    title: str = "Internal Server Error"

    def __init__(
        self,
        detail: str = "",
        *,
        headers: dict[str, str] | None = None,
        extras: dict[str, Any] | None = None,
    ) -> None:
        self.detail = detail or self.title
        self.headers = headers
        self.extras = extras or {}
        super().__init__(self.detail)

    def to_problem_detail(self, *, trace_id: str | None = None) -> ProblemDetail:
        return ProblemDetail(
            type=self.problem_type,
            title=self.title,
            status=self.status_code,
            detail=self.detail,
            trace_id=trace_id,
            **(self.extras),
        )


# ---------------------------------------------------------------------------
# 4xx
# ---------------------------------------------------------------------------


class BadRequestError(AppError):
    status_code = 400
    title = "Bad Request"


class UnauthorizedError(AppError):
    status_code = 401
    title = "Unauthorized"

    def __init__(
        self, detail: str = "Could not validate credentials", **kwargs: Any
    ) -> None:
        super().__init__(detail, headers={"WWW-Authenticate": "Bearer"}, **kwargs)


class ForbiddenError(AppError):
    status_code = 403
    title = "Forbidden"

    def __init__(self, detail: str = "Not enough permissions", **kwargs: Any) -> None:
        super().__init__(detail, **kwargs)


class NotFoundError(AppError):
    status_code = 404
    title = "Not Found"

    def __init__(self, resource: str, identifier: Any = "") -> None:
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} not found: {identifier}"
        super().__init__(detail)


class ConflictError(AppError):
    status_code = 409
    title = "Conflict"


class ValidationError(AppError):
    status_code = 422
    title = "Validation Error"


# ---------------------------------------------------------------------------
# 5xx
# ---------------------------------------------------------------------------


class ServiceUnavailableError(AppError):
    status_code = 503
    title = "Service Unavailable"


class ContentSyncError(AppError):
    status_code = 500
    title = "Content Sync Error"
