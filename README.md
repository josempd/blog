# jmpd.dev

Personal blog and portfolio — built with FastAPI, HTMX, and a Markdown content engine.

## Stack

- **Backend**: FastAPI + SQLModel + PostgreSQL + Alembic
- **Frontend**: Jinja2 templates + HTMX + Svelte 5 islands
- **Content**: Markdown files synced to DB at startup (mistune 3 + Pygments)
- **Deploy**: Docker + Traefik + GitHub Actions

## Local development

```bash
make up        # Start all services
make test      # Run backend tests with coverage
make lint      # Run ty + ruff checks
make fmt       # Auto-format with ruff
make check     # Lint + test (CI equivalent)
```

App runs at http://localhost:8000.

## Publishing content

Add Markdown files with YAML frontmatter to the appropriate directory:

| Type | Directory |
|------|-----------|
| Blog posts | `content/posts/` |
| Projects | `content/projects/` |
| Pages | `content/pages/` |

Content is synced to the database on startup — restart the backend to pick up changes.

## License

[MIT](LICENSE)
