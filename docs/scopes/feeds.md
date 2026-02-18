# scope: feeds

Machine discovery — RSS/Atom feeds, llms.txt, sitemap.xml, JSON-LD structured data, and Open Graph meta tags.

## Key Files

```
backend/app/api/routes/feeds.py    # RSS/Atom XML endpoints
backend/app/pages/feeds.py         # sitemap.xml, llms.txt, robots.txt routes
backend/app/templates/feeds/       # Feed XML templates (rss.xml, atom.xml, sitemap.xml)
```

## Dependencies

- **core** — config (DOMAIN, site metadata)
- **blog** — PostService (recent posts for feeds)
- **portfolio** — ProjectService (projects for sitemap)

## Testing

- Feed XML validation (well-formed RSS/Atom)
- Sitemap structure verification
- JSON-LD schema validation
- Open Graph meta tag presence in HTML responses
- llms.txt content and format
