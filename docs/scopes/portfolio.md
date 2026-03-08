# scope: portfolio

Portfolio domain — project models, schemas, CRUD, services, and routes for showcasing projects and the about page.

## Key Files

```
backend/app/models/project.py       # Project model (title, slug, description, url, tech stack)
backend/app/schemas/project.py      # ProjectUpsert, ProjectPublic, ProjectDetail, ProjectsPublic
backend/app/crud/project.py         # Project queries (by slug, list)
backend/app/services/project.py     # sync_project_from_content, enrich_project_github_metadata
backend/app/services/portfolio.py   # list_projects, get_about_page
backend/app/services/github.py      # GitHub metadata enrichment
backend/app/pages/portfolio.py      # HTML page routes (/projects, /projects/:slug, /about)
```

## Dependencies

- **core** — db, exceptions, deps
- **content** — loader (project markdown files), renderer

## Testing

- `backend/tests/crud/test_project.py` — project data access unit tests
- `backend/tests/services/test_portfolio_service.py` — portfolio service tests
- `backend/tests/services/test_github.py` — GitHub enrichment tests
- `backend/tests/pages/test_portfolio.py` — portfolio page route tests
