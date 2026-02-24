"""Content engine — pure functions for Markdown processing and content loading."""

import re
import unicodedata


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug.

    Lowercases, strips accents (NFKD), replaces non-alphanumeric characters
    with hyphens, collapses consecutive hyphens, and strips leading/trailing
    hyphens.
    """
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_text.lower()
    hyphenated = re.sub(r"[^a-z0-9]+", "-", lowered)
    return hyphenated.strip("-")
