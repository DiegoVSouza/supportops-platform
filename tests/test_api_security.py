from fastapi.testclient import TestClient

from supportops_platform.api.app import create_app


def client() -> TestClient:
    return TestClient(create_app())


def create_ticket(api: TestClient, token: str = "tenant-a-agent") -> str:
    response = api.post(
        "/v1/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={"customer_id": "c-1", "subject": "Invoice question", "body": "Need help"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_health_is_fake_by_default_and_openapi_is_versioned() -> None:
    api = client()
    assert api.get("/health").json()["llm_mode"] == "fake"
    schema = api.get("/openapi.json").json()
    assert schema["info"]["version"] == "0.1.0"
    assert "/v1/tickets/{ticket_id}/refund-approvals" in schema["paths"]


def test_authentication_and_scope_fail_closed() -> None:
    api = client()
    assert api.get("/v1/tickets").status_code == 401
    assert api.get("/v1/tickets", headers={"Authorization": "Bearer unknown"}).status_code == 401
    assert api.post(
        "/v1/tickets",
        headers={"Authorization": "Bearer tenant-b-agent"},
        json={"customer_id": "c", "subject": "s", "body": "b"},
    ).status_code == 201
    assert api.post(
        "/v1/tickets",
        headers={"Authorization": "Bearer tenant-a-reader"},
        json={"customer_id": "c", "subject": "s", "body": "b"},
    ).status_code == 403


def test_tenant_cannot_read_another_tenant_ticket() -> None:
    api = client()
    ticket_id = create_ticket(api)
    response = api.get(
        f"/v1/tickets/{ticket_id}", headers={"Authorization": "Bearer tenant-b-agent"}
    )
    assert response.status_code == 404


def test_refund_pauses_for_approval_and_is_idempotent() -> None:
    api = client()
    ticket_id = create_ticket(api)
    headers = {"Authorization": "Bearer tenant-a-agent", "Idempotency-Key": "refund-1"}
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
    headers = {"Authorization": "Bearer tenant-a-agent", "Idempotency-Key": "key-1"}
    assert api.post(url, headers=headers, json={"amount_cents": 5001}).status_code == 422
    assert api.post(url, headers=headers, json={"amount_cents": 1000}).status_code == 202
    assert api.post(url, headers=headers, json={"amount_cents": 2000}).status_code == 422


def test_only_same_tenant_approver_can_decide_once() -> None:
    api = client()
    ticket_id = create_ticket(api)
    result = api.post(
        f"/v1/tickets/{ticket_id}/refund-approvals",
        headers={"Authorization": "Bearer tenant-a-agent", "Idempotency-Key": "key-2"},
        json={"amount_cents": 100},
    ).json()
    path = f"/v1/approvals/{result['id']}/decision"
    denied = api.post(
        path,
        headers={"Authorization": "Bearer tenant-b-agent"},
        json={"decision": "approved"},
    )
    assert denied.status_code == 403
    approver_headers = {"Authorization": "Bearer tenant-a-approver"}
    assert api.post(path, headers=approver_headers, json={"decision": "approved"}).status_code == 200
    assert api.post(path, headers=approver_headers, json={"decision": "approved"}).status_code == 409


def test_rate_limit_is_enforced() -> None:
    api = TestClient(create_app(requests_per_minute=1))
    assert api.get("/health").status_code == 200
    assert api.get("/health").status_code == 429


def test_request_body_size_limit_is_enforced() -> None:
    api = client()
    response = api.post(
        "/v1/tickets",
        headers={"Authorization": "Bearer tenant-a-agent", "Content-Length": "1000001"},
        content=b"{}",
    )
    assert response.status_code == 413
