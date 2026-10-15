"""Integration tests against P04's approved wheel with in-process doubles."""

import pytest

pytest.importorskip("supportops_async")

from fastapi.testclient import TestClient

from supportops_platform.integrations.p04_async import create_p04_local_components


def test_p04_api_idempotency_and_fake_worker_completion() -> None:
    app, store, broker, worker = create_p04_local_components()
    api = TestClient(app)
    first = api.post("/tasks", headers={"Idempotency-Key": "p05-p04-1"}, json={"steps": ["triage"]})
    replay = api.post("/tasks", headers={"Idempotency-Key": "p05-p04-1"}, json={"steps": ["triage"]})
    assert first.status_code == replay.status_code == 202
    task_id = first.json()["task_id"]
    assert task_id == replay.json()["task_id"]
    assert first.headers["Idempotency-Replayed"] == "false"
    assert replay.headers["Idempotency-Replayed"] == "true"
    assert api.get(f"/tasks/{task_id}").json()["status"] == "queued"
    assert worker.run_once() is True
    completed = api.get(f"/tasks/{task_id}").json()
    assert completed["status"] == "done"
    assert completed["result"]["steps"][0]["outcome"] == "simulated"
    # P04 republishes on idempotent HTTP retry; the worker must safely ack the duplicate.
    assert worker.run_once() is True
    assert broker.consume() is None
    store.close()
