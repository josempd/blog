"""Markdown renderer — mistune 3 with Pygments syntax highlighting and heading anchors."""

from __future__ import annotations

import re
from dataclasses import dataclass

import mistune
from mistune import HTMLRenderer
from pygments import highlight
from pygments.formatters import HtmlFormatter  # type: ignore[attr-defined]
from pygments.lexers import TextLexer, get_lexer_by_name  # type: ignore[attr-defined]
from pygments.util import ClassNotFound

from app.content import slugify


class _HighlightRenderer(HTMLRenderer):
    """Custom HTML renderer with syntax highlighting and heading anchors."""

    def block_code(self, code: str, info: str | None = None, **attrs: object) -> str:
        """Render a fenced code block with Pygments syntax highlighting."""
        lang = info.strip().split(None, 1)[0] if info else ""

        try:
            lexer = (
                get_lexer_by_name(lang, stripall=True)
                if lang
                else TextLexer(stripall=True)
            )
        except ClassNotFound:
            lexer = TextLexer(stripall=True)

        formatter = HtmlFormatter(nowrap=False, cssclass="highlight")
        return highlight(code, lexer, formatter)

    def heading(self, text: str, level: int, **attrs: object) -> str:
        """Render a heading with a slugified ``id`` attribute for anchor links."""
        plain = re.sub(r"<[^>]+>", "", text)
        anchor = slugify(plain)
        return f'<h{level} id="{anchor}">{text}</h{level}>\n'


_md = mistune.create_markdown(renderer=_HighlightRenderer())


def render_markdown(text: str) -> str:
    """Convert Markdown text to an HTML string.

    Uses mistune 3 with Pygments syntax highlighting on fenced code blocks
    and slugified ``id`` anchors on all headings.

    Args:
        text: Raw Markdown source.

    Returns:
        Rendered HTML string.
    """
    result = _md(text)
    return str(result) if result is not None else ""


_TOC_RE = re.compile(r'<h([2-6]) id="([^"]+)">(.*?)</h\1>')


@dataclass(slots=True)
class TocEntry:
    level: int
    id: str
    text: str


def extract_toc(html: str) -> list[TocEntry]:
    """Extract table of contents entries from rendered HTML.

    Parses h2–h6 headings with id attributes from the rendered HTML.
    h1 is excluded as it represents the post title, not a ToC entry.
    Inline HTML tags (like ``<code>``, ``<em>``) are stripped from the text.

    Args:
        html: Rendered HTML string produced by ``render_markdown``.

    Returns:
        Ordered list of ``TocEntry`` objects, one per matched heading.
    """
    entries = []
    for match in _TOC_RE.finditer(html):
        level = int(match.group(1))
        anchor = match.group(2)
        text = re.sub(r"<[^>]+>", "", match.group(3))
        entries.append(TocEntry(level=level, id=anchor, text=text))
    return entries
