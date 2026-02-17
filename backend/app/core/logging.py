"""Structured logging setup via structlog.

Call ``setup_logging()`` once at application startup — before any other
imports that use ``logging`` or ``structlog``.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

# ---------------------------------------------------------------------------
# Sensitive data filter
# ---------------------------------------------------------------------------

_REDACTED = "**REDACTED**"
_SENSITIVE_KEYS = frozenset(
    {"password", "token", "secret_key", "authorization", "cookie", "access_token"}
)


def _sensitive_data_filter(
    _logger: Any, _method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    for key in event_dict:
        if key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = _REDACTED
    return event_dict


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def setup_logging(*, log_level: str = "INFO", json_output: bool = True) -> None:
    """Configure structlog + stdlib logging.

    Args:
        log_level: Root log level name (DEBUG, INFO, WARNING, ERROR).
        json_output: ``True`` for JSON lines (prod), ``False`` for coloured
            console output (dev).
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [  # type: ignore[assignment]
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        _sensitive_data_filter,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet noisy third-party loggers
    for name in ("uvicorn.access", "sqlalchemy.engine", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name)
