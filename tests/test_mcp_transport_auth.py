from __future__ import annotations

import asyncio

import httpx2
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.server.auth.provider import AccessToken
from mcp.server.transport_security import TransportSecuritySettings

from supportops_platform.mcp.tools import create_network_mcp_server

ISSUER = "https://issuer.example.test/"
RESOURCE = "http://127.0.0.1/mcp"


class TestTokenVerifier:
    async def verify_token(self, token: str) -> AccessToken | None:
        if token == "tenant-a-token":
            return AccessToken(
                token=token,
                client_id="test-client",
                subject="agent-a",
                scopes=["billing:read", "refund:request"],
                resource=RESOURCE,
                claims={"tenant_id": "tenant-a", "roles": ["agent"]},
            )
        if token == "tenant-b-token":
            return AccessToken(
                token=token,
                client_id="test-client",
                subject="agent-b",
                scopes=["billing:read"],
                resource=RESOURCE,
                claims={"tenant_id": "tenant-b", "roles": ["agent"]},
            )
        return None


async def _call_tool(token: str | None, tool: str, arguments: dict[str, object]):
    server = create_network_mcp_server(TestTokenVerifier(), ISSUER, RESOURCE)
    app = server.streamable_http_app(
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(allowed_hosts=["127.0.0.1"]),
    )
    async with app.router.lifespan_context(app):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url="http://127.0.0.1", headers=headers
        ) as http:
            async with streamable_http_client(RESOURCE, http_client=http) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return await session.call_tool(tool, arguments)


def test_network_mcp_uses_verified_transport_tenant() -> None:
    async def run() -> None:
        own = await _call_tool("tenant-a-token", "lookup_invoice", {"invoice_id": "inv-a-1"})
        assert not own.is_error
        foreign = await _call_tool("tenant-b-token", "lookup_invoice", {"invoice_id": "inv-a-1"})
        assert foreign.is_error

    asyncio.run(run())


def test_network_mcp_rejects_missing_bearer_token() -> None:
    async def run() -> None:
        server = create_network_mcp_server(TestTokenVerifier(), ISSUER, RESOURCE)
        app = server.streamable_http_app(
            stateless_http=True,
            json_response=True,
            transport_security=TransportSecuritySettings(allowed_hosts=["127.0.0.1"]),
        )
        async with app.router.lifespan_context(app):
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app), base_url="http://127.0.0.1"
            ) as http:
                response = await http.post(
                    "/mcp",
                    headers={"Accept": "application/json, text/event-stream"},
                    json={
                        "jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-11-25", "capabilities": {},
                            "clientInfo": {"name": "test", "version": "0"},
                        },
                    },
                )
                assert response.status_code == 401
                assert "Bearer" in response.headers.get("www-authenticate", "")

    asyncio.run(run())
