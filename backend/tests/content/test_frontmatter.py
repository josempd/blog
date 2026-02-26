"""Unit tests for app.content.frontmatter.parse_frontmatter."""

import pytest

from app.content.frontmatter import parse_frontmatter


def test_valid_frontmatter_with_body() -> None:
    text = "---\ntitle: Hello World\nslug: hello-world\n---\n# Body content"
    meta, body = parse_frontmatter(text)
    assert meta["title"] == "Hello World"
    assert meta["slug"] == "hello-world"
    assert body.strip() == "# Body content"


def test_valid_frontmatter_multiple_fields() -> None:
    text = (
        "---\n"
        "title: My Post\n"
        "published: true\n"
        "tags:\n"
        "  - python\n"
        "  - fastapi\n"
        "---\n"
        "Post body here."
    )
    meta, body = parse_frontmatter(text)
    assert meta["title"] == "My Post"
    assert meta["published"] is True
    assert meta["tags"] == ["python", "fastapi"]
    assert body.strip() == "Post body here."


def test_no_frontmatter_returns_empty_dict_and_full_text() -> None:
    text = "# Just a heading\n\nSome paragraph text."
    meta, body = parse_frontmatter(text)
    assert meta == {}
    assert body == text


def test_frontmatter_delimiter_not_at_start_returns_empty_dict() -> None:
    text = "Some text before\n---\ntitle: Hello\n---\nBody"
    meta, body = parse_frontmatter(text)
    assert meta == {}
    assert body == text


def test_only_one_delimiter_returns_empty_dict() -> None:
    text = "---\ntitle: Hello\n"
    meta, body = parse_frontmatter(text)
    assert meta == {}
    assert body == text


def test_empty_frontmatter_block_returns_empty_dict() -> None:
    text = "---\n---\nBody after empty front matter."
    meta, body = parse_frontmatter(text)
    assert meta == {}
    assert body.strip() == "Body after empty front matter."


def test_frontmatter_without_body() -> None:
    text = "---\ntitle: No Body\nslug: no-body\n---\n"
    meta, body = parse_frontmatter(text)
    assert meta["title"] == "No Body"
    assert body == ""


def test_invalid_yaml_raises_value_error() -> None:
    text = "---\ntitle: Hello\ninvalid: :\n  - bad yaml: [\n---\nBody"
    with pytest.raises(ValueError, match="Invalid YAML front matter"):
        parse_frontmatter(text)


def test_non_dict_yaml_raises_value_error() -> None:
    text = "---\n- item1\n- item2\n---\nBody"
    with pytest.raises(ValueError, match="Front matter must be a YAML mapping"):
        parse_frontmatter(text)


def test_scalar_yaml_raises_value_error() -> None:
    text = "---\njust a string\n---\nBody"
    with pytest.raises(ValueError, match="Front matter must be a YAML mapping"):
        parse_frontmatter(text)


def test_body_leading_newlines_stripped() -> None:
    text = "---\ntitle: Hello\n---\n\n\nBody starts here."
    meta, body = parse_frontmatter(text)
    assert body == "Body starts here."


def test_empty_string_returns_empty_dict() -> None:
    meta, body = parse_frontmatter("")
    assert meta == {}
    assert body == ""


def test_frontmatter_date_field_parsed() -> None:
    text = "---\ntitle: Post\ndate: 2024-06-15\n---\nContent"
    meta, body = parse_frontmatter(text)
    import datetime

    assert meta["date"] == datetime.date(2024, 6, 15)
    assert body.strip() == "Content"
