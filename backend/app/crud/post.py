from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, func, select

from app.models.base import get_datetime_utc
from app.models.post import Post, PostTagLink, Tag
from app.schemas.post import PostUpsert, TagCreate


def get_post_by_slug(*, session: Session, slug: str) -> Post | None:
    eager = selectinload(Post.tags)  # type: ignore[arg-type]
    statement = select(Post).options(eager).where(Post.slug == slug)
    return session.exec(statement).first()


def get_posts(
    *,
    session: Session,
    tag_slug: str | None = None,
    published_only: bool = True,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Post], int]:
    eager = selectinload(Post.tags)  # type: ignore[arg-type]
    base = select(Post).options(eager)
    count_base = select(func.count()).select_from(Post)

    if published_only:
        base = base.where(Post.published == True)  # noqa: E712
        count_base = count_base.where(Post.published == True)  # noqa: E712

    if tag_slug:
        base = base.join(PostTagLink).join(Tag).where(Tag.slug == tag_slug)
        count_base = count_base.join(PostTagLink).join(Tag).where(Tag.slug == tag_slug)

    count = session.exec(count_base).one()
    posts = session.exec(
        base.order_by(col(Post.published_at).desc()).offset(skip).limit(limit)
    ).all()
    return list(posts), count


def upsert_post(*, session: Session, source_path: str, data: PostUpsert) -> Post:
    statement = select(Post).where(Post.source_path == source_path)
    existing = session.exec(statement).first()
    if existing:
        existing.sqlmodel_update(data.model_dump())
        existing.updated_at = get_datetime_utc()
        session.add(existing)
        session.flush()
        session.refresh(existing)
        return existing
    post = Post(source_path=source_path, **data.model_dump())
    session.add(post)
    session.flush()
    session.refresh(post)
    return post


def get_or_create_tag(*, session: Session, data: TagCreate) -> Tag:
    statement = select(Tag).where(Tag.slug == data.slug)
    existing = session.exec(statement).first()
    if existing:
        return existing
    tag = Tag(name=data.name, slug=data.slug)
    session.add(tag)
    session.flush()
    session.refresh(tag)
    return tag


def get_tags_with_counts(
    *, session: Session, published_only: bool = True
) -> list[tuple[Tag, int]]:
    statement = (
        select(Tag, func.count(PostTagLink.post_id).label("post_count"))
        .join(PostTagLink, Tag.id == PostTagLink.tag_id)
        .join(Post, Post.id == PostTagLink.post_id)
    )
    if published_only:
        statement = statement.where(Post.published == True)  # noqa: E712
    statement = statement.group_by(Tag.id).having(func.count(PostTagLink.post_id) > 0)
    results = session.exec(statement).all()
    return list(results)
