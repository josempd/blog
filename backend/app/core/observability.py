"""OpenTelemetry tracing and metrics setup.

Call ``setup_observability(app)`` during startup.  Everything is a no-op
when ``settings.OTEL_ENABLED`` is ``False``.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI

from app.core.config import settings

logger = structlog.get_logger(__name__)


def setup_observability(app: FastAPI) -> None:
    """Initialise OTEL TracerProvider, MeterProvider, and auto-instrumentation.

    Silently degrades if the collector is unreachable (exports just fail,
    the app keeps running).
    """
    if not settings.OTEL_ENABLED:
        logger.info("otel_disabled")
        return

    try:
        _init_otel(app)
        logger.info("otel_initialized", endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
    except Exception:
        logger.exception("otel_init_failed")


def _init_otel(app: FastAPI) -> None:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": settings.OTEL_SERVICE_NAME})

    # --- Traces ---
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # --- Metrics ---
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT),
        export_interval_millis=settings.OTEL_METRIC_EXPORT_INTERVAL_MS,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    meter = meter_provider.get_meter(settings.OTEL_SERVICE_NAME)
    app.state.otel_metrics = {
        "request_count": meter.create_counter(
            "http.server.request.count",
            description="Total HTTP requests",
        ),
        "request_duration": meter.create_histogram(
            "http.server.request.duration",
            unit="s",
            description="HTTP request duration",
        ),
        "error_count": meter.create_counter(
            "http.server.error.count",
            description="Total HTTP 5xx errors",
        ),
    }

    # --- Auto-instrumentation ---
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
