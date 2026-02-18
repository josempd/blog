# scope: blog

Blog domain — post and tag models, schemas, CRUD, services, and API/page routes for blog content.

## Key Files

```
backend/app/models/post.py         # Post model (title, slug, content, published_at)
backend/app/models/tag.py          # Tag model, PostTagLink many-to-many
backend/app/schemas/post.py        # PostCreate, PostUpdate, PostPublic, PostsPublic
backend/app/schemas/tag.py         # TagPublic
backend/app/crud/post.py           # Post queries (by slug, paginated list, upsert)
backend/app/services/post.py       # PostService (create, get, list, sync from content)
backend/app/api/routes/posts.py    # JSON API endpoints (/api/v1/posts)
backend/app/pages/blog.py          # HTML page routes (/blog, /blog/:slug)
```

## Dependencies

- **core** — db, exceptions, deps
- **content** — renderer (markdown → HTML), loader (source files)
- **auth** — author_id foreign key to User

## Testing

- `backend/tests/api/routes/test_posts.py` — post API integration tests
- `backend/tests/crud/test_post.py` — post data access unit tests
- `backend/tests/services/test_post.py` — post business logic tests
