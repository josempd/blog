# scope: portfolio

Portfolio domain — project models, schemas, CRUD, services, and routes for showcasing projects and the about page.

## Key Files

```
backend/app/models/project.py       # Project model (title, slug, description, url, tech stack)
backend/app/schemas/project.py      # ProjectCreate, ProjectUpdate, ProjectPublic
backend/app/crud/project.py         # Project queries (by slug, list)
backend/app/services/project.py     # ProjectService (create, get, list, sync from content)
backend/app/api/routes/projects.py  # JSON API endpoints (/api/v1/projects)
backend/app/pages/portfolio.py      # HTML page routes (/projects, /projects/:slug)
backend/app/pages/about.py          # About page route (/about)
```

## Dependencies

- **core** — db, exceptions, deps
- **content** — loader (project markdown files), renderer

## Testing

- `backend/tests/api/routes/test_projects.py` — project API integration tests
- `backend/tests/crud/test_project.py` — project data access unit tests
- `backend/tests/services/test_project.py` — project business logic tests
