from __future__ import annotations

from datetime import datetime, timezone

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


# ---------------------------------------------------------------------------
# Seed fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def seed_projects(db: Session) -> None:
    _make_project(
        db,
        slug="test-project",
        title="Test Project",
        description="A project for testing",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("seed_projects")
def test_projects_page(client: TestClient) -> None:
    response = client.get("/projects")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Test Project" in response.text


@pytest.mark.usefixtures("seed_projects")
def test_projects_page_shows_description(client: TestClient) -> None:
    response = client.get("/projects")
    assert response.status_code == 200
    assert "A project for testing" in response.text


def test_about_page(client: TestClient) -> None:
    # about.md exists at content/pages/about.md in the repo
    response = client.get("/about")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "About" in response.text


def test_about_has_jsonld_person(client: TestClient) -> None:
    response = client.get("/about")
    assert response.status_code == 200
    assert '"@type": "Person"' in response.text
    assert '"name":' in response.text


def test_about_has_canonical(client: TestClient) -> None:
    response = client.get("/about")
    assert response.status_code == 200
    assert 'rel="canonical"' in response.text
    assert "/about" in response.text


def test_privacy_page(client: TestClient) -> None:
    response = client.get("/privacy")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Privacy Policy" in response.text


def test_privacy_has_canonical(client: TestClient) -> None:
    response = client.get("/privacy")
    assert response.status_code == 200
    assert 'rel="canonical"' in response.text
    assert "/privacy" in response.text


def test_project_card_renders_github_metadata(client: TestClient, db: Session) -> None:
    project = _make_project(db)
    project.github_stars = 42
    project.github_language = "Python"
    project.github_forks = 5
    project.github_last_pushed_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
    db.add(project)
    db.commit()

    response = client.get("/projects")
    assert response.status_code == 200
    assert "Python" in response.text
    assert "42" in response.text
    assert "aria-label" in response.text


def test_project_card_without_metadata_renders_cleanly(
    client: TestClient, db: Session
) -> None:
    project = _make_project(db)

    response = client.get("/projects")
    assert response.status_code == 200
    assert project.title in response.text
