from datetime import timedelta

from fastapi.testclient import TestClient

from supportops_platform.auth.jwt import issue_demo_token
from supportops_platform.api.app import create_app

TEST_SECRET = "p05-test-signing-secret-with-32-bytes-minimum"
IDENTITIES = {
    "tenant-a-agent": ("agent-a", "tenant-a", ["agent"], ["ticket:read", "ticket:write", "refund:request", "task:read", "task:write", "feedback:write", "triage:run"]),
    "tenant-a-approver": ("approver-a", "tenant-a", ["approver"], ["ticket:read", "approval:decide", "task:read"]),
    "tenant-a-reader": ("reader-a", "tenant-a", ["viewer"], ["ticket:read"]),
    "tenant-a-dual": ("agent-a", "tenant-a", ["agent", "approver"], ["ticket:read", "ticket:write", "refund:request", "approval:decide"]),
    "tenant-b-agent": ("agent-b", "tenant-b", ["agent"], ["ticket:read", "ticket:write", "task:read", "task:write"]),
}


def auth_headers(identity: str) -> dict[str, str]:
    subject, tenant, roles, scopes = IDENTITIES[identity]
    token = issue_demo_token(subject, tenant, roles, scopes, secret=TEST_SECRET)
    return {"Authorization": f"Bearer {token}"}


def client() -> TestClient:
    return TestClient(create_app(token_secret=TEST_SECRET))


def create_ticket(api: TestClient, token: str = "tenant-a-agent") -> str:
    response = api.post(
        "/v1/tickets",
        headers=auth_headers(token),
        json={"customer_id": "c-1", "subject": "Invoice question", "body": "Need help"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_health_is_fake_by_default_and_openapi_is_versioned() -> None:
    api = client()
    assert api.get("/health").json()["llm_mode"] == "fake"
    assert api.get("/healthz").json()["status"] == "ok"
    schema = api.get("/openapi.json").json()
    assert schema["info"]["version"] == "0.3.0"
    assert "/healthz" in schema["paths"]
    assert "/health" not in schema["paths"]
    assert "/v1/tickets/{ticket_id}/refund-approvals" in schema["paths"]
    assert "HTTPBearer" in schema["components"]["securitySchemes"]
    assert "/v1/tickets/{ticket_id}/approve" in schema["paths"]
    assert "/v1/feedback" in schema["paths"]
    assert "/v1/tickets/{ticket_id}/feedback" in schema["paths"]
    assert "/v1/tasks/{task_id}" in schema["paths"]


def test_authentication_and_scope_fail_closed() -> None:
    api = client()
    assert api.get("/v1/tickets").status_code == 401
    assert api.get("/v1/tickets", headers={"Authorization": "Bearer unknown"}).status_code == 401
    assert api.post(
        "/v1/tickets",
        headers=auth_headers("tenant-b-agent"),
        json={"customer_id": "c", "subject": "s", "body": "b"},
    ).status_code == 201
    assert api.post(
        "/v1/tickets",
        headers=auth_headers("tenant-a-reader"),
        json={"customer_id": "c", "subject": "s", "body": "b"},
    ).status_code == 403


def test_invalid_signature_and_expired_jwt_are_rejected() -> None:
    api = client()
    expired = issue_demo_token(
        "agent-a", "tenant-a", ["agent"], ["ticket:read"],
        secret=TEST_SECRET, lifetime=timedelta(seconds=-1),
    )
    wrong_key = issue_demo_token(
        "agent-a", "tenant-a", ["agent"], ["ticket:read"],
        secret="another-test-signing-secret-at-least-32-bytes",
    )
    for token in (expired, wrong_key, "not-a-jwt"):
        response = api.get("/v1/tickets", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


def test_tenant_cannot_read_another_tenant_ticket() -> None:
    api = client()
    ticket_id = create_ticket(api)
    response = api.get(
        f"/v1/tickets/{ticket_id}", headers=auth_headers("tenant-b-agent")
    )
    assert response.status_code == 404


def test_refund_pauses_for_approval_and_is_idempotent() -> None:
    api = client()
    ticket_id = create_ticket(api)
    headers = {**auth_headers("tenant-a-agent"), "Idempotency-Key": "refund-1"}
    payload = {"amount_cents": 2500}
    first = api.post(f"/v1/tickets/{ticket_id}/refund-approvals", headers=headers, json=payload)
    second = api.post(f"/v1/tickets/{ticket_id}/refund-approvals", headers=headers, json=payload)
    assert first.status_code == second.status_code == 202
    assert first.json()["state"] == "pending"
    assert first.json()["id"] == second.json()["id"]


def test_refund_boundary_and_reused_key_conflict() -> None:
    api = client()
    ticket_id = create_ticket(api)
    url = f"/v1/tickets/{ticket_id}/refund-approvals"
    headers = {**auth_headers("tenant-a-agent"), "Idempotency-Key": "key-1"}
    assert api.post(url, headers=headers, json={"amount_cents": 5001}).status_code == 422
    assert api.post(url, headers=headers, json={"amount_cents": 1000}).status_code == 202
    assert api.post(url, headers=headers, json={"amount_cents": 2000}).status_code == 422


def test_only_same_tenant_approver_can_decide_once() -> None:
    api = client()
    ticket_id = create_ticket(api)
    result = api.post(
        f"/v1/tickets/{ticket_id}/refund-approvals",
        headers={**auth_headers("tenant-a-agent"), "Idempotency-Key": "key-2"},
        json={"amount_cents": 100},
    ).json()
    path = f"/v1/approvals/{result['id']}/decision"
    denied = api.post(
        path,
        headers=auth_headers("tenant-b-agent"),
        json={"decision": "approved"},
    )
    assert denied.status_code == 403
    approver_headers = auth_headers("tenant-a-approver")
    assert api.post(path, headers=approver_headers, json={"decision": "approved"}).status_code == 200
    assert api.post(path, headers=approver_headers, json={"decision": "approved"}).status_code == 409


def test_ticket_approval_compatibility_route_is_tenant_and_ticket_scoped() -> None:
    api = client()
    ticket_id = create_ticket(api)
    other_ticket_id = create_ticket(api)
    approval = api.post(
        f"/v1/tickets/{ticket_id}/refund-approvals",
        headers={**auth_headers("tenant-a-agent"), "Idempotency-Key": "compat-approval"},
        json={"amount_cents": 250},
    ).json()
    route = f"/v1/tickets/{ticket_id}/approve"
    decision = {"approval_id": approval["id"], "decision": "approved"}
    assert api.post(route, headers=auth_headers("tenant-a-agent"), json=decision).status_code == 403
    assert api.post(
        f"/v1/tickets/{other_ticket_id}/approve",
        headers=auth_headers("tenant-a-approver"), json=decision,
    ).status_code == 403
    result = api.post(
        route, headers=auth_headers("tenant-a-approver"), json=decision
    )
    assert result.status_code == 200
    assert result.json() == {"id": approval["id"], "state": "approved"}


def test_ticket_approval_route_defaults_to_approving_the_unique_pending_request() -> None:
    api = client()
    ticket_id = create_ticket(api)
    requested = api.post(
        f"/v1/tickets/{ticket_id}/refund-approvals",
        headers={**auth_headers("tenant-a-agent"), "Idempotency-Key": "approve-by-ticket"},
        json={"amount_cents": 300},
    )
    assert requested.status_code == 202
    response = api.post(
        f"/v1/tickets/{ticket_id}/approve", headers=auth_headers("tenant-a-approver"), json={}
    )
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "approved"


def test_refund_requester_cannot_approve_their_own_request() -> None:
    api = client()
    ticket_id = create_ticket(api)
    requested = api.post(
        f"/v1/tickets/{ticket_id}/refund-approvals",
        headers={**auth_headers("tenant-a-dual"), "Idempotency-Key": "dual-control"},
        json={"amount_cents": 250},
    ).json()
    path = f"/v1/approvals/{requested['id']}/decision"
    assert api.post(
        path, headers=auth_headers("tenant-a-dual"), json={"decision": "approved"}
    ).status_code == 403
    assert api.post(
        path, headers=auth_headers("tenant-a-approver"), json={"decision": "approved"}
    ).status_code == 200


def test_triage_returns_only_tenant_scoped_rag_citations() -> None:
    from supportops_platform.rag.retrieval import KnowledgeDocument, LocalRetriever

    retriever = LocalRetriever([
        KnowledgeDocument("tenant-a-refunds", "tenant-a", "Refund policy", "Refund requests need supervisor review."),
        KnowledgeDocument("tenant-b-refunds", "tenant-b", "Private refund policy", "Refunds are automatic."),
    ])
    api = TestClient(create_app(token_secret=TEST_SECRET, retriever=retriever))
    ticket_id = create_ticket(api)
    response = api.post(f"/v1/tickets/{ticket_id}/triage", headers=auth_headers("tenant-a-agent"))
    assert response.status_code == 200
    body = response.json()
    assert body["llm_mode"] == "fake"
    assert [citation["document_id"] for citation in body["citations"]] == ["tenant-a-refunds"]
    assert any("tenant-a-refunds" in step["detail"] for step in body["trace"])
    assert api.post(
        f"/v1/tickets/{ticket_id}/triage", headers=auth_headers("tenant-a-reader")
    ).status_code == 403


def test_rate_limit_is_enforced() -> None:
    api = TestClient(create_app(requests_per_minute=1))
    assert api.get("/health").status_code == 200
    assert api.get("/health").status_code == 429


def test_request_body_size_limit_is_enforced() -> None:
    api = client()
    response = api.post(
        "/v1/tickets",
        headers={**auth_headers("tenant-a-agent"), "Content-Length": "1000001"},
        content=b"{}",
    )
    assert response.status_code == 413


def test_async_triage_task_is_tenant_scoped_and_idempotent() -> None:
    api = client()
    ticket_id = create_ticket(api)
    headers = {**auth_headers("tenant-a-agent"), "Idempotency-Key": "triage-1"}
    payload = {"ticket_id": ticket_id}
    first = api.post("/v1/tasks", headers=headers, json=payload)
    duplicate = api.post("/v1/tasks", headers=headers, json=payload)
    assert first.status_code == duplicate.status_code == 202
    assert first.json()["status"] == "queued"
    assert first.json()["id"] == duplicate.json()["id"]
    assert api.get(
        f"/v1/tasks/{first.json()['id']}",
        headers=auth_headers("tenant-b-agent"),
    ).status_code == 404


def test_feedback_is_tenant_scoped_bounded_and_absent_from_metrics() -> None:
    api = client()
    ticket_id = create_ticket(api)
    accepted = api.post(
        f"/v1/tickets/{ticket_id}/feedback",
        headers=auth_headers("tenant-a-agent"),
        json={"rating": 5, "comment": "Worked well; user@example.test"},
    )
    assert accepted.status_code == 201
    wrong_tenant = api.post(
        f"/v1/tickets/{ticket_id}/feedback",
        headers=auth_headers("tenant-b-agent"),
        json={"rating": 1, "comment": "No"},
    )
    assert wrong_tenant.status_code == 403
    assert api.post(
        f"/v1/tickets/{ticket_id}/feedback",
        headers=auth_headers("tenant-a-agent"),
        json={"rating": 6, "comment": "out of bounds"},
    ).status_code == 422
    metrics = api.get("/metrics")
    assert metrics.status_code == 200
    assert "supportops_http_requests_total" in metrics.text
    assert ticket_id not in metrics.text
    assert "user@example.test" not in metrics.text


def test_top_level_feedback_route_is_tenant_scoped() -> None:
    api = client()
    ticket_id = create_ticket(api)
    accepted = api.post(
        "/v1/feedback",
        headers=auth_headers("tenant-a-agent"),
        json={"ticket_id": ticket_id, "rating": 4, "comment": "Resolved"},
    )
    assert accepted.status_code == 201
    assert accepted.json()["status"] == "recorded"
    denied = api.post(
        "/v1/feedback",
        headers=auth_headers("tenant-b-agent"),
        json={"ticket_id": ticket_id, "rating": 4},
    )
    assert denied.status_code == 403
