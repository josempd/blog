from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.crud.post import get_or_create_tag, upsert_post
from app.models.post import Post, PostTagLink, Tag
from app.schemas.post import PostUpsert, TagCreate
from tests.utils.utils import random_lower_string

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_post(
    db: Session,
    *,
    published: bool = True,
    slug: str | None = None,
    title: str | None = None,
    content_html: str = "<h1>Hello</h1>",
) -> Post:
    slug = slug or f"test-{random_lower_string()}"
    title = title or f"Post {random_lower_string()}"
    data = PostUpsert(
        title=title,
        slug=slug,
        content_markdown="# Hello",
        content_html=content_html,
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
# Module-scoped seed fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def seed_posts(client: TestClient, db: Session):  # noqa: ARG001
    tag = get_or_create_tag(session=db, data=TagCreate(name="Python", slug="python"))
    db.commit()

    post = _make_post(db, slug="published-post", title="Published Post")
    post.tags.append(tag)
    db.add(post)
    db.commit()

    _make_post(db, slug="another-post", title="Another Post", published=True)
    _make_post(db, slug="draft-post", title="Draft Post", published=False)
    _make_post(
        db,
        slug="post-with-toc",
        title="Post With ToC",
        content_html=(
            '<h2 id="intro">Introduction</h2><p>Text</p>'
            '<h3 id="details">Details</h3><p>More text</p>'
            '<h2 id="conclusion">Conclusion</h2><p>End</p>'
        ),
    )

    yield

    _cleanup(db)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_home_page(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Recent Posts" in response.text


def test_blog_list(client: TestClient) -> None:
    response = client.get("/blog")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Published Post" in response.text


def test_blog_list_excludes_drafts(client: TestClient) -> None:
    response = client.get("/blog")
    assert response.status_code == 200
    assert "Draft Post" not in response.text


def test_blog_tag_filter(client: TestClient) -> None:
    response = client.get("/blog?tag=python")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Published Post" in response.text
    assert "Another Post" not in response.text


def test_blog_tag_filter_no_match(client: TestClient) -> None:
    response = client.get("/blog?tag=nonexistent-tag")
    assert response.status_code == 200
    assert "No posts" in response.text


def test_blog_detail(client: TestClient) -> None:
    response = client.get("/blog/published-post")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Published Post" in response.text
    assert "<article" in response.text


def test_blog_detail_404(client: TestClient) -> None:
    response = client.get("/blog/nonexistent-post-slug")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "not found" in response.text.lower()


def test_blog_detail_unpublished_returns_404(client: TestClient) -> None:
    response = client.get("/blog/draft-post")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]


def test_blog_htmx_partial(client: TestClient) -> None:
    response = client.get("/blog", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "<html" not in response.text
    assert "Published Post" in response.text


def test_search_page(client: TestClient) -> None:
    response = client.get("/search?q=Published")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Published Post" in response.text


def test_search_htmx_partial(client: TestClient) -> None:
    response = client.get("/search?q=Published", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "<html" not in response.text
    assert "Published Post" in response.text


def test_search_no_results(client: TestClient) -> None:
    response = client.get("/search?q=xyznonexistent")
    assert response.status_code == 200
    assert "No results" in response.text


def test_search_empty_query(client: TestClient) -> None:
    response = client.get("/search")
    assert response.status_code == 200
    assert "Search" in response.text


def test_search_excludes_drafts(client: TestClient) -> None:
    response = client.get("/search?q=Draft")
    assert response.status_code == 200
    assert "Draft Post" not in response.text


def test_blog_detail_has_jsonld(client: TestClient) -> None:
    response = client.get("/blog/published-post")
    assert response.status_code == 200
    assert '"@type": "BlogPosting"' in response.text
    assert '"headline": "Published Post"' in response.text
    assert '"@type": "Person"' in response.text


def test_blog_detail_has_breadcrumb(client: TestClient) -> None:
    response = client.get("/blog/published-post")
    assert response.status_code == 200
    assert '"@type": "BreadcrumbList"' in response.text
    assert "/blog" in response.text


def test_blog_detail_has_canonical(client: TestClient) -> None:
    response = client.get("/blog/published-post")
    assert response.status_code == 200
    assert 'rel="canonical"' in response.text
    assert "/blog/published-post" in response.text


def test_blog_detail_markdown(client: TestClient) -> None:
    response = client.get("/blog/published-post.md")
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]
    assert "# Hello" in response.text


def test_blog_detail_markdown_404(client: TestClient) -> None:
    response = client.get("/blog/nonexistent-post.md")
    assert response.status_code == 404


def test_home_has_website_jsonld(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert '"@type": "WebSite"' in response.text
    assert '"SearchAction"' in response.text


def test_blog_detail_has_toc(client: TestClient) -> None:
    response = client.get("/blog/post-with-toc")
    assert response.status_code == 200
    assert 'id="toc-nav"' in response.text
    assert 'aria-label="Table of contents"' in response.text
    assert 'href="#intro"' in response.text
    assert 'href="#conclusion"' in response.text


def test_blog_detail_toc_sidebar_layout(client: TestClient) -> None:
    response = client.get("/blog/post-with-toc")
    assert response.status_code == 200
    assert "post-layout" in response.text
    assert "post-sidebar" in response.text


def test_blog_detail_no_toc_for_short_post(client: TestClient) -> None:
    response = client.get("/blog/published-post")
    assert response.status_code == 200
    assert "post-toc" not in response.text


def test_blog_empty_state(client: TestClient, db: Session) -> None:
    _cleanup(db)
    response = client.get("/blog")
    assert response.status_code == 200
    assert "No posts" in response.text
