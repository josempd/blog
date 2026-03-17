# jmpd.sh blog

[![CI](https://github.com/josempd/blog/actions/workflows/ci.yml/badge.svg)](https://github.com/josempd/blog/actions/workflows/ci.yml)
[![Deploy](https://github.com/josempd/blog/actions/workflows/deploy.yml/badge.svg)](https://github.com/josempd/blog/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.14](https://img.shields.io/badge/python-3.14-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![HTMX](https://img.shields.io/badge/HTMX-3366CC.svg?logo=htmx&logoColor=white)](https://htmx.org/)
[![Svelte](https://img.shields.io/badge/Svelte_5-FF3E00.svg?logo=svelte&logoColor=white)](https://svelte.dev/)

Personal blog and portfolio — built with FastAPI, HTMX, and a Markdown content engine.

## Stack

- **Backend**: FastAPI + SQLModel + PostgreSQL + Alembic
- **Frontend**: Jinja2 templates + HTMX + Svelte 5 islands
- **Content**: Markdown files synced to DB at startup (mistune 3 + Pygments)
- **Deploy**: Docker + Traefik + GitHub Actions

## Local development

```bash
make up              # Start all services
make test            # Run backend tests with coverage
make lint            # Run ty + ruff checks
make fmt             # Auto-format with ruff
make check           # Lint + type-check islands + test (CI equivalent)
make islands-build   # Build Svelte islands
make islands-dev     # Watch mode for island development
make new-post title="My Post Title"  # Scaffold a new blog post
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
