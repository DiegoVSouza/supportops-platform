from datetime import datetime, timedelta, timezone

import pytest

from supportops_platform.async_tasks.queue import EffectLedger, FakeWorker, LocalTaskQueue
from supportops_platform.contracts import Principal, TaskStatus


def principal(tenant_id: str = "tenant-a") -> Principal:
    return Principal(subject="agent", tenant_id=tenant_id, roles=frozenset({"agent"}))


def test_enqueue_is_idempotent_and_conflicting_reuse_fails() -> None:
    queue = LocalTaskQueue()
    first = queue.enqueue(principal(), "triage", {"ticket_id": "t1"}, "key-1")
    duplicate = queue.enqueue(principal(), "triage", {"ticket_id": "t1"}, "key-1")
    assert first.id == duplicate.id
    with pytest.raises(ValueError, match="different task"):
        queue.enqueue(principal(), "triage", {"ticket_id": "t2"}, "key-1")


def test_expired_worker_lease_recovers_task_for_retry() -> None:
    queue = LocalTaskQueue(lease_seconds=5, max_attempts=2)
    task = queue.enqueue(principal(), "triage", {"ticket_id": "t1"}, "key-1")
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert queue.claim("worker-a", now=start).id == task.id
    recovered = queue.claim("worker-b", now=start + timedelta(seconds=6))
    assert recovered.id == task.id
    assert recovered.attempts == 2
    assert recovered.worker_id == "worker-b"


def test_expired_worker_cannot_acknowledge_after_lease() -> None:
    queue = LocalTaskQueue(lease_seconds=5, max_attempts=2)
    task = queue.enqueue(principal(), "triage", {"ticket_id": "t1"}, "key-1")
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    queue.claim("worker-a", now=start)
    with pytest.raises(ValueError, match="not leased"):
        queue.complete("worker-a", task.id, now=start + timedelta(seconds=5))


def test_retry_limit_and_wrong_worker_are_enforced() -> None:
    queue = LocalTaskQueue(max_attempts=1)
    task = queue.enqueue(principal(), "triage", {"ticket_id": "t1"}, "key-1")
    queue.claim("worker-a")
    with pytest.raises(ValueError, match="not leased"):
        queue.complete("worker-b", task.id)
    failed = queue.fail("worker-a", task.id, "crash")
    assert failed.status == TaskStatus.FAILED
    assert queue.claim("worker-c") is None


def test_tenant_cannot_read_another_tenant_task() -> None:
    queue = LocalTaskQueue()
    task = queue.enqueue(principal("tenant-a"), "triage", {"ticket_id": "t1"}, "key-1")
    with pytest.raises(PermissionError, match="not found"):
        queue.get(principal("tenant-b"), task.id)


def test_effect_ledger_suppresses_duplicate_delivery() -> None:
    ledger = EffectLedger()
    assert ledger.apply_once("task-1", "triage completed") is True
    assert ledger.apply_once("task-1", "triage completed") is False
    assert ledger.effects == ["triage completed"]


def test_fake_worker_completes_once_and_retries_handler_failure() -> None:
    queue = LocalTaskQueue(max_attempts=2)
    ledger = EffectLedger()
    first = queue.enqueue(principal(), "triage", {"ticket_id": "t1"}, "key-1")
    worker = FakeWorker(queue, "worker-a", ledger)
    failed = worker.run_once(lambda task: (_ for _ in ()).throw(RuntimeError("temporary")))
    assert failed.id == first.id
    assert failed.status == TaskStatus.QUEUED
    succeeded = worker.run_once()
    assert succeeded.status == TaskStatus.SUCCEEDED
    assert len(ledger.effects) == 1


def test_task_input_limits_and_required_lease_configuration() -> None:
    with pytest.raises(ValueError, match="positive"):
        LocalTaskQueue(lease_seconds=0)
    queue = LocalTaskQueue()
    with pytest.raises(ValueError, match="idempotency"):
        queue.enqueue(principal(), "triage", {}, "")
    with pytest.raises(ValueError, match="bounds"):
        queue.enqueue(principal(), "triage", {"large": "x" * 501}, "key")
