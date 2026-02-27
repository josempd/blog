"""GitHub service — fetch repository metadata from the GitHub API."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

import httpx
import structlog

logger = structlog.stdlib.get_logger(__name__)

_GITHUB_REPO_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$"
)


def parse_github_url(url: str) -> tuple[str, str] | None:
    """Extract (owner, repo) from a GitHub repository URL.

    Handles:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/  (trailing slash)
    - https://github.com/owner/repo.git
    - http://github.com/owner/repo

    Returns None for non-GitHub URLs, owner-only paths, or blank strings.
    """
    if not url or not url.strip():
        return None
    match = _GITHUB_REPO_RE.match(url.strip())
    if not match:
        return None
    return match.group("owner"), match.group("repo")


@dataclass
class GitHubRepoMeta:
    stars: int
    language: str | None
    forks: int
    last_pushed_at: datetime | None


def fetch_repo_metadata(repo_url: str, *, token: str = "") -> GitHubRepoMeta | None:
    """Fetch repository metadata from the GitHub API.

    Returns None if the URL is not a GitHub repo URL, or on any failure
    (non-200 status, timeout, network error). Logs warnings on failures.
    """
    parsed = parse_github_url(repo_url)
    if not parsed:
        return None

    owner, repo = parsed
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = httpx.get(api_url, headers=headers, timeout=10.0)
    except httpx.TimeoutException:
        logger.warning("github_api_timeout", repo_url=repo_url)
        return None
    except httpx.RequestError as exc:
        logger.warning("github_api_request_error", repo_url=repo_url, error=str(exc))
        return None

    if response.status_code != 200:
        logger.warning(
            "github_api_non_200",
            repo_url=repo_url,
            status_code=response.status_code,
        )
        return None

    data = response.json()

    pushed_at_raw: str | None = data.get("pushed_at")
    if pushed_at_raw:
        try:
            last_pushed_at: datetime | None = datetime.fromisoformat(
                pushed_at_raw.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            last_pushed_at = None
    else:
        last_pushed_at = None

    return GitHubRepoMeta(
        stars=data.get("stargazers_count", 0),
        language=data.get("language"),
        forks=data.get("forks_count", 0),
        last_pushed_at=last_pushed_at,
    )
