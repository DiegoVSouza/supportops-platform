import asyncio

import pytest
from mcp import Client

from supportops_platform.contracts import Principal
from supportops_platform.mcp.tools import LocalToolGateway, ToolPolicy, create_mock_mcp_server
from supportops_platform.repositories import AuthorizationError


def test_gateway_enforces_scope_and_tenant_for_reads() -> None:
    gateway = LocalToolGateway()
    agent_a = Principal(
        subject="a", tenant_id="tenant-a", roles=frozenset({"agent"}),
        scopes=frozenset({"billing:read", "crm:read", "refund:request"}),
    )
    assert gateway.lookup_invoice(agent_a, "inv-a-1")["status"] == "paid"
    with pytest.raises(AuthorizationError, match="not found"):
        gateway.lookup_invoice(agent_a, "inv-b-1")
    no_billing = Principal(subject="a", tenant_id="tenant-a", roles=frozenset({"agent"}))
    with pytest.raises(AuthorizationError, match="not authorized"):
        gateway.lookup_invoice(no_billing, "inv-a-1")


def test_refund_tool_only_creates_approval_and_checks_bounds() -> None:
    gateway = LocalToolGateway()
    agent = Principal(
        subject="a", tenant_id="tenant-a", roles=frozenset({"agent"}),
        scopes=frozenset({"refund:request"}),
    )
    proposal = gateway.propose_refund(agent, "ticket-1", 5000)
    assert proposal["state"] == "needs_approval"
    assert proposal["effect_performed"] is False
    with pytest.raises(ValueError, match="ceiling"):
        gateway.propose_refund(agent, "ticket-1", 5001)


def test_tool_allowlist_denies_unknown_and_injection_escalation() -> None:
    principal = Principal(
        subject="reader", tenant_id="tenant-a", roles=frozenset({"viewer"}),
        scopes=frozenset({"ticket:read"}),
    )
    for tool in ("delete_customer", "issue_refund", "send_email", "lookup_invoice"):
        with pytest.raises(AuthorizationError):
            ToolPolicy.authorize(principal, tool)


def test_official_mcp_sdk_server_and_client_work_in_memory() -> None:
    principal = Principal(
        subject="agent-a", tenant_id="tenant-a", roles=frozenset({"agent"}),
        scopes=frozenset({"billing:read"}),
    )
    server = create_mock_mcp_server(authenticated_principal=principal)

    async def call() -> dict[str, object]:
        async with Client(server) as client:
            result = await client.call_tool("lookup_invoice", {"invoice_id": "inv-a-1"})
            return result.structured_content

    result = asyncio.run(call())
    assert result == {"invoice_id": "inv-a-1", "amount_cents": 2500, "status": "paid"}


def test_mcp_refund_does_not_perform_effect() -> None:
    principal = Principal(
        subject="agent-a", tenant_id="tenant-a", roles=frozenset({"agent"}),
        scopes=frozenset({"refund:request"}),
    )
    server = create_mock_mcp_server(authenticated_principal=principal)

    async def call() -> dict[str, object]:
        async with Client(server) as client:
            result = await client.call_tool(
                "propose_refund",
                {"ticket_id": "t1", "amount_cents": 100},
            )
            return result.structured_content

    assert asyncio.run(call())["effect_performed"] is False


def test_mcp_server_fails_closed_without_injected_identity() -> None:
    server = create_mock_mcp_server()

    async def call():
        async with Client(server) as client:
            return await client.call_tool("lookup_invoice", {"invoice_id": "inv-a-1"})

    result = asyncio.run(call())
    assert result.is_error is True


def test_mcp_caller_cannot_select_tenant_or_read_other_tenant_invoice() -> None:
    principal = Principal(
        subject="agent-a", tenant_id="tenant-a", roles=frozenset({"agent"}),
        scopes=frozenset({"billing:read"}),
    )
    server = create_mock_mcp_server(authenticated_principal=principal)

    async def call():
        async with Client(server) as client:
            forged = await client.call_tool(
                "lookup_invoice", {"invoice_id": "inv-a-1", "tenant_id": "tenant-b"}
            )
            cross_tenant = await client.call_tool(
                "lookup_invoice", {"invoice_id": "inv-b-1"}
            )
            own_tenant = await client.call_tool(
                "lookup_invoice", {"invoice_id": "inv-a-1"}
            )
            return forged, cross_tenant, own_tenant

    forged, cross_tenant, own_tenant = asyncio.run(call())
    # The SDK may ignore unknown fields; either way caller input cannot select scope.
    assert forged.structured_content["invoice_id"] == "inv-a-1"
    assert cross_tenant.is_error is True
    assert own_tenant.structured_content["invoice_id"] == "inv-a-1"
