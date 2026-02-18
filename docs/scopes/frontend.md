# scope: frontend

Server-rendered UI — Jinja2 templates, page routes, static assets, HTMX interactions, and Svelte 5 islands.

## Key Files

```
backend/app/pages/
  deps.py          # Jinja2Templates instance + global template context
  blog.py          # Blog page routes (list, detail)
  portfolio.py     # Portfolio page routes
  about.py         # About page

backend/app/templates/
  base.html        # Layout: head, nav, main, footer
  pages/           # Full-page templates (blog_list, blog_post, projects, about)
  partials/        # HTMX partial responses (post card, project card)
  errors/          # Error pages (404, 500)

backend/app/static/
  css/style.css    # Single stylesheet — system fonts, 60-70ch prose width
  js/htmx.min.js   # Vendored HTMX
  dist/islands/    # Vite-built Svelte components

islands/           # Svelte 5 source components + Vite config
```

## Dependencies

- **core** — config, deps
- **blog** — PostService (via page routes)
- **portfolio** — ProjectService (via page routes)

## Testing

- `e2e/` — Playwright end-to-end tests (semantic HTML, HTMX, accessibility)
- Template rendering tests with TestClient (status codes, content assertions)

## Notes

Progressive enhancement — all links have real `href`, HTMX enhances navigation. No CDN — all JS/CSS is vendored. Semantic HTML with proper heading hierarchy, ARIA labels, and `<time datetime>`.
