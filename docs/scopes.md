# Scopes

9 scopes covering 100% of the codebase. Used for PR labels, commit scopes, agent focus, and modular testing.

## Usage

| Context | Format | Example |
|---------|--------|---------|
| Commits | `type(scope): description` | `feat(blog): add post list endpoint` |
| PR labels | `scope:<name>` | `scope:core` |
| GitHub labeler | `.github/labeler.yml` | auto-applied on PR |
| Pre-commit | `--scopes` in conventional-pre-commit | rejects unknown scopes |

## Scopes

| Scope | Category | Description |
|-------|----------|-------------|
| [core](scopes/core.md) | Infrastructure | App foundation: config, db, logging, middleware, observability |
| [auth](scopes/auth.md) | Infrastructure | Authentication: login, security, JWT, user management |
| [blog](scopes/blog.md) | Domain | Blog content: post and tag models, CRUD, services, routes |
| [content](scopes/content.md) | Domain | Content engine: frontmatter, renderer, loader, markdown source |
| [portfolio](scopes/portfolio.md) | Domain | Portfolio: project models, CRUD, services, about page |
| [frontend](scopes/frontend.md) | Presentation | Server-rendered UI: templates, pages, static, HTMX, Svelte islands |
| [feeds](scopes/feeds.md) | Cross-cutting | Machine discovery: RSS, llms.txt, sitemap, JSON-LD, Open Graph |
| [tests](scopes/tests.md) | Cross-cutting | Test suite, fixtures, test utilities, e2e |
| [ci](scopes/ci.md) | Cross-cutting | GitHub Actions, Docker, compose, scripts, Makefile, pre-commit |

## Path → Scope Mapping

```
# Infrastructure
backend/app/core/**  (except security.py)  → core
backend/app/main.py                        → core
backend/app/api/deps.py                    → core
backend/app/api/main.py                    → core
backend/app/backend_pre_start.py           → core
backend/app/initial_data.py                → core
backend/app/utils.py                       → core

backend/app/core/security.py               → auth
backend/app/api/routes/login.py            → auth
backend/app/api/routes/users.py            → auth
backend/app/api/routes/private.py          → auth

# Domain
backend/app/models/post.py                 → blog
backend/app/models/tag.py                  → blog
backend/app/schemas/post.py                → blog
backend/app/crud/post.py                   → blog
backend/app/services/post.py               → blog
backend/app/api/routes/posts.py            → blog

backend/app/content/**                     → content
content/**                                 → content

backend/app/models/project.py              → portfolio
backend/app/schemas/project.py             → portfolio
backend/app/crud/project.py                → portfolio
backend/app/services/project.py            → portfolio
backend/app/api/routes/projects.py         → portfolio

# Presentation
backend/app/pages/**                       → frontend
backend/app/templates/**                   → frontend
backend/app/static/**                      → frontend
islands/**                                 → frontend

# Cross-cutting
backend/app/api/routes/feeds.py            → feeds
backend/app/templates/feeds/**             → feeds

backend/tests/**                           → tests
e2e/**                                     → tests

.github/**                                 → ci
backend/Dockerfile                         → ci
backend/.dockerignore                      → ci
compose*.yml                               → ci
Makefile                                   → ci
.pre-commit-config.yaml                    → ci
backend/scripts/**                         → ci
```

Notes:
- Patterns use glob syntax (`**` = recursive, `*` = wildcard)
- If a file matches multiple scopes, apply all matching labels
- `__init__.py` files inherit the scope of their parent directory
