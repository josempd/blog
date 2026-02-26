from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.crud.project import upsert_project
from app.models.project import Project
from app.schemas.project import ProjectUpsert
from tests.utils.utils import random_lower_string

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_project(
    db: Session,
    *,
    slug: str | None = None,
    title: str | None = None,
    description: str = "A test project",
) -> Project:
    slug = slug or f"project-{random_lower_string()}"
    title = title or f"Project {random_lower_string()}"
    data = ProjectUpsert(
        title=title,
        slug=slug,
        description=description,
    )
    project = upsert_project(session=db, source_path=f"projects/{slug}.md", data=data)
    db.commit()
    return project


def _cleanup(db: Session) -> None:
    db.exec(Project.__table__.delete())  # type: ignore[arg-type]
    db.commit()


# ---------------------------------------------------------------------------
# Module-scoped seed fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def seed_projects(client: TestClient, db: Session):  # noqa: ARG001
    _make_project(
        db,
        slug="test-project",
        title="Test Project",
        description="A project for testing",
    )
    yield
    _cleanup(db)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_projects_page(client: TestClient) -> None:
    response = client.get("/projects")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Test Project" in response.text


def test_projects_page_shows_description(client: TestClient) -> None:
    response = client.get("/projects")
    assert response.status_code == 200
    assert "A project for testing" in response.text


def test_projects_empty_state(client: TestClient, db: Session) -> None:
    _cleanup(db)
    response = client.get("/projects")
    assert response.status_code == 200
    assert "No projects" in response.text


def test_about_page(client: TestClient) -> None:
    # about.md exists at content/pages/about.md in the repo
    response = client.get("/about")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "About" in response.text
