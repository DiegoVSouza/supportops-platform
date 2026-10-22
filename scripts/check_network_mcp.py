"""Check signed MCP access and tenant denial from the API over Compose TCP."""

import asyncio
import os

import httpx
import httpx2
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

from supportops_platform.mcp.identity import JWTTokenVerifier


async def check_tenant(endpoint, verifier, tenant, denied):
    bearer = verifier.issue("network-test-" + tenant, tenant, ["agent"], ["billing:read"])
    async with httpx2.AsyncClient(headers={"Authorization": "Bearer " + bearer}) as client:
        async with streamable_http_client(endpoint, http_client=client) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("lookup_invoice", {"invoice_id": "inv-a-1"})
                assert result.is_error is denied, f"unexpected tool result for {tenant}"


async def main():
    endpoint = os.environ["MCP_URL"]
    response = httpx.post(
        endpoint,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "service-check", "version": "1"},
            },
        },
        headers={"Accept": "application/json, text/event-stream"},
        timeout=10,
    )
    assert response.status_code == 401, f"unauthenticated MCP returned {response.status_code}"

    verifier = JWTTokenVerifier(
        os.environ["MCP_SIGNING_SECRET"],
        os.environ["MCP_ISSUER"],
        endpoint,
    )
    await check_tenant(endpoint, verifier, "tenant-a", False)
    await check_tenant(endpoint, verifier, "tenant-b", True)
    print("network_mcp_auth=PASS; unauthenticated and cross-tenant access denied")


if __name__ == "__main__":
    asyncio.run(main())
