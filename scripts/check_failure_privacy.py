"""Exercise sanitized P05 worker persistence and API reads inside isolated services."""

from __future__ import annotations

import json
import os
import time
from uuid import uuid4

import httpx
import psycopg
from opentelemetry import trace
from supportops_obs import flush_telemetry

import supportops_platform.service_runtime as runtime
from supportops_platform.auth.jwt import issue_demo_token
from supportops_platform.contracts import Principal, Ticket
from supportops_platform.integrations.observability import configure_telemetry
from supportops_platform.service_runtime import ServiceWorker, create_components


SENTINEL = "P05_PRIVATE_FAILURE_SENTINEL_MUST_NOT_PERSIST"
EXPECTED_FAILURE_SPANS = {"worker.run", "agent.triage"}


def read_failure_trace(trace_id: str, *, get=httpx.get, sleep=time.sleep, attempts: int = 60):
    """Poll Jaeger for collector-delivered spans without repeating the task."""
    if not isinstance(trace_id, str) or len(trace_id) != 32 or any(char not in "0123456789abcdef" for char in trace_id.lower()):
        raise ValueError("invalid trace identifier")
    if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 1 or attempts > 120:
        raise ValueError("trace read attempts must be between 1 and 120")
    last_payload = {"data": None}
    for attempt in range(attempts):
        try:
            response = get("http://jaeger:16686/api/traces/" + trace_id, timeout=2)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                last_payload = payload
        except httpx.HTTPError:
            last_payload = {"data": None}
        spans = [
            span
            for item in (last_payload.get("data") or [])
            for span in item.get("spans", [])
        ]
        operations = {span.get("operationName") for span in spans}
        if EXPECTED_FAILURE_SPANS.issubset(operations):
            return last_payload, spans, True
        if attempt + 1 < attempts:
            sleep(0.25)
    spans = [
        span
        for item in (last_payload.get("data") or [])
        for span in item.get("spans", [])
    ]
    return last_payload, spans, False


def main() -> None:
    if os.getenv("LLM_MODE") != "fake" or os.getenv("P05_RUNTIME") != "services":
        raise RuntimeError("service privacy probe requires fake service runtime")
    configure_telemetry()
    os.environ["P05_QUEUE_NAME"] = "p05-failure-privacy-" + uuid4().hex
    store, retriever, queue, _ = create_components()
    actor = Principal(
        "privacy-probe-agent",
        "tenant-a",
        frozenset({"agent"}),
        frozenset(
            {
                "ticket:read",
                "ticket:write",
                "task:read",
                "task:write",
                "triage:run",
                "billing:read",
                "crm:read",
                "refund:request",
                "feedback:write",
            }
        ),
    )
    ticket = store.add_ticket(
        actor,
        Ticket("tenant-a", "customer-a", "Privacy probe", "Synthetic service test."),
    )
    tracer = trace.get_tracer("p05.failure-privacy-probe")
    with tracer.start_as_current_span("failure-privacy-probe") as parent:
        task = queue.enqueue(actor, "triage", {"ticket_id": ticket.id}, uuid4().hex)
        assert queue.dispatch_pending() == 1
        durable_job = queue.job(task.id)
        backend_task_id = durable_job["backend_task_id"]
        assert backend_task_id
        original = runtime.run_configured_triage

        def fail_with_sentinel(*_args, **_kwargs):
            raise ValueError(SENTINEL)

        runtime.run_configured_triage = fail_with_sentinel
        try:
            worker = ServiceWorker(store, retriever, queue)
            assert worker.run_once()
        finally:
            runtime.run_configured_triage = original
        observed = queue.get(actor, task.id)
        assert observed.status.value == "failed"
        assert observed.last_error == "invalid_input"
        trace_id = format(parent.get_span_context().trace_id, "032x")

    with psycopg.connect(queue.dsn) as conn:
        stored_error = conn.execute(
            "SELECT error FROM tasks WHERE task_id=%s", (backend_task_id,)
        ).fetchone()[0]
        outbox = conn.execute(
            "SELECT payload::text FROM event_outbox WHERE task_id=%s",
            (backend_task_id,),
        ).fetchall()
        assert stored_error == "invalid_input"
        assert SENTINEL not in json.dumps([stored_error, outbox])

        # Simulate one pre-fix legacy backend row in the disposable phase database.
        conn.execute(
            "UPDATE tasks SET error=%s WHERE task_id=%s", (SENTINEL, backend_task_id)
        )

    token = issue_demo_token(
        "privacy-probe-reviewer",
        "tenant-a",
        ["agent"],
        ["task:read"],
        secret=os.environ["JWT_SECRET"],
    )
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10) as client:
        denied = client.get("/v1/tasks/" + task.id)
        assert denied.status_code == 401
        response = client.get(
            "/v1/tasks/" + task.id,
            headers={"Authorization": "Bearer " + token},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "failed" and body["error"] == "worker_failure"
        assert SENTINEL not in json.dumps(body)

    flush_ok = flush_telemetry(timeout_millis=5000)
    traces = {"data": None}
    spans = []
    trace_export_observed = False
    if flush_ok:
        traces, spans, trace_export_observed = read_failure_trace(trace_id)
    encoded_trace = json.dumps(traces, ensure_ascii=False)
    assert SENTINEL not in encoded_trace
    assert flush_ok, "telemetry exporter flush did not complete"
    assert trace_export_observed, "failure worker spans were not visible in Jaeger before the bounded deadline"
    print(
        "failure-privacy-service: PASS persisted_code=invalid_input "
        "legacy_api_code=worker_failure trace_spans="
        + str(len(spans))
        + " trace_export_observed="
        + str(trace_export_observed).lower()
        + " exporter_flush="
        + str(flush_ok).lower()
        + " sentinel_absent=true"
    )


if __name__ == "__main__":
    main()
