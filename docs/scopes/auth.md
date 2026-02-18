# scope: auth

Authentication and user management — login routes, JWT token handling, password hashing, user CRUD, and permissions.

## Key Files

```
backend/app/core/security.py       # Password hashing (argon2/bcrypt), JWT creation/verification
backend/app/api/routes/login.py    # POST /login/access-token, test-token
backend/app/api/routes/users.py    # User CRUD endpoints (create, read, update, delete)
backend/app/api/routes/private.py  # Protected endpoint example
backend/app/models.py              # User model (temporary monolith, will split)
backend/app/crud.py                # User CRUD functions (temporary monolith, will split)
```

## Dependencies

- **core** — config (SECRET_KEY), db (Session), exceptions, deps (CurrentUser)

## Testing

- `backend/tests/api/routes/test_login.py` — login flow, token generation
- `backend/tests/api/routes/test_users.py` — user CRUD endpoints
- `backend/tests/api/routes/test_private.py` — auth-protected routes
- `backend/tests/crud/test_user.py` — user data access

## Notes

Do NOT modify auth unless explicitly required. The auth system is inherited from the FastAPI template and is intentionally left stable.
