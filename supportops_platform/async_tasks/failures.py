"""Fixed, content-free failure codes shared by task producers and API readers."""

from __future__ import annotations


FAILURE_CODES = frozenset(
    {
        "authorization_expired",
        "authorization_failure",
        "dependency_failure",
        "invalid_input",
        "maximum_attempts_exceeded",
        "timeout",
        "transient_failure",
        "worker_failure",
    }
)


def failure_code(error: BaseException | str | None) -> str | None:
    """Map exceptions and persisted strings to a fixed allowlisted error code."""
    if error is None:
        return None
    if isinstance(error, str):
        if error == "authorization lease expired":
            return "authorization_expired"
        if error == "maximum attempts exceeded":
            return "maximum_attempts_exceeded"
        return error if error in FAILURE_CODES else "worker_failure"
    if isinstance(error, TimeoutError):
        return "timeout"
    if isinstance(error, PermissionError):
        return "authorization_failure"
    if isinstance(error, (ConnectionError, OSError)):
        return "dependency_failure"
    if isinstance(error, (ValueError, TypeError)):
        return "invalid_input"
    return "worker_failure"
