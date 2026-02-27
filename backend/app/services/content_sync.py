"""Content sync service — orchestrates loading Markdown and persisting to DB.

Owns transaction boundaries: commits per file so one failure doesn't abort
the entire sync. Handles orphan cleanup for deleted Markdown files.
"""

from __future__ import annotations

from pathlib import Path

import structlog
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.content.loader import load_page, load_post, load_project
from app.core.config import settings
from app.core.exceptions import ContentSyncError
from app.crud.post import delete_posts_not_in
from app.crud.project import delete_projects_not_in
from app.services.post import sync_post_from_content
from app.services.project import (
    enrich_project_github_metadata,
    sync_project_from_content,
)

logger = structlog.stdlib.get_logger(__name__)


def _md_files(directory: Path) -> list[Path]:
    """Return sorted .md files in directory, or empty list if dir doesn't exist."""
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.md"))


def sync_content(*, session: Session, content_dir: Path) -> None:
    """Load all Markdown content and sync posts/projects into the DB.

    Each file is loaded and committed independently so a single failure
    doesn't abort the sync. Orphan records (source files that no longer
    exist) are deleted.

    Raises:
        ContentSyncError: If content_dir does not exist.
    """
    if not content_dir.is_dir():
        raise ContentSyncError(f"Content directory does not exist: {content_dir}")

    synced_posts = 0
    post_source_paths: set[str] = set()
    for file_path in _md_files(content_dir / "posts"):
        try:
            parsed = load_post(file_path, content_dir)
            post_source_paths.add(parsed.source_path)
            sync_post_from_content(session=session, parsed=parsed)
            session.commit()
            synced_posts += 1
        except IntegrityError:
            session.rollback()
            logger.warning(
                "post_sync_slug_conflict",
                source_path=file_path.name,
            )
        except Exception:
            session.rollback()
            logger.warning(
                "post_sync_failed",
                source_path=file_path.name,
                exc_info=True,
            )

    synced_projects = 0
    enriched_projects = 0
    project_source_paths: set[str] = set()
    for file_path in _md_files(content_dir / "projects"):
        try:
            parsed = load_project(file_path, content_dir)
            project_source_paths.add(parsed.source_path)
            project = sync_project_from_content(session=session, parsed=parsed)
            if enrich_project_github_metadata(
                session=session,
                project=project,
                token=settings.GITHUB_TOKEN.get_secret_value(),
            ):
                enriched_projects += 1
            session.commit()
            synced_projects += 1
        except IntegrityError:
            session.rollback()
            logger.warning(
                "project_sync_slug_conflict",
                source_path=file_path.name,
            )
        except Exception:
            session.rollback()
            logger.warning(
                "project_sync_failed",
                source_path=file_path.name,
                exc_info=True,
            )

    # Orphan cleanup — remove DB records for deleted Markdown files
    deleted_posts = delete_posts_not_in(session=session, source_paths=post_source_paths)
    deleted_projects = delete_projects_not_in(
        session=session, source_paths=project_source_paths
    )
    if deleted_posts or deleted_projects:
        session.commit()

    if deleted_posts:
        logger.info("orphan_posts_deleted", count=deleted_posts)
    if deleted_projects:
        logger.info("orphan_projects_deleted", count=deleted_projects)

    pages = [load_page(f, content_dir) for f in _md_files(content_dir / "pages")]
    logger.info(
        "content_sync_complete",
        posts=synced_posts,
        projects=synced_projects,
        projects_enriched=enriched_projects,
        pages=len(pages),
    )
