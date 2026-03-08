# scope: blog

Blog domain — post and tag models, schemas, CRUD, services, and API/page routes for blog content.

## Key Files

```
backend/app/models/post.py         # Post model (title, slug, content, published_at); Tag, PostTagLink
backend/app/schemas/post.py        # PostUpsert, TagCreate, PostPublic, PostDetail, PostsPublic, TagPublic, TagWithCount
backend/app/crud/post.py           # Post queries (by slug, paginated list, upsert)
backend/app/services/post.py       # sync_post_from_content (content → DB sync)
backend/app/services/blog.py       # list_published_posts, get_published_post, search_published_posts, list_tags
backend/app/pages/blog.py          # HTML page routes (/blog, /blog/:slug)
```

## Dependencies

- **core** — db, exceptions, deps
- **content** — renderer (markdown → HTML), loader (source files)

## Testing

- `backend/tests/crud/test_post.py` — post data access unit tests
- `backend/tests/services/test_blog_service.py` — blog service tests
- `backend/tests/pages/test_blog.py` — blog page route tests
