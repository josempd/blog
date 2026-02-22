from sqlmodel import Session

from app.crud.project import get_project_by_slug, get_projects, upsert_project
from tests.utils.utils import random_lower_string


def _project_data(**overrides: object) -> dict:
    defaults = {
        "title": f"Project {random_lower_string()}",
        "slug": f"project-{random_lower_string()}",
        "description": "A test project",
    }
    defaults.update(overrides)
    return defaults


def test_upsert_project_creates_new(db: Session) -> None:
    source = f"projects/{random_lower_string()}.md"
    data = _project_data()
    project = upsert_project(session=db, source_path=source, data=data)
    assert project.id is not None
    assert project.title == data["title"]
    assert project.slug == data["slug"]
    assert project.source_path == source
    assert project.created_at is not None
    assert project.updated_at is None


def test_upsert_project_updates_existing(db: Session) -> None:
    source = f"projects/{random_lower_string()}.md"
    data = _project_data()
    project1 = upsert_project(session=db, source_path=source, data=data)
    original_id = project1.id

    updated_data = _project_data(title="Updated Project")
    project2 = upsert_project(session=db, source_path=source, data=updated_data)
    assert project2.id == original_id
    assert project2.title == "Updated Project"
    assert project2.updated_at is not None


def test_get_projects(db: Session) -> None:
    source = f"projects/{random_lower_string()}.md"
    data = _project_data()
    upsert_project(session=db, source_path=source, data=data)

    projects = get_projects(session=db)
    assert len(projects) >= 1
    slugs = [p.slug for p in projects]
    assert data["slug"] in slugs


def test_get_projects_featured_only(db: Session) -> None:
    featured_slug = f"featured-{random_lower_string()}"
    normal_slug = f"normal-{random_lower_string()}"

    upsert_project(
        session=db,
        source_path=f"projects/{featured_slug}.md",
        data=_project_data(slug=featured_slug, featured=True),
    )
    upsert_project(
        session=db,
        source_path=f"projects/{normal_slug}.md",
        data=_project_data(slug=normal_slug, featured=False),
    )

    projects = get_projects(session=db, featured_only=True)
    slugs = [p.slug for p in projects]
    assert featured_slug in slugs
    assert normal_slug not in slugs


def test_get_project_by_slug(db: Session) -> None:
    source = f"projects/{random_lower_string()}.md"
    data = _project_data()
    upsert_project(session=db, source_path=source, data=data)

    found = get_project_by_slug(session=db, slug=data["slug"])
    assert found is not None
    assert found.slug == data["slug"]


def test_get_project_by_slug_not_found(db: Session) -> None:
    found = get_project_by_slug(session=db, slug="nonexistent-project")
    assert found is None
