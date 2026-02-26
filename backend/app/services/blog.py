from __future__ import annotations

from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.crud.post import get_post_by_slug, get_posts, get_tags_with_counts
from app.models.post import Post, Tag


def list_published_posts(
    *, session: Session, tag_slug: str | None = None, skip: int = 0, limit: int = 20
) -> tuple[list[Post], int]:
    return get_posts(
        session=session, tag_slug=tag_slug, published_only=True, skip=skip, limit=limit
    )


def get_published_post(*, session: Session, slug: str) -> Post:
    post = get_post_by_slug(session=session, slug=slug)
    if not post or not post.published:
        raise NotFoundError("Post", slug)
    return post


def list_tags(*, session: Session) -> list[tuple[Tag, int]]:
    return get_tags_with_counts(session=session, published_only=True)
