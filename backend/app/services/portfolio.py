from __future__ import annotations

from pathlib import Path

from sqlmodel import Session

from app.content.loader import ParsedPage, load_page
from app.core.exceptions import NotFoundError
from app.crud.project import get_projects
from app.models.project import Project


def list_projects(
    *, session: Session, featured_only: bool = False, skip: int = 0, limit: int = 50
) -> tuple[list[Project], int]:
    return get_projects(
        session=session, featured_only=featured_only, skip=skip, limit=limit
    )


def get_about_page(*, content_dir: Path) -> ParsedPage:
    file_path = content_dir / "pages" / "about.md"
    try:
        return load_page(file_path, content_dir)
    except (FileNotFoundError, ValueError) as exc:
        raise NotFoundError("Page", "about") from exc
