# jmpd blog

Personal blog + portfolio built on [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template).

## Stack

- **Backend**: FastAPI + SQLModel + PostgreSQL + Alembic (Python 3.10, uv)
- **Frontend**: Jinja2 templates + HTMX (vendored) + Svelte 5 islands (Vite)
- **Content**: Markdown in `content/` → synced to DB at startup (mistune 3 + Pygments)
- **Deploy**: Docker + Traefik + GitHub Actions

## Architecture

Layered backend with strict separation of concerns:

```
Routes (thin HTTP handlers)
  → Services (business logic, orchestration)
    → CRUD (data access, queries)
      → Models (SQLModel table classes)
      → Schemas (Pydantic v2 request/response)
```

- **Routes** receive requests, call services, return responses. No logic.
- **Services** orchestrate business rules, call CRUD, raise domain exceptions.
- **CRUD** executes queries and mutations. No business logic, no HTTP concepts.
- **Models** define DB tables via SQLModel. **Schemas** define API shapes via Pydantic v2.
- **Content** modules (frontmatter, renderer, loader) are pure functions — no DB, no side effects.

## Scopes

9 scopes with 100% codebase coverage — see [docs/scopes.md](docs/scopes.md) for full definitions and path mappings.

| Category | Scopes |
|----------|--------|
| Infrastructure | `core`, `auth` |
| Domain | `blog`, `content`, `portfolio` |
| Presentation | `frontend` |
| Cross-cutting | `feeds`, `tests`, `ci` |

## Project Structure

```
backend/
  app/
    api/              # JSON API (/api/v1/*)
      deps.py         # SessionDep, CurrentUser, TokenDep, service deps
      routes/         # Thin handlers — one file per domain
    pages/            # HTML pages (/*) [Phase 3]
      deps.py         # Jinja2Templates + global context
    models/           # SQLModel table classes — one file per domain
    schemas/          # Pydantic v2 request/response — one file per domain
    crud/             # Data access functions — one file per domain
    services/         # Business logic — one file per domain
    content/          # Markdown engine — pure functions [Phase 2]
      frontmatter.py, renderer.py, loader.py
    core/             # config.py (Settings), db.py, security.py, exceptions.py
    templates/        # Jinja2: base.html, pages/, partials/, feeds/, errors/ [Phase 3]
    static/           # css/, js/htmx.min.js, dist/islands/ [Phase 3-4]
    main.py           # FastAPI app, router mounts
    alembic/          # Migrations
  tests/
    api/routes/       # Integration tests (TestClient)
    crud/             # Unit tests (direct Session)
    services/         # Service tests
    utils/            # Test helpers (NOT test files)
  scripts/            # prestart.sh, test.sh, lint.sh, format.sh
content/              # Markdown source: posts/, projects/, pages/ [Phase 2]
islands/              # Svelte 5 components + Vite build [Phase 4]
e2e/                  # Playwright frontend tests
```

Current phase: see [PLAN.md](PLAN.md)

## Conventions

### Python

- **Layered architecture** — routes → services → CRUD → models/schemas
- **Dependency injection** — services injected via FastAPI `Depends`, defined in `api/deps.py`
- **Domain exceptions** — services raise `PostNotFound`, `SlugConflict`, etc. Routes map to HTTP codes.
- **One file per domain** — `models/post.py`, `schemas/post.py`, `crud/post.py`, `services/post.py`
- **File size** — target ~500 LOC per file (400–600). Split when a file grows beyond this.
- **No dead code** — remove unused imports, functions, and variables. No commented-out code.
- **No code duplication** — extract shared logic into helpers or base classes.
- **Type unions**: `X | None`, never `Optional[X]`. No `Any` return types.
- **UUIDs** for all primary keys, `created_at` with `DateTime(timezone=True)`
- **Pure functions** where possible — content engine, utilities, helpers
- **Config**: add settings to `Settings` class, read from `.env`

### Commits

- Format: `type(scope): description` — max 100 chars, lowercase, no period
- Types: feat, fix, docs, chore, refactor, test, style
- Scopes: core, auth, blog, content, portfolio, frontend, feeds, tests, ci (see [docs/scopes.md](docs/scopes.md))
- No co-author footer

### Frontend

- Progressive enhancement — real `href` on all links, HTMX enhances
- Vendored assets only — no CDN links
- Semantic HTML — `<article>`, `<time datetime>`, `<nav aria-label>`, heading hierarchy
- Single `style.css` — system fonts, 60–70ch prose width
- Spacing scale — only use defined steps via CSS custom properties (`--space-1` through `--space-7`), no arbitrary values
- Type ramp — consistent font sizes via CSS custom properties (`--text-sm` through `--text-3xl`), no ad-hoc sizes
- Disciplined color palette — neutrals + one accent, WCAG AA contrast minimum
- Consistent component language — shared radii, shadows, padding across all partials
- HTMX loading states — `hx-indicator` on every async interaction
- No decorative effects — no gradients, sparkles, animations-for-show
- Visible focus styles — every interactive element has outline/ring on focus, never bare `outline: none`
- Portfolio audience — digestible by both developers and non-technical stakeholders

## Agent Delegation

Specialized agents live in `.claude/agents/`. **Always delegate implementation work to the appropriate agent** — the orchestrator coordinates and reviews, agents write code.

| Agent | When to use | Model |
|-------|-------------|-------|
| `backend` | Python backend: routes, services, CRUD, models, schemas, content engine, migrations | sonnet |
| `frontend` | Templates, CSS, HTMX interactions, Svelte islands, static files | sonnet |
| `test-backend` | pytest tests for routes, CRUD, services, content, feeds | sonnet |
| `test-frontend` | Playwright e2e tests for pages, HTMX, accessibility | sonnet |
| `feature-spec` | Challenge feature proposals before coding — read-only, Socratic questioning | opus |
| `review` | Code review after changes — enforce architecture and conventions, read-only | opus |
| `devops` | Docker, compose, CI/CD, Traefik, deployment config | sonnet |

### Rules

- **Parallelize independent agents.** Launch `frontend` + `backend` simultaneously when their files don't overlap. Launch `test-backend` after implementation agents complete.
- **Give agents the plan, not breadcrumbs.** Include full context: existing code signatures, model fields, CRUD function names, test patterns. Agents start fresh — they don't see the conversation.
- **Run `review` proactively** after code changes, before committing. Don't skip this.
- **Run `feature-spec` before implementing** non-trivial features. Get questions answered before writing code.
- **Never do an agent's job yourself.** If the task matches an agent description, delegate. The orchestrator's job is to coordinate, fix integration issues, run `make lint` / `make test`, and commit.
- **Fix integration issues directly.** After agents complete, the orchestrator handles cross-cutting fixes (import sorting, fixture names, path resolution) — don't re-launch an agent for a one-line fix.

## Do NOT

- Change auth behavior (JWT algorithm, token format, password hashing, OAuth2 flow)
- Modify `core/security.py` or `api/deps.py` auth dependencies without explicit approval
- Put business logic in route handlers — that belongs in services
- Put HTTP concepts (status codes, HTTPException) in services or CRUD
- Use CDN for JS/CSS — vendor everything
- Skip Alembic migrations when changing models
- Use `Optional[X]` — use `X | None`
- Use `Any` as a return type — be explicit
- Leave dead code, unused imports, or commented-out blocks
- Add debug mode or dev flags in production config
- Use arbitrary spacing or font-size values — use the defined scale tokens
- Mix visual styles between components — radii, shadows, padding must be consistent
- Add decorative animations or gradient effects

## Running Locally

```bash
# Lifecycle
make up              # Start all services (detached)
make down            # Stop all services
make build           # Rebuild backend image
make restart         # Restart backend (keeps DB running)
make logs            # Tail backend logs
make logs-all        # Tail all service logs
make ps              # Show running services

# Development
make shell           # Shell into backend container
make dbshell         # psql into the database

# Code quality
make lint            # Run ty + ruff checks
make fmt             # Auto-format with ruff
make check           # Lint + test (CI equivalent)

# Testing
make test            # Run pytest with coverage
make test-fast       # Run pytest without coverage (faster)

# Database
make migrate m="description"   # Generate alembic migration
make upgrade                   # Apply all pending migrations
make downgrade                 # Rollback one migration
make db-reset                  # Drop and recreate database (destructive!)

# Dependencies
make lock            # Regenerate uv.lock
make install         # Install backend deps locally (for IDE support)
make setup           # Full dev setup (deps + pre-commit hooks)
```

- **App**: http://localhost:8000
- **API docs**: http://localhost:8000/docs
- **Adminer**: http://localhost:8080
- **Mailcatcher**: http://localhost:1080
