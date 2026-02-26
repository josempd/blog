"""Unit tests for app.content.renderer.render_markdown."""

from app.content.renderer import TocEntry, extract_toc, render_markdown


def test_plain_text_renders_to_paragraph() -> None:
    result = render_markdown("Hello world")
    assert "<p>" in result
    assert "Hello world" in result


def test_heading_renders_with_tag() -> None:
    result = render_markdown("# My Heading")
    assert "<h1" in result
    assert "My Heading" in result


def test_heading_gets_slugified_id() -> None:
    result = render_markdown("# Hello World")
    assert 'id="hello-world"' in result


def test_heading_level_two() -> None:
    result = render_markdown("## Sub Heading")
    assert "<h2" in result
    assert 'id="sub-heading"' in result


def test_heading_with_accented_chars_gets_slugified_id() -> None:
    result = render_markdown("# Café Style")
    assert 'id="cafe-style"' in result


def test_heading_with_special_chars_gets_slugified_id() -> None:
    result = render_markdown("# Hello, World!")
    assert 'id="hello-world"' in result


def test_fenced_code_block_known_language_gets_highlighting() -> None:
    code = "```python\nprint('hello')\n```"
    result = render_markdown(code)
    assert 'class="highlight"' in result


def test_fenced_code_block_python_contains_code() -> None:
    code = "```python\nx = 1 + 2\n```"
    result = render_markdown(code)
    assert "x" in result
    assert "1" in result


def test_fenced_code_block_unknown_language_falls_back_gracefully() -> None:
    code = "```unknownlang999\nsome code here\n```"
    result = render_markdown(code)
    # Falls back to TextLexer — highlight wrapper still present
    assert "some code here" in result


def test_fenced_code_block_no_language_renders() -> None:
    code = "```\nplain code block\n```"
    result = render_markdown(code)
    assert "plain code block" in result


def test_empty_string_returns_empty_string() -> None:
    result = render_markdown("")
    assert result == ""


def test_bold_text_renders() -> None:
    result = render_markdown("**bold text**")
    assert "<strong>" in result
    assert "bold text" in result


def test_link_renders() -> None:
    result = render_markdown("[Click here](https://example.com)")
    assert "<a" in result
    assert "https://example.com" in result
    assert "Click here" in result


def test_multiple_headings_each_get_id() -> None:
    markdown = "# First Heading\n\n## Second Heading\n\n### Third Heading"
    result = render_markdown(markdown)
    assert 'id="first-heading"' in result
    assert 'id="second-heading"' in result
    assert 'id="third-heading"' in result


def test_returns_string_type() -> None:
    result = render_markdown("Some text")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# extract_toc
# ---------------------------------------------------------------------------


def test_extract_toc_from_html() -> None:
    html = render_markdown("## Introduction\n\n### Details\n\n## Conclusion")
    toc = extract_toc(html)
    assert len(toc) == 3
    assert toc[0] == TocEntry(level=2, id="introduction", text="Introduction")
    assert toc[1] == TocEntry(level=3, id="details", text="Details")
    assert toc[2] == TocEntry(level=2, id="conclusion", text="Conclusion")


def test_extract_toc_empty_html() -> None:
    toc = extract_toc("")
    assert toc == []


def test_extract_toc_no_headings() -> None:
    html = render_markdown("Just a paragraph.\n\nAnother paragraph.")
    toc = extract_toc(html)
    assert toc == []


def test_extract_toc_skips_h1() -> None:
    html = render_markdown("# Title\n\n## Section")
    toc = extract_toc(html)
    assert len(toc) == 1
    assert toc[0].level == 2
    assert toc[0].text == "Section"


def test_extract_toc_strips_inline_html() -> None:
    html = render_markdown("## Hello **World**")
    toc = extract_toc(html)
    assert len(toc) == 1
    assert toc[0].text == "Hello World"
