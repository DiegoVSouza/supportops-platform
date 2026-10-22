"""P03 telemetry adapter. Export is disabled unless a separate runtime config enables it."""

import os
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from supportops_obs.instrumentation import metrics_registry, setup_telemetry


def configure_telemetry() -> None:
    setup_telemetry(os.getenv("OTEL_SERVICE_NAME","supportops-platform"), otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"), capture_content=False)


def prometheus_metrics() -> tuple[bytes, str]:
    return generate_latest(metrics_registry()), CONTENT_TYPE_LATEST
