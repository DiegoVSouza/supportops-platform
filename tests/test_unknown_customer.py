from types import SimpleNamespace

from supportops_platform.contracts import Principal
from supportops_platform.service_runtime import ServiceWorker

ACTOR = Principal("agent-a", "tenant-a", frozenset({"agent"}), frozenset({"crm:read", "billing:read"}))


class Queue:
    def __init__(self):
        self.finished = []

    def job(self, _identifier):
        return {"id": "job-1", "generation": 1, "status": "queued", "ticket_id": "t-1", "approval_id": None,
                "idempotency_key": "triage:key", "trace_context": {}}

    def authorization_active(self, _identifier, _generation):
        return True

    def actor(self, _job):
        return ACTOR

    def finish(self, identifier, status, result, approval_id=None, *, generation):
        self.finished.append((identifier, status, result))


class Store:
    def __init__(self, customer_id):
        self.customer_id = customer_id

    def get_ticket(self, _actor, _ticket_id):
        return SimpleNamespace(id="t-1", subject="Cannot log in", body="Password reset mail never arrives",
                               customer_id=self.customer_id)


def triage(_ticket, _retriever, **_kwargs):
    decision = SimpleNamespace(response="Use the reset link on the sign-in page.")
    outcome = SimpleNamespace(trace=["classify", "answer"], decision=decision, stop_reason="done")
    return SimpleNamespace(result=outcome, citations=[], live_metrics=None, llm_steps=None)


def worker(customer_id):
    runtime = ServiceWorker.__new__(ServiceWorker)
    runtime.queue = Queue()
    runtime.store = Store(customer_id)
    runtime.retriever = None
    runtime.triage_handler = triage
    return runtime


def tools(known):
    def call(_actor, name, arguments):
        if name == "lookup_customer":
            if arguments["customer_id"] not in known:
                raise PermissionError("MCP tool denied or failed")
            return {"customer_id": arguments["customer_id"], "tier": "standard"}
        return {"invoice_id": arguments["invoice_id"], "amount_cents": 2500, "status": "paid"}

    return call


def test_a_customer_the_crm_does_not_know_does_not_fail_the_whole_run(monkeypatch):
    # The console lets a visitor type any customer. The triage already ran (and was paid); losing the answer over a missing CRM row wastes it.
    monkeypatch.setattr("supportops_platform.service_runtime.call_tool", tools({"customer-a"}))
    runtime = worker("maria-silva")
    result = runtime.run_job({"job_id": "job-1", "generation": 1}, "triage")
    assert result["response"] == "Use the reset link on the sign-in page."
    assert result["customer"] == {"customer_id": "maria-silva", "tier": "unknown", "found": False}
    assert runtime.queue.finished[0][1] == "succeeded"


def test_a_known_customer_keeps_the_crm_record(monkeypatch):
    monkeypatch.setattr("supportops_platform.service_runtime.call_tool", tools({"customer-a"}))
    result = worker("customer-a").run_job({"job_id": "job-1", "generation": 1}, "triage")
    assert result["customer"] == {"customer_id": "customer-a", "tier": "standard"}
