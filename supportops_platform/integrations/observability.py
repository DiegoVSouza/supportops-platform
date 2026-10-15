"""P03 telemetry adapter. Export is disabled unless a separate runtime config enables it."""

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from supportops_obs.instrumentation import metrics_registry, setup_telemetry


def configure_telemetry() -> None:
    setup_telemetry("supportops-platform", otlp_endpoint=None, capture_content=False)


def prometheus_metrics() -> tuple[bytes, str]:
    return generate_latest(metrics_registry()), CONTENT_TYPE_LATEST
