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
    server = create_mock_mcp_server()

    async def call() -> dict[str, object]:
        async with Client(server) as client:
            result = await client.call_tool(
                "lookup_invoice", {"invoice_id": "inv-a-1", "tenant_id": "tenant-a"}
            )
            return result.structured_content

    result = asyncio.run(call())
    assert result == {"invoice_id": "inv-a-1", "amount_cents": 2500, "status": "paid"}


def test_mcp_refund_does_not_perform_effect() -> None:
    server = create_mock_mcp_server()

    async def call() -> dict[str, object]:
        async with Client(server) as client:
            result = await client.call_tool(
                "propose_refund",
                {"ticket_id": "t1", "tenant_id": "tenant-a", "amount_cents": 100},
            )
            return result.structured_content

    assert asyncio.run(call())["effect_performed"] is False
