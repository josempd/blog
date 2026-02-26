from __future__ import annotations

import pytest
from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.crud.post import get_or_create_tag, upsert_post
from app.models.post import Post, PostTagLink, Tag
from app.schemas.post import PostUpsert, TagCreate
from app.services import blog as blog_service
from tests.utils.utils import random_lower_string

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_post(
    db: Session,
    *,
    published: bool = False,
    slug: str | None = None,
    title: str | None = None,
) -> Post:
    slug = slug or f"svc-{random_lower_string()}"
    title = title or f"Service Post {random_lower_string()}"
    data = PostUpsert(
        title=title,
        slug=slug,
        content_markdown="# Hello",
        content_html="<h1>Hello</h1>",
        published=published,
    )
    post = upsert_post(session=db, source_path=f"posts/{slug}.md", data=data)
    db.commit()
    return post


def _cleanup(db: Session) -> None:
    db.exec(PostTagLink.__table__.delete())  # type: ignore[arg-type]
    db.exec(Tag.__table__.delete())  # type: ignore[arg-type]
    db.exec(Post.__table__.delete())  # type: ignore[arg-type]
    db.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_list_published_posts(db: Session) -> None:
    _cleanup(db)
    _make_post(db, published=True, slug="pub-a", title="Published A")
    _make_post(db, published=True, slug="pub-b", title="Published B")
    _make_post(db, published=False, slug="draft-c", title="Draft C")

    posts, count = blog_service.list_published_posts(session=db)

    slugs = [p.slug for p in posts]
    assert "pub-a" in slugs
    assert "pub-b" in slugs
    assert "draft-c" not in slugs
    assert count == 2
    _cleanup(db)


def test_list_published_posts_pagination(db: Session) -> None:
    _cleanup(db)
    for i in range(5):
        _make_post(db, published=True, slug=f"page-post-{i}", title=f"Page Post {i}")

    posts, count = blog_service.list_published_posts(session=db, skip=0, limit=3)
    assert len(posts) == 3
    assert count == 5
    _cleanup(db)


def test_get_published_post_found(db: Session) -> None:
    _cleanup(db)
    slug = f"found-{random_lower_string()}"
    _make_post(db, published=True, slug=slug, title="Found Post")

    post = blog_service.get_published_post(session=db, slug=slug)

    assert post.slug == slug
    assert post.title == "Found Post"
    _cleanup(db)


def test_get_published_post_not_found(db: Session) -> None:
    with pytest.raises(NotFoundError):
        blog_service.get_published_post(session=db, slug="this-slug-does-not-exist")


def test_get_published_post_unpublished(db: Session) -> None:
    _cleanup(db)
    slug = f"unpub-{random_lower_string()}"
    _make_post(db, published=False, slug=slug, title="Unpublished Post")

    with pytest.raises(NotFoundError):
        blog_service.get_published_post(session=db, slug=slug)
    _cleanup(db)


def test_list_tags(db: Session) -> None:
    _cleanup(db)
    tag_slug = f"tag-{random_lower_string()}"
    tag = get_or_create_tag(
        session=db,
        data=TagCreate(name=f"Tag {tag_slug}", slug=tag_slug),
    )
    db.commit()

    post = _make_post(db, published=True)
    post.tags.append(tag)
    db.add(post)
    db.commit()

    results = blog_service.list_tags(session=db)

    tag_map = {t.slug: count for t, count in results}
    assert tag_slug in tag_map
    assert tag_map[tag_slug] >= 1
    _cleanup(db)


def test_list_tags_excludes_unpublished_posts(db: Session) -> None:
    _cleanup(db)
    tag_slug = f"unpub-tag-{random_lower_string()}"
    tag = get_or_create_tag(
        session=db,
        data=TagCreate(name=f"UnpubTag {tag_slug}", slug=tag_slug),
    )
    db.commit()

    post = _make_post(db, published=False)
    post.tags.append(tag)
    db.add(post)
    db.commit()

    results = blog_service.list_tags(session=db)

    tag_map = {t.slug: count for t, count in results}
    assert tag_slug not in tag_map
    _cleanup(db)
