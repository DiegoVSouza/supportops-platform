"""CORS allowlist for a browser front served from another origin.

Clients authenticate with a bearer token, never a cookie, so credentials stay off and the allowlist is
the only gate: an exact scheme + host + port match. Wildcards, paths and plain http (except loopback)
are refused at startup so a typo cannot widen the surface.
"""
from __future__ import annotations

from urllib.parse import urlsplit

ALLOWED_METHODS = ["GET", "POST", "OPTIONS"]
ALLOWED_HEADERS = ["Authorization", "Content-Type", "Idempotency-Key", "traceparent", "tracestate"]
EXPOSED_HEADERS = ["Retry-After"]
LOOPBACK = {"localhost", "127.0.0.1", "[::1]"}


def _normalize(raw: str) -> str:
    if "*" in raw:
        raise ValueError(f"CORS_ALLOWED_ORIGINS must not contain a wildcard: {raw!r}")
    parts = urlsplit(raw)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError(f"CORS origin must be http(s)://host[:port]: {raw!r}")
    if parts.path not in {"", "/"} or parts.query or parts.fragment or parts.username or parts.password:
        raise ValueError(f"CORS origin must not carry a path, query or credentials: {raw!r}")
    host = parts.hostname.lower()
    display = f"[{host}]" if ":" in host else host
    if parts.scheme == "http" and display not in LOOPBACK:
        raise ValueError(f"CORS origin must use https unless it is loopback: {raw!r}")
    port = f":{parts.port}" if parts.port else ""
    return f"{parts.scheme}://{display}{port}"


def parse_cors_origins(value: str | None) -> list[str]:
    """Comma-separated origins to a deduplicated, normalized list. Empty or None means CORS is off."""
    if not value or not value.strip():
        return []
    origins: list[str] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        origin = _normalize(item)
        if origin not in origins:
            origins.append(origin)
    return origins
