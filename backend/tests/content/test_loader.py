"""Unit tests for app.content.loader — uses tmp_path, no DB access."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.content.loader import (
    ParsedPage,
    ParsedPost,
    ParsedProject,
    load_page,
    load_pages,
    load_post,
    load_posts,
    load_project,
    load_projects,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_md(directory: Path, filename: str, content: str) -> Path:
    """Write a markdown file to directory and return its Path."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# load_post
# ---------------------------------------------------------------------------


def test_load_post_date_slug_filename(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-03-15-my-first-post.md",
        "---\ntitle: My First Post\n---\nBody text here.",
    )
    post = load_post(path, tmp_path)
    assert isinstance(post, ParsedPost)
    assert post.title == "My First Post"
    assert post.slug == "my-first-post"
    assert post.published_at == datetime(2024, 3, 15, tzinfo=timezone.utc)
    assert post.source_path == "posts/2024-03-15-my-first-post.md"
    assert "Body text here" in post.content_markdown


def test_load_post_slug_from_frontmatter_overrides_filename(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-03-15-original-slug.md",
        "---\ntitle: Override Slug\nslug: custom-slug\n---\nContent.",
    )
    post = load_post(path, tmp_path)
    assert post.slug == "custom-slug"


def test_load_post_published_at_from_frontmatter_overrides_filename(
    tmp_path: Path,
) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-03-15-a-post.md",
        "---\ntitle: A Post\npublished_at: 2025-06-01\n---\nContent.",
    )
    post = load_post(path, tmp_path)
    assert post.published_at == datetime(2025, 6, 1, tzinfo=timezone.utc)


def test_load_post_date_field_overrides_filename(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-03-15-a-post.md",
        "---\ntitle: A Post\ndate: 2023-01-10\n---\nContent.",
    )
    post = load_post(path, tmp_path)
    assert post.published_at == datetime(2023, 1, 10, tzinfo=timezone.utc)


def test_load_post_missing_title_raises_value_error(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-03-15-no-title.md",
        "---\nslug: no-title\n---\nContent without title.",
    )
    with pytest.raises(ValueError, match="Missing required frontmatter field 'title'"):
        load_post(path, tmp_path)


def test_load_post_tags_as_yaml_list(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-01-01-tagged.md",
        "---\ntitle: Tagged Post\ntags:\n  - python\n  - fastapi\n---\nContent.",
    )
    post = load_post(path, tmp_path)
    assert post.tags == ["python", "fastapi"]


def test_load_post_tags_as_comma_separated_string(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-01-01-tagged2.md",
        "---\ntitle: Tagged Post\ntags: python, fastapi, testing\n---\nContent.",
    )
    post = load_post(path, tmp_path)
    assert post.tags == ["python", "fastapi", "testing"]


def test_load_post_no_tags_returns_empty_list(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-01-01-no-tags.md",
        "---\ntitle: No Tags\n---\nContent.",
    )
    post = load_post(path, tmp_path)
    assert post.tags == []


def test_load_post_published_defaults_to_false(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-01-01-draft.md",
        "---\ntitle: Draft Post\n---\nContent.",
    )
    post = load_post(path, tmp_path)
    assert post.published is False


def test_load_post_published_true(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-01-01-live.md",
        "---\ntitle: Live Post\npublished: true\n---\nContent.",
    )
    post = load_post(path, tmp_path)
    assert post.published is True


def test_load_post_excerpt_from_frontmatter(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-01-01-excerpt.md",
        "---\ntitle: Post With Excerpt\nexcerpt: Short summary here.\n---\nFull content.",
    )
    post = load_post(path, tmp_path)
    assert post.excerpt == "Short summary here."


def test_load_post_no_excerpt_is_none(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-01-01-no-excerpt.md",
        "---\ntitle: Post\n---\nFull content.",
    )
    post = load_post(path, tmp_path)
    assert post.excerpt is None


def test_load_post_content_html_is_rendered(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-01-01-html.md",
        "---\ntitle: HTML Post\n---\n# Heading\n\nParagraph text.",
    )
    post = load_post(path, tmp_path)
    assert "<h1" in post.content_html
    assert "<p>" in post.content_html


def test_load_post_string_date_in_frontmatter(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-01-01-string-date.md",
        '---\ntitle: String Date Post\ndate: "2024-06-15"\n---\nContent.',
    )
    post = load_post(path, tmp_path)
    assert post.published_at == datetime(2024, 6, 15, tzinfo=timezone.utc)


def test_load_post_string_datetime_in_frontmatter(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "2024-01-01-string-datetime.md",
        '---\ntitle: String Datetime Post\ndate: "2024-06-15T10:30:00"\n---\nContent.',
    )
    post = load_post(path, tmp_path)
    assert post.published_at == datetime(2024, 6, 15, 10, 30, tzinfo=timezone.utc)


def test_load_post_no_date_in_filename_published_at_none(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    path = _write_md(
        posts_dir,
        "undated-post.md",
        "---\ntitle: Undated Post\n---\nContent.",
    )
    post = load_post(path, tmp_path)
    assert post.published_at is None
    assert post.slug == "undated-post"


# ---------------------------------------------------------------------------
# load_project
# ---------------------------------------------------------------------------


def test_load_project_basic(tmp_path: Path) -> None:
    projects_dir = tmp_path / "projects"
    path = _write_md(
        projects_dir,
        "my-project.md",
        "---\ntitle: My Project\n---\nProject description.",
    )
    project = load_project(path, tmp_path)
    assert isinstance(project, ParsedProject)
    assert project.title == "My Project"
    assert project.source_path == "projects/my-project.md"


def test_load_project_slug_from_frontmatter(tmp_path: Path) -> None:
    projects_dir = tmp_path / "projects"
    path = _write_md(
        projects_dir,
        "my-project.md",
        "---\ntitle: My Project\nslug: custom-project-slug\n---\nContent.",
    )
    project = load_project(path, tmp_path)
    assert project.slug == "custom-project-slug"


def test_load_project_slug_derived_from_filename(tmp_path: Path) -> None:
    projects_dir = tmp_path / "projects"
    path = _write_md(
        projects_dir,
        "cool-project.md",
        "---\ntitle: Cool Project\n---\nContent.",
    )
    project = load_project(path, tmp_path)
    assert project.slug == "cool-project"


def test_load_project_missing_title_raises_value_error(tmp_path: Path) -> None:
    projects_dir = tmp_path / "projects"
    path = _write_md(
        projects_dir,
        "no-title.md",
        "---\nslug: no-title\n---\nContent.",
    )
    with pytest.raises(ValueError, match="Missing required frontmatter field 'title'"):
        load_project(path, tmp_path)


def test_load_project_optional_fields_defaults(tmp_path: Path) -> None:
    projects_dir = tmp_path / "projects"
    path = _write_md(
        projects_dir,
        "minimal.md",
        "---\ntitle: Minimal Project\n---\nContent.",
    )
    project = load_project(path, tmp_path)
    assert project.description is None
    assert project.url is None
    assert project.repo_url is None
    assert project.featured is False
    assert project.sort_order == 0


def test_load_project_all_optional_fields(tmp_path: Path) -> None:
    projects_dir = tmp_path / "projects"
    path = _write_md(
        projects_dir,
        "full-project.md",
        (
            "---\n"
            "title: Full Project\n"
            "description: A full project\n"
            "url: https://example.com\n"
            "repo_url: https://github.com/user/repo\n"
            "featured: true\n"
            "sort_order: 5\n"
            "---\n"
            "Content."
        ),
    )
    project = load_project(path, tmp_path)
    assert project.description == "A full project"
    assert project.url == "https://example.com"
    assert project.repo_url == "https://github.com/user/repo"
    assert project.featured is True
    assert project.sort_order == 5


# ---------------------------------------------------------------------------
# load_page
# ---------------------------------------------------------------------------


def test_load_page_basic(tmp_path: Path) -> None:
    pages_dir = tmp_path / "pages"
    path = _write_md(
        pages_dir,
        "about.md",
        "---\ntitle: About\n---\nAbout page content.",
    )
    page = load_page(path, tmp_path)
    assert isinstance(page, ParsedPage)
    assert page.title == "About"
    assert page.source_path == "pages/about.md"


def test_load_page_slug_from_frontmatter(tmp_path: Path) -> None:
    pages_dir = tmp_path / "pages"
    path = _write_md(
        pages_dir,
        "about.md",
        "---\ntitle: About Me\nslug: about-me\n---\nContent.",
    )
    page = load_page(path, tmp_path)
    assert page.slug == "about-me"


def test_load_page_slug_derived_from_filename(tmp_path: Path) -> None:
    pages_dir = tmp_path / "pages"
    path = _write_md(
        pages_dir,
        "contact-us.md",
        "---\ntitle: Contact Us\n---\nContent.",
    )
    page = load_page(path, tmp_path)
    assert page.slug == "contact-us"


def test_load_page_missing_title_raises_value_error(tmp_path: Path) -> None:
    pages_dir = tmp_path / "pages"
    path = _write_md(
        pages_dir,
        "no-title.md",
        "---\nslug: no-title\n---\nContent.",
    )
    with pytest.raises(ValueError, match="Missing required frontmatter field 'title'"):
        load_page(path, tmp_path)


def test_load_page_content_html_rendered(tmp_path: Path) -> None:
    pages_dir = tmp_path / "pages"
    path = _write_md(
        pages_dir,
        "rich.md",
        "---\ntitle: Rich Page\n---\n# Heading\n\nParagraph.",
    )
    page = load_page(path, tmp_path)
    assert "<h1" in page.content_html
    assert "<p>" in page.content_html


# ---------------------------------------------------------------------------
# load_posts (directory scanner)
# ---------------------------------------------------------------------------


def test_load_posts_returns_sorted_descending(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    _write_md(
        posts_dir,
        "2024-01-01-older.md",
        "---\ntitle: Older Post\npublished: true\n---\nContent.",
    )
    _write_md(
        posts_dir,
        "2024-06-15-newer.md",
        "---\ntitle: Newer Post\npublished: true\n---\nContent.",
    )
    posts = load_posts(tmp_path)
    assert len(posts) == 2
    assert posts[0].slug == "newer"
    assert posts[1].slug == "older"


def test_load_posts_none_published_at_sorted_last(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    _write_md(
        posts_dir,
        "2024-01-01-dated.md",
        "---\ntitle: Dated Post\n---\nContent.",
    )
    _write_md(
        posts_dir,
        "undated.md",
        "---\ntitle: Undated Post\n---\nContent.",
    )
    posts = load_posts(tmp_path)
    assert len(posts) == 2
    # Post with a date should come first; undated (None) sorted last
    assert posts[0].published_at is not None
    assert posts[1].published_at is None


def test_load_posts_missing_directory_returns_empty_list(tmp_path: Path) -> None:
    posts = load_posts(tmp_path)
    assert posts == []


def test_load_posts_empty_directory_returns_empty_list(tmp_path: Path) -> None:
    (tmp_path / "posts").mkdir()
    posts = load_posts(tmp_path)
    assert posts == []


def test_load_posts_returns_parsed_post_instances(tmp_path: Path) -> None:
    posts_dir = tmp_path / "posts"
    _write_md(
        posts_dir,
        "2024-01-01-a-post.md",
        "---\ntitle: A Post\n---\nContent.",
    )
    posts = load_posts(tmp_path)
    assert all(isinstance(p, ParsedPost) for p in posts)


# ---------------------------------------------------------------------------
# load_projects (directory scanner)
# ---------------------------------------------------------------------------


def test_load_projects_returns_all_projects(tmp_path: Path) -> None:
    projects_dir = tmp_path / "projects"
    _write_md(projects_dir, "alpha.md", "---\ntitle: Alpha\n---\nContent.")
    _write_md(projects_dir, "beta.md", "---\ntitle: Beta\n---\nContent.")
    projects = load_projects(tmp_path)
    assert len(projects) == 2


def test_load_projects_missing_directory_returns_empty_list(tmp_path: Path) -> None:
    projects = load_projects(tmp_path)
    assert projects == []


def test_load_projects_returns_parsed_project_instances(tmp_path: Path) -> None:
    projects_dir = tmp_path / "projects"
    _write_md(projects_dir, "proj.md", "---\ntitle: Proj\n---\nContent.")
    projects = load_projects(tmp_path)
    assert all(isinstance(p, ParsedProject) for p in projects)


# ---------------------------------------------------------------------------
# load_pages (directory scanner)
# ---------------------------------------------------------------------------


def test_load_pages_returns_all_pages(tmp_path: Path) -> None:
    pages_dir = tmp_path / "pages"
    _write_md(pages_dir, "about.md", "---\ntitle: About\n---\nContent.")
    _write_md(pages_dir, "contact.md", "---\ntitle: Contact\n---\nContent.")
    pages = load_pages(tmp_path)
    assert len(pages) == 2


def test_load_pages_missing_directory_returns_empty_list(tmp_path: Path) -> None:
    pages = load_pages(tmp_path)
    assert pages == []


def test_load_pages_returns_parsed_page_instances(tmp_path: Path) -> None:
    pages_dir = tmp_path / "pages"
    _write_md(pages_dir, "faq.md", "---\ntitle: FAQ\n---\nContent.")
    pages = load_pages(tmp_path)
    assert all(isinstance(p, ParsedPage) for p in pages)
