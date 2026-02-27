from datetime import datetime

from sqlmodel import Session, col, func, select

from app.models.base import get_datetime_utc
from app.models.project import Project
from app.schemas.project import ProjectUpsert


def get_projects(
    *,
    session: Session,
    featured_only: bool = False,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Project], int]:
    base = select(Project)
    count_base = select(func.count()).select_from(Project)

    if featured_only:
        base = base.where(Project.featured == True)  # noqa: E712
        count_base = count_base.where(Project.featured == True)  # noqa: E712

    count = session.exec(count_base).one()
    projects = session.exec(
        base.order_by(col(Project.sort_order).asc(), col(Project.created_at).desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return list(projects), count


def get_project_by_slug(*, session: Session, slug: str) -> Project | None:
    statement = select(Project).where(Project.slug == slug)
    return session.exec(statement).first()


def upsert_project(
    *, session: Session, source_path: str, data: ProjectUpsert
) -> Project:
    statement = select(Project).where(Project.source_path == source_path)
    existing = session.exec(statement).first()
    if existing:
        existing.sqlmodel_update(data.model_dump())
        existing.updated_at = get_datetime_utc()
        session.add(existing)
        session.flush()
        session.refresh(existing)
        return existing
    project = Project(source_path=source_path, **data.model_dump())
    session.add(project)
    session.flush()
    session.refresh(project)
    return project


def update_github_metadata(
    *,
    session: Session,
    project: Project,
    stars: int,
    language: str | None,
    forks: int,
    last_pushed_at: datetime | None,
) -> None:
    """Update GitHub-sourced metadata fields on an existing project.

    Does NOT commit — the caller owns the transaction boundary.
    """
    project.github_stars = stars
    project.github_language = language
    project.github_forks = forks
    project.github_last_pushed_at = last_pushed_at
    session.add(project)
    session.flush()


def delete_projects_not_in(*, session: Session, source_paths: set[str]) -> int:
    """Delete projects whose source_path is not in the given set. Returns count deleted."""
    statement = select(Project).where(Project.source_path.is_not(None))  # type: ignore[union-attr]
    all_projects = session.exec(statement).all()
    deleted = 0
    for project in all_projects:
        if project.source_path not in source_paths:
            session.delete(project)
            deleted += 1
    if deleted:
        session.flush()
    return deleted
