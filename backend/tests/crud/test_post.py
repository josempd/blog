from datetime import datetime

from sqlmodel import Session

from app.crud.post import (
    get_or_create_tag,
    get_post_by_slug,
    get_posts,
    get_tags_with_counts,
    upsert_post,
)
from app.schemas.post import PostUpsert
from tests.utils.utils import random_lower_string


def _post_data(
    *,
    title: str | None = None,
    slug: str | None = None,
    content_markdown: str = "# Hello",
    content_html: str = "<h1>Hello</h1>",
    published: bool = False,
    excerpt: str | None = None,
    published_at: datetime | None = None,
) -> PostUpsert:
    return PostUpsert(
        title=title or f"Post {random_lower_string()}",
        slug=slug or f"post-{random_lower_string()}",
        content_markdown=content_markdown,
        content_html=content_html,
        published=published,
        excerpt=excerpt,
        published_at=published_at,
    )


def test_upsert_post_creates_new(db: Session) -> None:
    source = f"posts/{random_lower_string()}.md"
    data = _post_data()
    post = upsert_post(session=db, source_path=source, data=data)
    assert post.id is not None
    assert post.title == data.title
    assert post.slug == data.slug
    assert post.source_path == source
    assert post.created_at is not None
    assert post.updated_at is None


def test_upsert_post_updates_existing(db: Session) -> None:
    source = f"posts/{random_lower_string()}.md"
    data = _post_data()
    post1 = upsert_post(session=db, source_path=source, data=data)
    original_id = post1.id

    updated_data = _post_data(title="Updated Title")
    post2 = upsert_post(session=db, source_path=source, data=updated_data)
    assert post2.id == original_id
    assert post2.title == "Updated Title"
    assert post2.updated_at is not None


def test_get_post_by_slug(db: Session) -> None:
    source = f"posts/{random_lower_string()}.md"
    data = _post_data()
    upsert_post(session=db, source_path=source, data=data)

    found = get_post_by_slug(session=db, slug=data.slug)
    assert found is not None
    assert found.slug == data.slug


def test_get_post_by_slug_not_found(db: Session) -> None:
    found = get_post_by_slug(session=db, slug="nonexistent-slug")
    assert found is None


def test_get_posts_published_only(db: Session) -> None:
    slug_pub = f"pub-{random_lower_string()}"
    slug_draft = f"draft-{random_lower_string()}"
    upsert_post(
        session=db,
        source_path=f"posts/{slug_pub}.md",
        data=_post_data(slug=slug_pub, published=True),
    )
    upsert_post(
        session=db,
        source_path=f"posts/{slug_draft}.md",
        data=_post_data(slug=slug_draft, published=False),
    )

    posts, count = get_posts(session=db, published_only=True)
    slugs = [p.slug for p in posts]
    assert slug_pub in slugs
    assert slug_draft not in slugs
    assert count >= 1


def test_get_or_create_tag_creates(db: Session) -> None:
    name = f"Tag {random_lower_string()}"
    slug = f"tag-{random_lower_string()}"
    tag = get_or_create_tag(session=db, name=name, slug=slug)
    assert tag.id is not None
    assert tag.name == name
    assert tag.slug == slug


def test_get_or_create_tag_returns_existing(db: Session) -> None:
    name = f"Tag {random_lower_string()}"
    slug = f"tag-{random_lower_string()}"
    tag1 = get_or_create_tag(session=db, name=name, slug=slug)
    tag2 = get_or_create_tag(session=db, name=name, slug=slug)
    assert tag1.id == tag2.id


def test_get_tags_with_counts(db: Session) -> None:
    tag_slug = f"tag-{random_lower_string()}"
    tag = get_or_create_tag(session=db, name=f"Tag {tag_slug}", slug=tag_slug)

    post_data = _post_data(published=True)
    post = upsert_post(
        session=db,
        source_path=f"posts/{post_data.slug}.md",
        data=post_data,
    )
    post.tags.append(tag)
    db.add(post)
    db.commit()

    results = get_tags_with_counts(session=db, published_only=True)
    tag_map = {t.slug: c for t, c in results}
    assert tag_slug in tag_map
    assert tag_map[tag_slug] >= 1


def test_get_posts_filtered_by_tag(db: Session) -> None:
    tag_slug = f"filter-{random_lower_string()}"
    tag = get_or_create_tag(session=db, name=f"Filter {tag_slug}", slug=tag_slug)

    tagged_slug = f"tagged-{random_lower_string()}"
    tagged_post = upsert_post(
        session=db,
        source_path=f"posts/{tagged_slug}.md",
        data=_post_data(slug=tagged_slug, published=True),
    )
    tagged_post.tags.append(tag)
    db.add(tagged_post)
    db.commit()

    untagged_slug = f"untagged-{random_lower_string()}"
    upsert_post(
        session=db,
        source_path=f"posts/{untagged_slug}.md",
        data=_post_data(slug=untagged_slug, published=True),
    )

    posts, count = get_posts(session=db, tag_slug=tag_slug, published_only=True)
    slugs = [p.slug for p in posts]
    assert tagged_slug in slugs
    assert untagged_slug not in slugs
    assert count >= 1
