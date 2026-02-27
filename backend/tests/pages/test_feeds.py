from __future__ import annotations

from fastapi.testclient import TestClient


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
