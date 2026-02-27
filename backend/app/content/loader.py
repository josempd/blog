"""Content loader — pure functions to scan and parse Markdown content files.

No DB access. Returns dataclasses that sync.py bridges into CRUD calls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

from app.content import slugify
from app.content.frontmatter import parse_frontmatter
from app.content.renderer import TocEntry, extract_toc, render_markdown

# Matches filenames like 2024-01-15-my-post-slug.md
_DATE_SLUG_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")


def _to_utc_datetime(value: str | date | datetime) -> datetime:
    """Coerce a date, datetime, or ISO-format string into an aware UTC datetime."""
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def _parse_tags(raw: Any) -> list[str]:
    """Accept tags as a YAML list or a comma-separated string."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(t).strip() for t in raw if str(t).strip()]
    return [t.strip() for t in str(raw).split(",") if t.strip()]


def _relative_source(file_path: Path, content_dir: Path) -> str:
    """Return a POSIX path relative to content_dir."""
    return file_path.relative_to(content_dir).as_posix()


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class ParsedPost:
    source_path: str
    title: str
    slug: str
    excerpt: str | None
    content_markdown: str
    content_html: str
    published: bool
    published_at: datetime | None
    tags: list[str]
    toc: list[TocEntry]


@dataclass(slots=True)
class ParsedProject:
    source_path: str
    title: str
    slug: str
    description: str | None
    content_markdown: str
    content_html: str
    url: str | None
    repo_url: str | None
    featured: bool
    sort_order: int


@dataclass(slots=True)
class ParsedPage:
    source_path: str
    title: str
    slug: str
    content_markdown: str
    content_html: str
    frontmatter: dict[str, Any]


# ---------------------------------------------------------------------------
# Single-file loaders
# ---------------------------------------------------------------------------


def load_post(file_path: Path, content_dir: Path) -> ParsedPost:
    """Parse a single post Markdown file.

    Slug and date are derived from the ``YYYY-MM-DD-slug.md`` filename.
    Frontmatter fields override filename-derived values when present.

    Args:
        file_path: Absolute path to the ``.md`` file.
        content_dir: Root content directory (used to compute ``source_path``).

    Raises:
        ValueError: If ``title`` is missing from frontmatter.
    """
    text = file_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    if "title" not in meta:
        raise ValueError(f"Missing required frontmatter field 'title' in {file_path}")

    stem = file_path.stem
    date_match = _DATE_SLUG_RE.match(stem)
    filename_slug = date_match.group(2) if date_match else stem
    filename_date_str = date_match.group(1) if date_match else None

    slug = str(meta.get("slug", filename_slug))

    # Resolve published_at: frontmatter > filename date
    published_at: datetime | None = None
    if "published_at" in meta:
        published_at = _to_utc_datetime(meta["published_at"])
    elif "date" in meta:
        published_at = _to_utc_datetime(meta["date"])
    elif filename_date_str:
        published_at = _to_utc_datetime(date.fromisoformat(filename_date_str))

    html = render_markdown(body)
    return ParsedPost(
        source_path=_relative_source(file_path, content_dir),
        title=str(meta["title"]),
        slug=slug,
        excerpt=str(meta["excerpt"]) if "excerpt" in meta else None,
        content_markdown=body,
        content_html=html,
        published=bool(meta.get("published", False)),
        published_at=published_at,
        tags=_parse_tags(meta.get("tags")),
        toc=extract_toc(html),
    )


def load_project(file_path: Path, content_dir: Path) -> ParsedProject:
    """Parse a single project Markdown file.

    Args:
        file_path: Absolute path to the ``.md`` file.
        content_dir: Root content directory (used to compute ``source_path``).

    Raises:
        ValueError: If ``title`` is missing from frontmatter.
    """
    text = file_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    if "title" not in meta:
        raise ValueError(f"Missing required frontmatter field 'title' in {file_path}")

    slug = str(meta.get("slug", slugify(file_path.stem)))

    return ParsedProject(
        source_path=_relative_source(file_path, content_dir),
        title=str(meta["title"]),
        slug=slug,
        description=str(meta["description"]) if "description" in meta else None,
        content_markdown=body,
        content_html=render_markdown(body),
        url=str(meta["url"]) if "url" in meta else None,
        repo_url=str(meta["repo_url"]) if "repo_url" in meta else None,
        featured=bool(meta.get("featured", False)),
        sort_order=int(meta.get("sort_order", 0)),
    )


def load_page(file_path: Path, content_dir: Path) -> ParsedPage:
    """Parse a single static page Markdown file.

    Args:
        file_path: Absolute path to the ``.md`` file.
        content_dir: Root content directory (used to compute ``source_path``).

    Raises:
        ValueError: If ``title`` is missing from frontmatter.
    """
    text = file_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    if "title" not in meta:
        raise ValueError(f"Missing required frontmatter field 'title' in {file_path}")

    slug = str(meta.get("slug", slugify(file_path.stem)))

    return ParsedPage(
        source_path=_relative_source(file_path, content_dir),
        title=str(meta["title"]),
        slug=slug,
        content_markdown=body,
        content_html=render_markdown(body),
        frontmatter=meta,
    )


# ---------------------------------------------------------------------------
# Directory scanners
# ---------------------------------------------------------------------------


def load_posts(content_dir: Path) -> list[ParsedPost]:
    """Scan ``<content_dir>/posts/*.md`` and return posts sorted by ``published_at`` descending.

    Posts with ``published_at=None`` are sorted last. Returns an empty list if
    the directory does not exist.
    """
    posts_dir = content_dir / "posts"
    if not posts_dir.is_dir():
        return []
    posts = [load_post(f, content_dir) for f in sorted(posts_dir.glob("*.md"))]
    _min_dt = datetime.min.replace(tzinfo=timezone.utc)
    return sorted(posts, key=lambda p: p.published_at or _min_dt, reverse=True)


def load_projects(content_dir: Path) -> list[ParsedProject]:
    """Scan ``<content_dir>/projects/*.md`` and return all parsed projects.

    Returns an empty list if the directory does not exist.
    """
    projects_dir = content_dir / "projects"
    if not projects_dir.is_dir():
        return []
    return [load_project(f, content_dir) for f in sorted(projects_dir.glob("*.md"))]


def load_pages(content_dir: Path) -> list[ParsedPage]:
    """Scan ``<content_dir>/pages/*.md`` and return all parsed pages.

    Returns an empty list if the directory does not exist.
    """
    pages_dir = content_dir / "pages"
    if not pages_dir.is_dir():
        return []
    return [load_page(f, content_dir) for f in sorted(pages_dir.glob("*.md"))]
