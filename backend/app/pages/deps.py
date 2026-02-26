from __future__ import annotations

import functools
import json
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.core.config import settings

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent
    / "static"
    / "dist"
    / "islands"
    / ".vite"
    / "manifest.json"
)


@functools.lru_cache(maxsize=1)
def _load_manifest() -> dict[str, Any]:
    """Load and cache the Vite manifest (immutable after deployment)."""
    if not _MANIFEST_PATH.exists():
        return {}
    return json.loads(_MANIFEST_PATH.read_text())


def island_asset(name: str) -> str | None:
    """Resolve a hashed island filename from the Vite manifest."""
    manifest = _load_manifest()
    entry = manifest.get(f"src/{name}.js")
    if isinstance(entry, dict) and "file" in entry:
        return f"/static/dist/islands/{entry['file']}"
    return None


templates.env.globals.update(
    {
        "site_title": settings.SITE_TITLE,
        "site_author": settings.SITE_AUTHOR,
        "site_description": settings.SITE_DESCRIPTION,
        "github_username": settings.GITHUB_USERNAME,
        "current_year": datetime.now(timezone.utc).year,
        "island_asset": island_asset,
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
