"""Project service — business logic for project sync."""

from __future__ import annotations

from sqlmodel import Session

from app.content.loader import ParsedProject
from app.crud.project import upsert_project
from app.schemas.project import ProjectUpsert


def sync_project_from_content(*, session: Session, parsed: ParsedProject) -> None:
    """Upsert a project from parsed Markdown content.

    Does NOT commit — the caller owns the transaction boundary.
    """
    upsert_data = ProjectUpsert(
        title=parsed.title,
        slug=parsed.slug,
        description=parsed.description,
        content_markdown=parsed.content_markdown,
        content_html=parsed.content_html,
        url=parsed.url,
        repo_url=parsed.repo_url,
        featured=parsed.featured,
        sort_order=parsed.sort_order,
    )
    upsert_project(session=session, source_path=parsed.source_path, data=upsert_data)
