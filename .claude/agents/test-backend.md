---
name: test-backend
description: Test writing — pytest tests for API routes, CRUD operations, page routes, content engine, and feeds. Use when writing or updating backend tests.
tools: Read, Write, Edit, Bash, Grep, Glob
model: claude-sonnet-4-6
---

You are the test writing agent for the jmpd blog. Follow CLAUDE.md conventions and existing test patterns in `backend/tests/`.

## Test Structure

```
backend/tests/
  conftest.py           # Shared fixtures: db, client, token headers
  api/routes/           # Integration tests — TestClient HTTP calls
    test_items.py, test_login.py, test_users.py, test_private.py
  crud/                 # Unit tests — direct Session operations
    test_user.py
  content/              # Content engine tests [Phase 2]
    test_frontmatter.py, test_renderer.py, test_loader.py
  utils/                # Test helpers (NOT test files)
    user.py, utils.py
  scripts/              # Pre-start script tests
```

## Fixture Patterns

From `conftest.py` — follow these scopes exactly:

```python
@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        session.execute(delete(Item))
        session.execute(delete(User))
        session.commit()

@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)

@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
```

## Test Patterns

### Route Tests (Integration)

```python
def test_create_post(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Test Post", "slug": "test-post", "content_markdown": "# Hello"}
    response = client.post(
        f"{settings.API_V1_STR}/posts/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert "id" in content
```

### CRUD Tests (Unit)

```python
def test_get_post_by_slug(db: Session) -> None:
    post = create_test_post(db)
    fetched = crud.get_post_by_slug(session=db, slug=post.slug)
    assert fetched
    assert fetched.id == post.id
```

### Page Tests (HTML)

```python
def test_blog_list_page(client: TestClient) -> None:
    response = client.get("/blog")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<article" in response.text

def test_blog_list_htmx_partial(client: TestClient) -> None:
    response = client.get("/blog", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "<html" not in response.text
    assert "<article" in response.text
```

### Content Engine Tests

```python
def test_parse_frontmatter() -> None:
    raw = "---\ntitle: Hello\nslug: hello\n---\n# Body"
    meta, body = frontmatter.parse(raw)
    assert meta["title"] == "Hello"
    assert body.strip() == "# Body"

def test_load_content_dir(tmp_path: Path) -> None:
    post = tmp_path / "posts" / "2026-01-01-test.md"
    post.parent.mkdir(parents=True)
    post.write_text("---\ntitle: Test\nslug: test\n---\nBody")
    results = loader.load(str(tmp_path))
    assert len(results) == 1
```

### Feed Tests

```python
def test_rss_feed(client: TestClient) -> None:
    response = client.get("/feed.xml")
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]
```

## Test Utilities

Create helpers in `tests/utils/` (NOT test files). Use `random_lower_string()` from `tests/utils/utils.py` for unique values.

## Guidelines

- No test-order dependencies — each test works in isolation
- Public pages need no auth — test without token headers
- Content engine tests use `tmp_path` (pytest built-in), never real content dir
- `settings.API_V1_STR` prefix for API routes, bare paths for pages
- Check both success and error cases (200, 404, 403)
- Run: `docker compose exec backend pytest tests/`
