from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.crud.post import upsert_post
from app.schemas.post import PostUpsert


def _seed_published_posts(
    db: Session,
) -> list[tuple[str, str, datetime]]:
    """Create 2 published posts with known slugs and different dates.

    Returns [(slug, title, published_at), ...] ordered oldest first.
    """
    posts = [
        ("test-post-older", "Older Post", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("test-post-newer", "Newer Post", datetime(2024, 6, 1, tzinfo=timezone.utc)),
    ]
    for slug, title, pub_at in posts:
        upsert_post(
            session=db,
            source_path=f"posts/{slug}.md",
            data=PostUpsert(
                title=title,
                slug=slug,
                content_markdown="# Hello",
                content_html="<h1>Hello</h1>",
                published=True,
                published_at=pub_at,
            ),
        )
    db.commit()
    return posts


def test_rss_feed(client: TestClient) -> None:
    response = client.get("/feed.xml")
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]
    assert "<channel>" in response.text
    assert "<link>" in response.text


def test_sitemap(client: TestClient) -> None:
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]
    assert "<url>" in response.text
    assert "<loc>" in response.text


def test_llms_txt(client: TestClient) -> None:
    response = client.get("/llms.txt")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_llms_full_txt(client: TestClient) -> None:
    response = client.get("/llms-full.txt")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_robots_txt(client: TestClient) -> None:
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "Sitemap:" in response.text
    assert "GPTBot" in response.text
    assert "ClaudeBot" in response.text
    assert "PerplexityBot" in response.text


def test_rss_feed_valid_xml(client: TestClient) -> None:
    response = client.get("/feed.xml")
    ET.fromstring(response.content)  # Raises ParseError if invalid


def test_rss_feed_contains_post_items(client: TestClient, db: Session) -> None:
    posts = _seed_published_posts(db)
    response = client.get("/feed.xml")
    root = ET.fromstring(response.content)
    items = root.findall(".//item")
    assert len(items) >= len(posts)
    for item in items:
        assert item.find("title") is not None
        assert item.find("link") is not None
        assert item.find("guid") is not None


def test_rss_feed_ordering(client: TestClient, db: Session) -> None:
    _seed_published_posts(db)
    response = client.get("/feed.xml")
    root = ET.fromstring(response.content)
    items = root.findall(".//item")
    titles = [item.findtext("title") for item in items]
    # "Newer Post" (2024-06-01) must appear before "Older Post" (2024-01-01)
    assert "Newer Post" in titles
    assert "Older Post" in titles
    assert titles.index("Newer Post") < titles.index("Older Post")


def test_sitemap_valid_xml(client: TestClient) -> None:
    response = client.get("/sitemap.xml")
    ET.fromstring(response.content)  # Raises ParseError if invalid


def test_sitemap_contains_post_urls(client: TestClient, db: Session) -> None:
    posts = _seed_published_posts(db)
    response = client.get("/sitemap.xml")
    root = ET.fromstring(response.content)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [el.text for el in root.findall(".//sm:loc", ns)]
    for slug, _title, _pub_at in posts:
        assert any(f"/blog/{slug}" in (loc or "") for loc in locs)


def test_sitemap_contains_static_pages(client: TestClient) -> None:
    response = client.get("/sitemap.xml")
    root = ET.fromstring(response.content)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [el.text for el in root.findall(".//sm:loc", ns)]
    assert any(
        "/blog" in (loc or "") and loc is not None and loc.rstrip("/").endswith("/blog")
        for loc in locs
    )
    assert any(
        "/projects" in (loc or "")
        and loc is not None
        and loc.rstrip("/").endswith("/projects")
        for loc in locs
    )
    assert any(
        "/privacy" in (loc or "")
        and loc is not None
        and loc.rstrip("/").endswith("/privacy")
        for loc in locs
    )
