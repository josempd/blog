# scope: content

Content engine — pure functions for parsing markdown frontmatter, rendering HTML, loading source files, and the markdown source directory.

## Key Files

```
backend/app/content/
  frontmatter.py   # Parse YAML between --- delimiters → (metadata, body)
  renderer.py      # mistune 3 → HTML with Pygments syntax highlighting + heading anchors
  loader.py        # Scan content/ dir, parse all .md files, return list of dicts

content/           # Markdown source files
  posts/           # Blog post .md files
  projects/        # Portfolio project .md files
  pages/           # Static page .md files (about, etc.)
```

## Dependencies

- **core** — config (CONTENT_DIR path)

## Testing

- Unit tests for each pure function (frontmatter parsing, rendering, loading)
- Test with sample .md fixtures — no DB required
- Verify Pygments highlighting, heading anchor generation, frontmatter extraction

## Notes

All content functions are pure — no database, no side effects. They accept strings/paths and return data structures. The blog and portfolio services call content functions to sync markdown to the database.
