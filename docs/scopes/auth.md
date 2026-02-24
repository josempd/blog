# scope: auth

Authentication and user management — login routes, JWT token handling, password hashing, user CRUD, services, and permissions.

## Key Files

```
backend/app/core/security.py       # Password hashing (argon2/bcrypt), JWT creation/verification
backend/app/api/routes/login.py    # POST /login/access-token, test-token, password recovery
backend/app/api/routes/users.py    # User CRUD endpoints (create, read, update, delete)
backend/app/api/routes/private.py  # Protected endpoint example
backend/app/models/user.py         # User model
backend/app/schemas/user.py        # User schemas (Create, Update, Public, etc.)
backend/app/schemas/auth.py        # Token, TokenPayload, NewPassword
backend/app/crud/user.py           # User data access functions
backend/app/services/user.py       # User lifecycle business logic
backend/app/services/auth.py       # Authentication flows (login, password recovery/reset)
```

## Dependencies

- **core** — config (SECRET_KEY), db (Session), exceptions, deps (CurrentUser)

## Testing

- `backend/tests/api/routes/test_login.py` — login flow, token generation
- `backend/tests/api/routes/test_users.py` — user CRUD endpoints
- `backend/tests/api/routes/test_private.py` — auth-protected routes
- `backend/tests/crud/test_user.py` — user data access
- `backend/tests/services/test_user.py` — user service business logic
- `backend/tests/services/test_auth.py` — auth service business logic

## Notes

Do NOT change auth behavior (JWT algorithm, token format, password hashing, OAuth2 flow) without explicit approval. Structural refactoring (extracting services, fixing route → service → CRUD layering) is allowed.
