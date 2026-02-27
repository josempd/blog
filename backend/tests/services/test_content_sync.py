"""Integration tests for services.content_sync — uses tmp_path + real DB session."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlmodel import Session, select

from app.core.exceptions import ContentSyncError
from app.models.post import Post, PostTagLink, Tag
from app.models.project import Project
from app.services.content_sync import sync_content
from app.services.github import GitHubRepoMeta

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_md(directory: Path, filename: str, content: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(content, encoding="utf-8")
    return path


def _setup_post(
    content_dir: Path, filename: str, *, title: str, **kwargs: object
) -> Path:
    lines = [f"title: {title}"]
    for key, value in kwargs.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    frontmatter = "\n".join(lines)
    return _write_md(content_dir / "posts", filename, f"---\n{frontmatter}\n---\nBody.")


def _setup_project(
    content_dir: Path, filename: str, *, title: str, **kwargs: object
) -> Path:
    lines = [f"title: {title}"]
    for key, value in kwargs.items():
        lines.append(f"{key}: {value}")
    frontmatter = "\n".join(lines)
    return _write_md(
        content_dir / "projects", filename, f"---\n{frontmatter}\n---\nBody."
    )


def _get_post(session: Session, slug: str) -> Post | None:
    return session.exec(select(Post).where(Post.slug == slug)).first()


def _get_project(session: Session, slug: str) -> Project | None:
    return session.exec(select(Project).where(Project.slug == slug)).first()


def _cleanup(session: Session) -> None:
    session.exec(PostTagLink.__table__.delete())  # type: ignore[arg-type]
    session.exec(Tag.__table__.delete())  # type: ignore[arg-type]
    session.exec(Post.__table__.delete())  # type: ignore[arg-type]
    session.exec(Project.__table__.delete())  # type: ignore[arg-type]
    session.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_sync_creates_posts_and_projects(db: Session, tmp_path: Path) -> None:
    _cleanup(db)
    _setup_post(tmp_path, "2024-01-01-hello.md", title="Hello", published="true")
    _setup_project(tmp_path, "my-project.md", title="My Project")

    sync_content(session=db, content_dir=tmp_path)

    assert _get_post(db, "hello") is not None
    assert _get_project(db, "my-project") is not None
    _cleanup(db)


def test_idempotent_resync(db: Session, tmp_path: Path) -> None:
    _cleanup(db)
    _setup_post(tmp_path, "2024-01-01-idem.md", title="Idempotent")

    sync_content(session=db, content_dir=tmp_path)
    post1 = _get_post(db, "idem")
    assert post1 is not None
    first_id = post1.id

    sync_content(session=db, content_dir=tmp_path)
    post2 = _get_post(db, "idem")
    assert post2 is not None
    assert post2.id == first_id

    count = db.exec(select(Post).where(Post.slug == "idem")).all()
    assert len(count) == 1
    _cleanup(db)


def test_content_updates_propagate(db: Session, tmp_path: Path) -> None:
    _cleanup(db)
    path = _setup_post(tmp_path, "2024-01-01-update.md", title="Original")
    sync_content(session=db, content_dir=tmp_path)

    post = _get_post(db, "update")
    assert post is not None
    assert post.title == "Original"

    path.write_text("---\ntitle: Updated\n---\nNew body.", encoding="utf-8")
    sync_content(session=db, content_dir=tmp_path)

    db.expire_all()
    post = _get_post(db, "update")
    assert post is not None
    assert post.title == "Updated"
    _cleanup(db)


def test_tags_created_and_associated(db: Session, tmp_path: Path) -> None:
    _cleanup(db)
    _setup_post(
        tmp_path,
        "2024-01-01-tagged.md",
        title="Tagged",
        tags=["python", "fastapi"],
    )

    sync_content(session=db, content_dir=tmp_path)

    post = _get_post(db, "tagged")
    assert post is not None
    tag_names = sorted(t.name for t in post.tags)
    assert tag_names == ["fastapi", "python"]
    _cleanup(db)


def test_orphan_cleanup(db: Session, tmp_path: Path) -> None:
    _cleanup(db)
    _setup_post(tmp_path, "2024-01-01-keep.md", title="Keep")
    _setup_post(tmp_path, "2024-01-01-remove.md", title="Remove")
    _setup_project(tmp_path, "keep-proj.md", title="Keep Proj")
    _setup_project(tmp_path, "remove-proj.md", title="Remove Proj")

    sync_content(session=db, content_dir=tmp_path)
    assert _get_post(db, "keep") is not None
    assert _get_post(db, "remove") is not None
    assert _get_project(db, "keep-proj") is not None
    assert _get_project(db, "remove-proj") is not None

    # Delete the markdown files
    (tmp_path / "posts" / "2024-01-01-remove.md").unlink()
    (tmp_path / "projects" / "remove-proj.md").unlink()

    sync_content(session=db, content_dir=tmp_path)

    db.expire_all()
    assert _get_post(db, "keep") is not None
    assert _get_post(db, "remove") is None
    assert _get_project(db, "keep-proj") is not None
    assert _get_project(db, "remove-proj") is None
    _cleanup(db)


def test_slug_conflict_logs_warning_no_crash(db: Session, tmp_path: Path) -> None:
    _cleanup(db)
    # Two posts from different source files that produce the same slug
    _setup_post(tmp_path, "2024-01-01-conflict.md", title="Conflict", slug="same-slug")
    _setup_post(
        tmp_path, "2024-01-02-conflict.md", title="Conflict 2", slug="same-slug"
    )

    # Should not raise — first wins, second logs a warning
    sync_content(session=db, content_dir=tmp_path)

    posts = db.exec(select(Post).where(Post.slug == "same-slug")).all()
    assert len(posts) == 1
    _cleanup(db)


def test_partial_failure_does_not_abort_sync(db: Session, tmp_path: Path) -> None:
    _cleanup(db)
    _setup_post(tmp_path, "2024-01-01-good.md", title="Good Post")
    # Write an invalid file (missing title)
    _write_md(tmp_path / "posts", "2024-01-02-bad.md", "---\nslug: bad\n---\nNo title.")
    _setup_project(tmp_path, "good-proj.md", title="Good Project")

    sync_content(session=db, content_dir=tmp_path)

    assert _get_post(db, "good") is not None
    assert _get_project(db, "good-proj") is not None
    _cleanup(db)


def test_empty_directory_no_errors(db: Session, tmp_path: Path) -> None:
    _cleanup(db)
    # tmp_path exists but has no posts/projects/pages subdirs
    sync_content(session=db, content_dir=tmp_path)
    _cleanup(db)


def test_nonexistent_directory_raises_content_sync_error(
    db: Session, tmp_path: Path
) -> None:
    nonexistent = tmp_path / "does-not-exist"
    with pytest.raises(ContentSyncError):
        sync_content(session=db, content_dir=nonexistent)


def test_sync_enriches_project_with_github_metadata(
    db: Session, tmp_path: Path
) -> None:
    _cleanup(db)
    _setup_project(
        tmp_path,
        "github-proj.md",
        title="GitHub Project",
        repo_url="https://github.com/owner/repo",
    )
    mock_meta = GitHubRepoMeta(
        stars=100,
        language="Python",
        forks=10,
        last_pushed_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
    )

    with patch("app.services.project.fetch_repo_metadata", return_value=mock_meta):
        sync_content(session=db, content_dir=tmp_path)

    db.expire_all()
    project = _get_project(db, "github-proj")
    assert project is not None
    assert project.github_stars == 100
    assert project.github_language == "Python"
    assert project.github_forks == 10
    assert project.github_last_pushed_at is not None
    _cleanup(db)


def test_sync_continues_when_github_api_fails(db: Session, tmp_path: Path) -> None:
    _cleanup(db)
    _setup_project(
        tmp_path,
        "failing-github-proj.md",
        title="Failing GitHub Project",
        repo_url="https://github.com/owner/repo",
    )

    with patch("app.services.project.fetch_repo_metadata", return_value=None):
        sync_content(session=db, content_dir=tmp_path)

    db.expire_all()
    project = _get_project(db, "failing-github-proj")
    assert project is not None
    assert project.title == "Failing GitHub Project"
    assert project.github_stars is None
    _cleanup(db)
