# Personal Blog + Portfolio: LLM-Friendly, GitHub-Connected

## Context

Build a personal blog and portfolio site where you can post findings, research, and experiences. Must be LLM-friendly (llms.txt, JSON-LD, semantic HTML), GitHub-connected, and serve as an about-me/portfolio page. Uses the **full-stack-fastapi-template** as a foundation to get auth, Docker, migrations, and CI/CD for free.

## Stack

- **Base**: [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) (v0.10.0)
- **Backend**: FastAPI + SQLModel + PostgreSQL + Alembic
- **Frontend**: Jinja2 templates + HTMX + Svelte 5 islands
- **Content**: Markdown files in git repo (synced to DB at startup)
- **Rendering**: mistune + Pygments (syntax highlighting)
- **Build**: Vite + vite-plugin-svelte for islands
- **Deploy**: Docker (multi-stage) + Traefik (from template)

---

## Phase 0: Bootstrap ✅

Clone template, strip React frontend, verify backend boots.

1. ~~Clone `fastapi/full-stack-fastapi-template` into `/Users/jmpd/code/blog/`~~ — Cloned to temp dir, copied needed files (backend/, compose files, root pyproject.toml, uv.lock)
2. ~~Delete `frontend/` directory~~ — Never copied it in the first place
3. ~~Remove `frontend` + `playwright` services from `compose.yml` and `compose.override.yml`~~ — Done
4. ~~Update `.env` with project settings (SITE_TITLE, SITE_AUTHOR, GITHUB_USERNAME, etc.)~~ — Done
5. Verify: `docker compose up db backend` -> `/docs` works — **TODO: not yet verified**

**Findings**:
- Template uses a **uv workspace** — root `pyproject.toml` defines `[tool.uv.workspace]` with `members = ["backend"]`, and `uv.lock` lives at root. Both needed for Dockerfile `uv sync`.
- Dockerfile references `--mount=type=bind,source=uv.lock` and `--mount=type=bind,source=pyproject.toml` at the **build context root**, so root pyproject.toml + uv.lock are required.
- Backend Traefik routing changed from `Host(`api.${DOMAIN}`)` to `Host(`${DOMAIN}`)` since backend now serves HTML directly (no separate frontend).
- `httpx` is **already a dependency** in the template's pyproject.toml — no need to add it in Phase 6.
- `jinja2` is **already a dependency** — no need to add it for Phase 3.
- `compose.traefik.yml` was also copied (needed for production Traefik setup).

**Modify**: `compose.yml`, `compose.override.yml`, `.env`
~~**Delete**: `frontend/`~~

---

## Phase 1: Models + Migrations

Extend SQLModel models for blog content. Keep User model, remove Item.

**New models in `/backend/app/models.py`**:
- `Post` (title, slug, excerpt, content_markdown, content_html, published, published_at, source_path, author_id FK)
- `Tag` (name, slug) with many-to-many via `PostTagLink`
- `Project` (title, slug, description, content_markdown, content_html, url, repo_url, featured, sort_order)

**New CRUD in `/backend/app/crud.py`**:
- `get_post_by_slug`, `get_posts` (with tag filter + pagination), `upsert_post`
- `get_or_create_tag`, `get_tags_with_counts`
- `get_projects`, `upsert_project`

**Delete**: `/backend/app/api/routes/items.py`
**Run**: `alembic revision --autogenerate` + `alembic upgrade head`

---

## Phase 2: Markdown Content Engine

Read markdown files from `content/` dir, parse frontmatter, render HTML, sync to DB.

**Content dir structure**:
```
content/
  posts/2026-02-17-hello-world.md    (YAML frontmatter: title, slug, date, tags, excerpt, published)
  projects/my-project.md
  pages/about.md
```

**New files**:
- `/backend/app/content/frontmatter.py` -- parse YAML frontmatter between `---` delimiters
- `/backend/app/content/renderer.py` -- mistune with Pygments syntax highlighting + heading IDs for anchor links
- `/backend/app/content/loader.py` -- scan content dir, parse all markdown files, return dicts
- `/backend/scripts/sync-content.py` -- upsert all content into DB (runs in `prestart.sh`)

**New deps** in `/backend/pyproject.toml`: `mistune>=3.0`, `pygments>=2.17`, `pyyaml>=6.0`

**Sample content**: at least 1 post, 1 project, 1 about page

---

## Phase 3: Jinja2 Templates + HTMX + Static Files

Server-rendered frontend with progressive enhancement.

### Architecture: Dual Router Pattern
- `/api/v1/*` -- JSON API (existing template routes + new post/project endpoints)
- `/*` -- HTML pages (new page router at root)

Both share the same models, CRUD layer, and DB session.

**Modify `/backend/app/main.py`**: add `pages_router` + `StaticFiles` mount

**New files**:
- `/backend/app/pages/router.py` -- aggregates all page routers
- `/backend/app/pages/blog.py` -- `GET /` (home), `GET /blog` (list), `GET /blog/{slug}` (detail)
- `/backend/app/pages/portfolio.py` -- `GET /projects`, `GET /about`
- `/backend/app/pages/feeds.py` -- `GET /feed.xml`, `GET /llms.txt`, `GET /llms-full.txt`, `GET /sitemap.xml`
- `/backend/app/pages/deps.py` -- Jinja2Templates setup with global context

**Templates** (`/backend/app/templates/`):
- `base.html` -- layout with meta tags, Open Graph, RSS autodiscovery, HTMX script, island script blocks
- `partials/` -- header, footer, nav, post_card, tag_list, pagination
- `pages/` -- home, blog_list, blog_post, projects, about, tag
- `feeds/` -- rss.xml, llms.txt, llms_full.txt
- `errors/` -- 404, 500

**Static files** (`/backend/app/static/`):
- `css/` -- split by concern: `tokens.css`, `base.css`, `components.css`, `syntax.css`, `utilities.css`
- `js/htmx.min.js` -- vendored (not CDN)

**HTMX usage**:
- Tag filtering: `hx-get="/blog?tag=python"` + `hx-target="#post-list"` + `hx-push-url`
- Pagination: "Load more" with `hx-swap="afterend"`
- All links are real URLs (works without JS)

**Modify**: `/backend/app/core/config.py` (add SITE_TITLE, SITE_AUTHOR, CONTENT_DIR, GITHUB_USERNAME)

---

## Phase 4: Svelte Islands Build Pipeline

Standalone Svelte 5 components compiled by Vite, mounted into Jinja2 templates.

**Structure**:
```
islands/
  package.json
  vite.config.js
  src/islands/
    ThemeToggle.js + ThemeToggle.svelte
    SearchDialog.js + SearchDialog.svelte
    TableOfContents.js + TableOfContents.svelte
    GitHubRepos.js + GitHubRepos.svelte
```

Each `.js` file imports the Svelte component and mounts it to a DOM element:
```js
import { mount } from "svelte";
import Component from "./Component.svelte";
const el = document.getElementById("component-island");
if (el) mount(Component, { target: el, props: { ...el.dataset } });
```

**Vite config**: auto-discovers `.js` entry points, outputs standalone files to `/backend/app/static/dist/islands/[name].js`

**Dev workflow**: `cd islands && npm run dev` (watch mode) alongside Docker backend

**In templates**: `<div id="theme-toggle-island"></div>` + `<script type="module" src="/static/dist/islands/ThemeToggle.js"></script>`

---

## Phase 5: LLM-Friendly Features

- **`/llms.txt`**: H1 title, blockquote summary, H2 sections with links to posts/projects (per llmstxt.org spec)
- **`/llms-full.txt`**: Full raw markdown of all published posts (more useful for LLMs than HTML)
- **`/feed.xml`**: RSS 2.0 feed
- **`/sitemap.xml`**: XML sitemap
- **JSON-LD**: `BlogPosting` schema on post pages, `Person` schema on about page
- **Semantic HTML**: `<article>`, `<section>`, `<time datetime>`, `<nav aria-label>`, heading hierarchy
- **Open Graph** meta tags on all pages

---

## Phase 6: Portfolio + GitHub Integration

- Projects page rendering from DB (synced from `content/projects/*.md`)
- About page rendered from `content/pages/about.md`
- GitHub repos API proxy: `/api/v1/github/repos` (uses `httpx` + optional `GITHUB_TOKEN`)
- `GitHubRepos` Svelte island fetches from proxy and renders repo cards
- Person JSON-LD schema on about page

~~**New dep**: `httpx` (for GitHub API calls)~~ — already in template deps

---

## Phase 7: Testing

Using existing pytest setup from template:
- `test_content_loader.py` -- frontmatter parsing, markdown rendering, file loading
- `test_blog.py` -- page routes (200s, 404s, HTMX partials)
- `test_feeds.py` -- RSS, llms.txt, llms-full.txt, sitemap
- `test_portfolio.py` -- projects page, about page

---

## Phase 8: Deployment Polish

- **Multi-stage Dockerfile**: Stage 1 builds Svelte islands (Node), Stage 2 runs backend (Python), copies island output
- **Content volume mount**: `./content:/app/content:ro` in compose.yml (content changes without rebuild)
- **CI/CD**: Add islands build step to `.github/workflows/ci.yml`
- **Prestart**: `sync-content.py` runs on every deploy, upserting markdown -> DB

---

## Phase Dependencies

```
Phase 0 (Bootstrap)
  -> Phase 1 (Models)
     -> Phase 2 (Content Engine)
        -> Phase 3 (Templates + HTMX)
           -> Phase 4 (Svelte Islands)  \
           -> Phase 5 (LLM Features)     > can run in parallel
           -> Phase 6 (Portfolio)        /
              -> Phase 7 (Testing)
                 -> Phase 8 (Deployment)
```

---

## Verification

After each phase, verify:
1. `docker compose up db backend` -- app starts without errors
2. `http://localhost:8000/docs` -- API docs work (Phases 0-1)
3. `http://localhost:8000/` -- home page renders with posts (Phase 3)
4. `http://localhost:8000/blog/hello-world` -- post renders with syntax highlighting (Phase 3)
5. View source -- semantic HTML, JSON-LD present (Phase 5)
6. `curl http://localhost:8000/llms.txt` -- valid llms.txt format (Phase 5)
7. `curl http://localhost:8000/feed.xml` -- valid RSS (Phase 5)
8. Svelte islands interactive in browser (Phase 4)
9. `pytest` -- all tests pass (Phase 7)
10. `docker compose up` -- full stack boots in production mode (Phase 8)
