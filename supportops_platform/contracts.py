"""Versioned local boundary contracts; doubles do not represent real package integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    NEEDS_APPROVAL = "needs_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    tenant_id: str
    roles: frozenset[str] = frozenset()
    scopes: frozenset[str] = frozenset()


@dataclass(slots=True)
class Ticket:
    tenant_id: str
    customer_id: str
    subject: str
    body: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "open"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class Approval:
    tenant_id: str
    ticket_id: str
    action: str
    amount_cents: int
    idempotency_key: str
    requested_by: str
    id: str = field(default_factory=lambda: str(uuid4()))
    state: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class Citation:
    document_id: str
    title: str
    chunk_id: str
    text: str
    score: float


@dataclass(frozen=True, slots=True)
class PackageProvenance:
    package: str
    version: str
    origin_commit: str
    artifact_sha256: str
    approved: bool = False


class ContractError(ValueError):
    """Raised when a boundary contract receives an invalid value."""


class AuthorizationLeaseExpired(ValueError):
    """A durable task outlived its original authorization lease."""
