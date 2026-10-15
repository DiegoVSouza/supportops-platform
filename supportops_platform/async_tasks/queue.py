"""Local deterministic queue contract; the P04 broker integration remains separate."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from uuid import uuid4

from supportops_platform.contracts import Principal, TaskStatus
from supportops_platform.repositories import AuthorizationError


@dataclass(slots=True)
class TaskRecord:
    tenant_id: str
    task_type: str
    payload: dict[str, str]
    idempotency_key: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: TaskStatus = TaskStatus.QUEUED
    attempts: int = 0
    worker_id: str | None = None
    lease_until: datetime | None = None
    last_error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LocalTaskQueue:
    """Thread-safe queue double with leases and tenant-bound idempotency."""

    def __init__(self, lease_seconds: int = 30, max_attempts: int = 3):
        if lease_seconds < 1 or max_attempts < 1:
            raise ValueError("lease_seconds and max_attempts must be positive")
        self.lease_seconds = lease_seconds
        self.max_attempts = max_attempts
        self._tasks: dict[str, TaskRecord] = {}
        self._keys: dict[tuple[str, str], str] = {}
        self._lock = Lock()

    def enqueue(
        self, principal: Principal, task_type: str, payload: dict[str, str], idempotency_key: str
    ) -> TaskRecord:
        if not task_type or len(task_type) > 80:
            raise ValueError("task_type must contain 1 to 80 characters")
        if not idempotency_key or len(idempotency_key) > 128:
            raise ValueError("valid idempotency key required")
        if len(payload) > 20 or any(len(key) > 80 or len(value) > 500 for key, value in payload.items()):
            raise ValueError("task payload exceeds local bounds")
        key = (principal.tenant_id, idempotency_key)
        with self._lock:
            prior_id = self._keys.get(key)
            if prior_id:
                prior = self._tasks[prior_id]
                if prior.task_type != task_type or prior.payload != payload:
                    raise ValueError("idempotency key reused with different task")
                return prior
            task = TaskRecord(principal.tenant_id, task_type, payload.copy(), idempotency_key)
            self._tasks[task.id] = task
            self._keys[key] = task.id
            return task

    def get(self, principal: Principal, task_id: str) -> TaskRecord:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.tenant_id != principal.tenant_id:
                raise AuthorizationError("task not found")
            return task

    def claim(self, worker_id: str, now: datetime | None = None) -> TaskRecord | None:
        if not worker_id:
            raise ValueError("worker_id required")
        now = now or datetime.now(timezone.utc)
        with self._lock:
            for task in self._tasks.values():
                expired = task.status == TaskStatus.RUNNING and task.lease_until and task.lease_until <= now
                if task.status != TaskStatus.QUEUED and not expired:
                    continue
                if task.attempts >= self.max_attempts:
                    task.status = TaskStatus.FAILED
                    task.last_error = task.last_error or "maximum attempts exceeded"
                    continue
                task.status = TaskStatus.RUNNING
                task.attempts += 1
                task.worker_id = worker_id
                task.lease_until = now + timedelta(seconds=self.lease_seconds)
                return task
        return None

    def complete(
        self, worker_id: str, task_id: str, now: datetime | None = None
    ) -> TaskRecord:
        now = now or datetime.now(timezone.utc)
        with self._lock:
            task = self._tasks.get(task_id)
            if (
                task is None
                or task.status != TaskStatus.RUNNING
                or task.worker_id != worker_id
                or task.lease_until is None
                or task.lease_until <= now
            ):
                raise ValueError("task is not leased by this worker")
            task.status = TaskStatus.SUCCEEDED
            task.lease_until = None
            return task

    def fail(
        self, worker_id: str, task_id: str, reason: str, now: datetime | None = None
    ) -> TaskRecord:
        now = now or datetime.now(timezone.utc)
        with self._lock:
            task = self._tasks.get(task_id)
            if (
                task is None
                or task.status != TaskStatus.RUNNING
                or task.worker_id != worker_id
                or task.lease_until is None
                or task.lease_until <= now
            ):
                raise ValueError("task is not leased by this worker")
            task.last_error = reason[:500]
            task.lease_until = None
            task.worker_id = None
            task.status = TaskStatus.FAILED if task.attempts >= self.max_attempts else TaskStatus.QUEUED
            return task


class EffectLedger:
    """Fake downstream ledger illustrating idempotent effects across redelivery."""

    def __init__(self) -> None:
        self.applied: set[str] = set()
        self.effects: list[str] = []

    def apply_once(self, effect_key: str, effect_description: str) -> bool:
        if not effect_key:
            raise ValueError("effect key required")
        if effect_key in self.applied:
            return False
        self.applied.add(effect_key)
        self.effects.append(effect_description)
        return True


class FakeWorker:
    """Synchronous fake worker used to exercise task-state transitions in tests/demo."""

    def __init__(self, queue: LocalTaskQueue, worker_id: str, effects: EffectLedger):
        self.queue = queue
        self.worker_id = worker_id
        self.effects = effects

    def run_once(self, handler=None) -> TaskRecord | None:
        task = self.queue.claim(self.worker_id)
        if task is None:
            return None
        try:
            if handler is not None:
                handler(task)
            self.effects.apply_once(f"task:{task.id}", f"processed {task.task_type}")
        except Exception as exc:
            return self.queue.fail(self.worker_id, task.id, str(exc))
        return self.queue.complete(self.worker_id, task.id)
