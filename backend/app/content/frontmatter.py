"""Frontmatter parser — splits YAML front matter from Markdown body."""

from __future__ import annotations

import re
from typing import Any

import yaml

_DELIMITER = re.compile(r"^---\s*$", re.MULTILINE)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split YAML front matter from Markdown body.

    Expects front matter delimited by ``---`` lines at the start of the text.
    Returns a tuple of (metadata dict, body string). If no front matter is
    present, returns an empty dict and the full text unchanged.

    Raises:
        ValueError: If the YAML block is present but cannot be parsed.
    """
    matches = list(_DELIMITER.finditer(text))
    if len(matches) < 2:
        return {}, text

    first, second = matches[0], matches[1]
    if first.start() != 0:
        return {}, text

    yaml_block = text[first.end() : second.start()].strip()
    body = text[second.end() :].lstrip("\n")

    if not yaml_block:
        return {}, body

    try:
        metadata = yaml.safe_load(yaml_block)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML front matter: {exc}") from exc

    if not isinstance(metadata, dict):
        raise ValueError("Front matter must be a YAML mapping")

    return metadata, body
