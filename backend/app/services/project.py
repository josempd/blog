"""Project service — business logic for project sync."""

from __future__ import annotations

from sqlmodel import Session

from app.content.loader import ParsedProject
from app.crud.project import update_github_metadata, upsert_project
from app.models.project import Project
from app.schemas.project import ProjectUpsert
from app.services.github import fetch_repo_metadata


def sync_project_from_content(*, session: Session, parsed: ParsedProject) -> Project:
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
    return upsert_project(
        session=session, source_path=parsed.source_path, data=upsert_data
    )


def enrich_project_github_metadata(
    *, session: Session, project: Project, token: str = ""
) -> bool:
    """Fetch GitHub metadata for a project and persist it.

    Returns True if metadata was successfully fetched and stored, False otherwise.
    Does NOT commit — the caller owns the transaction boundary.
    """
    if not project.repo_url:
        return False
    meta = fetch_repo_metadata(project.repo_url, token=token)
    if not meta:
        return False
    update_github_metadata(
        session=session,
        project=project,
        stars=meta.stars,
        language=meta.language,
        forks=meta.forks,
        last_pushed_at=meta.last_pushed_at,
    )
    return True
