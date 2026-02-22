from datetime import datetime, timezone

from sqlmodel import Session, col, select

from app.models.project import Project


def get_projects(*, session: Session, featured_only: bool = False) -> list[Project]:
    statement = select(Project)
    if featured_only:
        statement = statement.where(Project.featured == True)  # noqa: E712
    statement = statement.order_by(
        col(Project.sort_order).asc(), col(Project.created_at).desc()
    )
    return list(session.exec(statement).all())


def get_project_by_slug(*, session: Session, slug: str) -> Project | None:
    statement = select(Project).where(Project.slug == slug)
    return session.exec(statement).first()


def upsert_project(*, session: Session, source_path: str, data: dict) -> Project:
    statement = select(Project).where(Project.source_path == source_path)
    existing = session.exec(statement).first()
    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.now(timezone.utc)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    project = Project(source_path=source_path, **data)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project
