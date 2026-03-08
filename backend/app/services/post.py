"""Post service — business logic for post sync and tag management."""

from __future__ import annotations

from sqlmodel import Session

from app.content import slugify
from app.content.loader import ParsedPost
from app.crud.post import reconcile_post_tags, upsert_post
from app.schemas.post import PostUpsert, TagCreate


def sync_post_from_content(*, session: Session, parsed: ParsedPost) -> None:
    """Upsert a post from parsed Markdown content and reconcile its tags.

    Does NOT commit — the caller owns the transaction boundary.
    """
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

    tag_creates = [TagCreate(name=name, slug=slugify(name)) for name in parsed.tags]
    reconcile_post_tags(session=session, post=post, tag_creates=tag_creates)
