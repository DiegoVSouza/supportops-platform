from types import SimpleNamespace

import pytest

from supportops_platform.contracts import Principal
from supportops_platform.service_runtime import ServiceWorker


ACTOR = Principal("agent-a", "tenant-a", frozenset({"agent"}), frozenset({"refund:request"}))


class Queue:
    def __init__(self, job):
        self.record = job
        self.finished = []

    def job(self, _identifier):
        return self.record

    def authorization_active(self, _identifier, _generation):
        return True

    def actor(self, _job):
        return ACTOR

    def finish(self, identifier, status, result, approval_id=None, *, generation):
        self.finished.append((identifier, status, result, generation))


class Store:
    def __init__(self, state):
        self.state = state
        self.effects = []

    def get_ticket(self, _actor, _ticket_id):
        return SimpleNamespace(subject="Goodwill credit", body="No trigger word here")

    def approval(self, _actor, approval_id):
        return SimpleNamespace(id=approval_id, state=self.state, amount_cents=1234)

    def simulated_refund(self, job_id, amount_cents):
        self.effects.append((job_id, amount_cents))
        return {"simulated": True, "amount_cents": amount_cents}


def worker(state):
    job = {"id": "job-1", "generation": 1, "status": "queued", "ticket_id": "t-1", "approval_id": "a-1",
           "idempotency_key": "refund:key", "trace_context": {}}
    runtime = ServiceWorker.__new__(ServiceWorker)
    runtime.queue = Queue(job)
    runtime.store = Store(state)
    runtime.retriever = None
    runtime.triage_handler = None
    return runtime


@pytest.mark.parametrize("state, effects", [("approved", [("job-1", 1234)]), ("rejected", [])])
def test_manual_refund_carries_out_the_decision_without_triage(monkeypatch, state, effects):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("a manual refund must not run the agent")

    monkeypatch.setattr("supportops_platform.service_runtime.run_configured_triage", forbidden)
    runtime = worker(state)
    result = runtime.run_job({"job_id": "job-1", "generation": 1}, "triage")
    assert runtime.store.effects == effects
    assert result["approval_state"] == state
    assert ("refund" in result) is (state == "approved")
    assert runtime.queue.finished == [("job-1", "succeeded", result, 1)]
