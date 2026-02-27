"""Unit tests for services.github — parse_github_url and fetch_repo_metadata."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx

from app.services.github import fetch_repo_metadata, parse_github_url

# ---------------------------------------------------------------------------
# parse_github_url
# ---------------------------------------------------------------------------


def test_parse_github_url_standard() -> None:
    result = parse_github_url("https://github.com/owner/repo")
    assert result == ("owner", "repo")


def test_parse_github_url_trailing_slash() -> None:
    result = parse_github_url("https://github.com/owner/repo/")
    assert result == ("owner", "repo")


def test_parse_github_url_dot_git_suffix() -> None:
    result = parse_github_url("https://github.com/owner/repo.git")
    assert result == ("owner", "repo")


def test_parse_github_url_http_scheme() -> None:
    result = parse_github_url("http://github.com/owner/repo")
    assert result == ("owner", "repo")


def test_parse_github_url_non_github_url() -> None:
    result = parse_github_url("https://gitlab.com/owner/repo")
    assert result is None


def test_parse_github_url_owner_only_path() -> None:
    result = parse_github_url("https://github.com/owner")
    assert result is None


def test_parse_github_url_empty_string() -> None:
    result = parse_github_url("")
    assert result is None


def test_parse_github_url_whitespace_only() -> None:
    result = parse_github_url("   ")
    assert result is None


# ---------------------------------------------------------------------------
# fetch_repo_metadata
# ---------------------------------------------------------------------------


def _mock_response(status_code: int, json_body: dict) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_body
    return mock


def test_fetch_repo_metadata_success() -> None:
    body = {
        "stargazers_count": 42,
        "language": "Python",
        "forks_count": 5,
        "pushed_at": "2024-06-15T10:30:00Z",
    }
    with patch("app.services.github.httpx.get", return_value=_mock_response(200, body)):
        meta = fetch_repo_metadata("https://github.com/owner/repo")

    assert meta is not None
    assert meta.stars == 42
    assert meta.language == "Python"
    assert meta.forks == 5
    assert meta.last_pushed_at is not None


def test_fetch_repo_metadata_sends_auth_header() -> None:
    body = {
        "stargazers_count": 10,
        "language": "Go",
        "forks_count": 2,
        "pushed_at": "2024-01-01T00:00:00Z",
    }
    with patch(
        "app.services.github.httpx.get", return_value=_mock_response(200, body)
    ) as mock_get:
        fetch_repo_metadata("https://github.com/owner/repo", token="mytoken")

    assert mock_get.called
    call_kwargs = mock_get.call_args[1]
    assert "Authorization" in call_kwargs.get("headers", {})
    assert call_kwargs["headers"]["Authorization"] == "Bearer mytoken"


def test_fetch_repo_metadata_non_github_url_no_http_call() -> None:
    with patch("app.services.github.httpx.get") as mock_get:
        meta = fetch_repo_metadata("https://gitlab.com/x/y")

    assert meta is None
    mock_get.assert_not_called()


def test_fetch_repo_metadata_404_returns_none() -> None:
    with patch("app.services.github.httpx.get", return_value=_mock_response(404, {})):
        meta = fetch_repo_metadata("https://github.com/owner/repo")
    assert meta is None


def test_fetch_repo_metadata_timeout_returns_none() -> None:
    with patch(
        "app.services.github.httpx.get",
        side_effect=httpx.TimeoutException("timed out"),
    ):
        meta = fetch_repo_metadata("https://github.com/owner/repo")
    assert meta is None


def test_fetch_repo_metadata_rate_limit_403_returns_none() -> None:
    with patch("app.services.github.httpx.get", return_value=_mock_response(403, {})):
        meta = fetch_repo_metadata("https://github.com/owner/repo")
    assert meta is None


def test_fetch_repo_metadata_null_language() -> None:
    body = {
        "stargazers_count": 7,
        "language": None,
        "forks_count": 1,
        "pushed_at": "2024-03-01T00:00:00Z",
    }
    with patch("app.services.github.httpx.get", return_value=_mock_response(200, body)):
        meta = fetch_repo_metadata("https://github.com/owner/repo")

    assert meta is not None
    assert meta.language is None


def test_fetch_repo_metadata_missing_pushed_at() -> None:
    body = {
        "stargazers_count": 3,
        "language": "Rust",
        "forks_count": 0,
    }
    with patch("app.services.github.httpx.get", return_value=_mock_response(200, body)):
        meta = fetch_repo_metadata("https://github.com/owner/repo")

    assert meta is not None
    assert meta.last_pushed_at is None
