from datetime import datetime, timezone

from sqlmodel import Session, col, func, select

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
        existing.updated_at = datetime.now(timezone.utc)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    project = Project(source_path=source_path, **data.model_dump())
    session.add(project)
    session.commit()
    session.refresh(project)
    return project
