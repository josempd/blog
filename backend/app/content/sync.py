"""Content sync — bridges the loader functions to the CRUD layer.

This is the only content module with DB side effects. All other content
modules (frontmatter, renderer, loader) are pure functions.

Run as:  python -m app.content.sync
"""

from __future__ import annotations

from pathlib import Path

import structlog
from sqlmodel import Session

from app.content import slugify
from app.content.loader import (
    ParsedPost,
    ParsedProject,
    load_pages,
    load_posts,
    load_projects,
)
from app.core.config import settings
from app.core.db import engine
from app.core.logging import setup_logging
from app.crud.post import get_or_create_tag, upsert_post
from app.crud.project import upsert_project
from app.schemas.post import PostUpsert, TagCreate
from app.schemas.project import ProjectUpsert

logger = structlog.stdlib.get_logger(__name__)


def _sync_post(*, session: Session, parsed: ParsedPost) -> None:
    upsert_data = PostUpsert(
        title=parsed.title,
        slug=parsed.slug,
        excerpt=parsed.excerpt,
        content_markdown=parsed.content_markdown,
        content_html=parsed.content_html,
        published=parsed.published,
        published_at=parsed.published_at,
    )
    post = upsert_post(
        session=session, source_path=parsed.source_path, data=upsert_data
    )

    post.tags.clear()
    for name in parsed.tags:
        slug = slugify(name)
        tag = get_or_create_tag(session=session, data=TagCreate(name=name, slug=slug))
        post.tags.append(tag)

    session.add(post)
    session.commit()


def _sync_project(*, session: Session, parsed: ParsedProject) -> None:
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
    upsert_project(session=session, source_path=parsed.source_path, data=upsert_data)


def sync_content(*, session: Session, content_dir: Path) -> None:
    """Load all Markdown content and upsert posts and projects into the DB.

    Pages are parsed and logged but not persisted (no Page model yet).
    Per-file errors are logged as warnings and do not abort the sync.
    """
    posts = load_posts(content_dir)
    projects = load_projects(content_dir)
    pages = load_pages(content_dir)

    synced_posts = 0
    for parsed in posts:
        try:
            _sync_post(session=session, parsed=parsed)
            synced_posts += 1
        except Exception:
            session.rollback()
            logger.warning(
                "post_sync_failed", source_path=parsed.source_path, exc_info=True
            )

    synced_projects = 0
    for parsed in projects:
        try:
            _sync_project(session=session, parsed=parsed)
            synced_projects += 1
        except Exception:
            session.rollback()
            logger.warning(
                "project_sync_failed",
                source_path=parsed.source_path,
                exc_info=True,
            )

    logger.info(
        "content_sync_complete",
        posts=synced_posts,
        projects=synced_projects,
        pages=len(pages),
    )


def main() -> None:
    setup_logging(log_level="INFO", json_output=False)

    content_path = Path(settings.CONTENT_DIR)
    if not content_path.is_absolute():
        content_path = Path(__file__).resolve().parents[3] / content_path

    logger.info("content_sync_starting", content_dir=str(content_path))

    with Session(engine) as session:
        sync_content(session=session, content_dir=content_path)

    logger.info("content_sync_finished")


if __name__ == "__main__":
    main()
