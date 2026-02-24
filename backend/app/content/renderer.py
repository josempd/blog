"""Markdown renderer — mistune 3 with Pygments syntax highlighting and heading anchors."""

from __future__ import annotations

import re

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
