# scope: tests

Test suite — pytest integration/unit tests, test fixtures, test utilities, and Playwright e2e tests.

## Key Files

```
backend/tests/
  conftest.py              # Shared fixtures (db session, client, auth tokens)
  api/routes/              # API integration tests (TestClient)
  crud/                    # CRUD unit tests (direct Session)
  services/                # Service unit tests
  scripts/                 # Pre-start script tests
  utils/                   # Test helpers (NOT test files)
    utils.py               # random_lower_string, etc.
    user.py                # User creation helpers
    item.py                # Item creation helpers

e2e/                       # Playwright browser tests
```

## Dependencies

- **core** — test fixtures use db session, config
- **auth** — test fixtures use auth tokens, user creation

## Testing

Tests scope is self-referential — changes here affect test infrastructure, not application behavior. Verify by running the full test suite: `make test`.
