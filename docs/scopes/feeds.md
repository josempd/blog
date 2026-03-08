# scope: feeds

Machine discovery — RSS/Atom feeds, llms.txt, sitemap.xml, JSON-LD structured data, and Open Graph meta tags.

## Key Files

```
backend/app/pages/feeds.py         # RSS/Atom, sitemap.xml, llms.txt, robots.txt routes
backend/app/templates/feeds/       # Feed XML templates (rss.xml, atom.xml, sitemap.xml)
```

## Dependencies

- **core** — config (DOMAIN, site metadata)
- **blog** — services.blog (recent posts for feeds)
- **portfolio** — services.portfolio (projects for sitemap)

## Testing

- `backend/tests/pages/test_feeds.py` — feed route tests
- Feed XML validation (well-formed RSS/Atom)
- Sitemap structure verification
- JSON-LD schema validation
- Open Graph meta tag presence in HTML responses
- llms.txt content and format
