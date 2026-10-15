#!/usr/bin/env python3
"""Run the local API and retrieval demonstration without network/provider calls."""

from fastapi.testclient import TestClient

from supportops_platform.async_tasks.queue import EffectLedger, FakeWorker
from supportops_platform.api.app import create_app
from supportops_platform.auth.jwt import issue_demo_token
from supportops_platform.rag.retrieval import KnowledgeDocument, LocalRetriever

retriever = LocalRetriever(
    [KnowledgeDocument("refund-policy", "demo-tenant", "Refund policy", "Refund requests require approval.")]
)
application = create_app(retriever=retriever)
secret = application.state.token_secret
agent = issue_demo_token(
    "demo-agent", "demo-tenant", ["agent"],
    ["ticket:read", "ticket:write", "refund:request", "task:read", "task:write", "triage:run"],
    secret=secret,
)
approver = issue_demo_token(
    "demo-approver", "demo-tenant", ["approver"], ["ticket:read", "approval:decide"], secret=secret,
)
client = TestClient(application)
agent_headers = {"Authorization": f"Bearer {agent}"}
print("health:", client.get("/health").json())
ticket = client.post(
    "/v1/tickets", headers=agent_headers,
    json={"customer_id": "demo-customer", "subject": "Refund request", "body": "Please review a refund."},
)
ticket.raise_for_status()
ticket_id = ticket.json()["id"]
task = client.post(
    "/v1/tasks", headers={**agent_headers, "Idempotency-Key": "demo-triage"},
    json={"ticket_id": ticket_id},
)
task.raise_for_status()
triage = client.post(f"/v1/tickets/{ticket_id}/triage", headers=agent_headers)
triage.raise_for_status()
worker = FakeWorker(application.state.task_queue, "demo-worker", EffectLedger())
completed_task = worker.run_once()
approval = client.post(
    f"/v1/tickets/{ticket_id}/refund-approvals",
    headers={**agent_headers, "Idempotency-Key": "demo-refund"},
    json={"amount_cents": 1200},
)
approval.raise_for_status()
decision = client.post(
    f"/v1/approvals/{approval.json()['id']}/decision",
    headers={"Authorization": f"Bearer {approver}"},
    json={"decision": "approved"},
)
decision.raise_for_status()
print("ticket:", ticket_id)
print("task:", {"id": completed_task.id, "status": completed_task.status.value})
print("triage:", {"decision": triage.json()["decision"]["action"], "citations": [c["document_id"] for c in triage.json()["citations"]]})
print("refund approval:", decision.json(), "external_effect_performed=false")
print("demo_mode=fake; provider_calls=0; external_effects=0")
