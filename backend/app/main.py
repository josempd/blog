from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.db import engine
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import (
    MetricsMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    TraceIdMiddleware,
)
from app.core.observability import setup_observability
from app.core.rate_limit import limiter
from app.pages.router import pages_router

# 1. Structured logging — must be first so all subsequent logs are formatted
setup_logging(
    log_level=settings.LOG_LEVEL,
    json_output=settings.LOG_FORMAT == "json",
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    # --- Shutdown ---
    logger.info("shutdown_started")
    if settings.OTEL_ENABLED:
        _shutdown_otel()
    engine.dispose()
    logger.info("shutdown_complete")


def _shutdown_otel() -> None:
    try:
        from opentelemetry import metrics, trace
        from opentelemetry.sdk.metrics import MeterProvider as SdkMeterProvider
        from opentelemetry.sdk.trace import TracerProvider as SdkTracerProvider

        tracer_provider = trace.get_tracer_provider()
        if isinstance(tracer_provider, SdkTracerProvider):
            tracer_provider.force_flush(timeout_millis=5000)
            tracer_provider.shutdown()

        meter_provider = metrics.get_meter_provider()
        if isinstance(meter_provider, SdkMeterProvider):
            meter_provider.force_flush(timeout_millis=5000)
            meter_provider.shutdown()
    except Exception:
        logger.warning("otel_shutdown_failed", exc_info=True)


def custom_generate_unique_id(route: APIRoute) -> str:
    if route.tags:
        return f"{route.tags[0]}-{route.name}"
    return route.name


# 2. Create app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# 3. Exception handlers (RFC 9457 Problem Details)
register_exception_handlers(app)

# 3b. Rate limiter state (used by SlowAPI decorators)
app.state.limiter = limiter

# 4. Middleware — last-added runs first, so add order is:
#    Metrics → RequestLogging → TraceId → CORS → SecurityHeaders
#    Execution order: SecurityHeaders → CORS → TraceId → RequestLogging → Metrics
app.add_middleware(MetricsMiddleware)  # type: ignore[arg-type]
app.add_middleware(RequestLoggingMiddleware)  # type: ignore[arg-type]
app.add_middleware(TraceIdMiddleware)  # type: ignore[arg-type]
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )
app.add_middleware(SecurityHeadersMiddleware)  # type: ignore[arg-type]

# 5. OpenTelemetry (no-op if OTEL_ENABLED=false)
setup_observability(app)

# 6. Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(pages_router)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> RedirectResponse:
    return RedirectResponse(url="/static/favicon.svg", status_code=301)


app.mount("/static", StaticFiles(directory="app/static"), name="static")
