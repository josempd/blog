from __future__ import annotations

from pathlib import Path

import pytest
from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.crud.project import upsert_project
from app.models.project import Project
from app.schemas.project import ProjectUpsert
from app.services import portfolio as portfolio_service
from tests.utils.utils import random_lower_string

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_project(
    db: Session,
    *,
    slug: str | None = None,
    title: str | None = None,
    featured: bool = False,
    sort_order: int = 0,
) -> Project:
    slug = slug or f"svc-proj-{random_lower_string()}"
    title = title or f"Service Project {random_lower_string()}"
    data = ProjectUpsert(
        title=title,
        slug=slug,
        description="A test project",
        featured=featured,
        sort_order=sort_order,
    )
    project = upsert_project(session=db, source_path=f"projects/{slug}.md", data=data)
    db.commit()
    return project


def _cleanup(db: Session) -> None:
    db.exec(Project.__table__.delete())  # type: ignore[arg-type]
    db.commit()


# ---------------------------------------------------------------------------
# Tests — list_projects
# ---------------------------------------------------------------------------


def test_list_projects(db: Session) -> None:
    _cleanup(db)
    _make_project(db, slug="proj-a", title="Project A")
    _make_project(db, slug="proj-b", title="Project B")

    projects, count = portfolio_service.list_projects(session=db)

    slugs = [p.slug for p in projects]
    assert "proj-a" in slugs
    assert "proj-b" in slugs
    assert count == 2
    _cleanup(db)


def test_list_projects_featured_only(db: Session) -> None:
    _cleanup(db)
    _make_project(db, slug="featured-proj", title="Featured Project", featured=True)
    _make_project(db, slug="normal-proj", title="Normal Project", featured=False)

    projects, count = portfolio_service.list_projects(session=db, featured_only=True)

    slugs = [p.slug for p in projects]
    assert "featured-proj" in slugs
    assert "normal-proj" not in slugs
    assert count == 1
    _cleanup(db)


def test_list_projects_empty(db: Session) -> None:
    _cleanup(db)
    projects, count = portfolio_service.list_projects(session=db)
    assert projects == []
    assert count == 0


# ---------------------------------------------------------------------------
# Tests — get_about_page
# ---------------------------------------------------------------------------


def test_get_about_page_found(tmp_path: Path) -> None:
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir(parents=True)
    about_file = pages_dir / "about.md"
    about_file.write_text(
        "---\ntitle: About Me\nslug: about\n---\nI'm a software engineer.",
        encoding="utf-8",
    )

    page = portfolio_service.get_about_page(content_dir=tmp_path)

    assert page.title == "About Me"
    assert page.slug == "about"
    assert "software engineer" in page.content_html


def test_get_about_page_missing(tmp_path: Path) -> None:
    # tmp_path has no pages/about.md
    with pytest.raises(NotFoundError):
        portfolio_service.get_about_page(content_dir=tmp_path)


def test_get_about_page_missing_title(tmp_path: Path) -> None:
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir(parents=True)
    about_file = pages_dir / "about.md"
    about_file.write_text(
        "---\nslug: about\n---\nNo title here.",
        encoding="utf-8",
    )

    with pytest.raises(NotFoundError):
        portfolio_service.get_about_page(content_dir=tmp_path)
