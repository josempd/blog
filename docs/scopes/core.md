# scope: core

App foundation — config, database, exceptions, logging, middleware, observability, dependency injection, and startup scripts.

## Key Files

```
backend/app/core/
  config.py              # Settings class (pydantic-settings, reads .env)
  db.py                  # SQLModel engine, session factory
  exceptions.py          # AppError hierarchy (NotFoundError, ConflictError, etc.)
  exception_handlers.py  # AppError → RFC 9457 Problem Details response mappers
  logging.py             # structlog configuration, sensitive data filters
  middleware.py          # Request/response middleware (trace_id, logging)
  observability.py       # OpenTelemetry setup (OTLP exporter)

backend/app/main.py             # FastAPI app creation, router mounts
backend/app/api/deps.py         # SessionDep, CurrentUser, service dependency factories
backend/app/api/main.py         # APIRouter registration
backend/app/api/routes/utils.py # Health check, utility endpoints
backend/app/backend_pre_start.py # DB readiness check
backend/app/initial_data.py      # First superuser creation
backend/app/utils.py             # Shared utility functions
```

## Dependencies

None — core is the foundation layer. All other scopes depend on core.

## Testing

- `backend/tests/scripts/` — pre-start script tests
- `backend/tests/api/routes/test_utils.py` — health check tests (future)
- Unit tests for exception handlers, middleware, logging config
