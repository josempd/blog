from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.core.config import settings

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

templates.env.globals.update(
    {
        "site_title": settings.SITE_TITLE,
        "site_author": settings.SITE_AUTHOR,
        "site_description": settings.SITE_DESCRIPTION,
        "github_username": settings.GITHUB_USERNAME,
        "current_year": datetime.now(timezone.utc).year,
    }
)


def _rfc822_filter(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return format_datetime(dt, usegmt=True)


templates.env.filters["rfc822"] = _rfc822_filter


def is_htmx_request(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def content_dir() -> Path:
    path = Path(settings.CONTENT_DIR)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[3] / path
    return path
