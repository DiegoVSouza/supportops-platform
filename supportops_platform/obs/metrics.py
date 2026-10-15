"""Bounded-cardinality local HTTP metrics compatible with Prometheus text format."""

from collections import Counter
from threading import Lock

ALLOWED_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"})


class MetricsRegistry:
    def __init__(self) -> None:
        self._requests: Counter[tuple[str, int]] = Counter()
        self._lock = Lock()

    def record_request(self, method: str, status_code: int) -> None:
        method = method.upper()
        if method not in ALLOWED_METHODS:
            method = "OTHER"
        if not 100 <= status_code <= 599:
            status_code = 500
        with self._lock:
            self._requests[(method, status_code)] += 1

    def render(self) -> str:
        with self._lock:
            snapshot = sorted(self._requests.items())
        lines = [
            "# HELP supportops_http_requests_total Completed HTTP requests by bounded method and status.",
            "# TYPE supportops_http_requests_total counter",
        ]
        for (method, status), count in snapshot:
            lines.append(
                f'supportops_http_requests_total{{method="{method}",status="{status}"}} {count}'
            )
        return "\n".join(lines) + "\n"
