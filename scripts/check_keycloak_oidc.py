"""Exercise Keycloak token issuance, MCP authentication, and provider revocation locally."""

import asyncio
import os
import socket
import sys
import threading
import time

import httpx2
import uvicorn
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.server.transport_security import TransportSecuritySettings

from supportops_platform.mcp.identity import IntrospectionTokenVerifier
from supportops_platform.mcp.tools import create_network_mcp_server


BASE_URL = os.getenv("P05_KEYCLOAK_URL", "http://127.0.0.1:28180").rstrip("/")
REALM = "p05-local"
CLIENT_ID = "p05-resource"
CLIENT_SECRET = "p05-local-resource-secret-only"
ISSUER = f"{BASE_URL}/realms/{REALM}"
ENDPOINT = f"{ISSUER}/protocol/openid-connect/token/introspect"
RESOURCE = "http://127.0.0.1:28181/mcp"


async def check():
    server_socket = socket.socket()
    try:
        server_socket.bind(("127.0.0.1", 28181))
    except OSError as exc:
        server_socket.close()
        raise RuntimeError("isolated MCP test port 28181 is unavailable") from exc
    server_socket.listen()
    uv_server = None
    server_thread = None
    try:
        async with httpx2.AsyncClient(timeout=5) as client:
            token_response = await client.post(
                f"{ISSUER}/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "username": "agent-a",
                    "password": "p05-test-password-only",
                    "scope": "openid billing:read",
                },
            )
            if token_response.is_error:
                body = token_response.json()
                raise RuntimeError(
                    f"Keycloak token issuance failed: {body.get('error', 'unknown')} "
                    f"({body.get('error_description', 'no description')})"
                )
            token = token_response.json()["access_token"]
            verifier = IntrospectionTokenVerifier(
                endpoint=ENDPOINT,
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                issuer=ISSUER,
                audience=RESOURCE,
            )
            accepted = await verifier.verify_token(token)
            if accepted is None:
                diagnostic = await client.post(
                    ENDPOINT,
                    data={"token": token, "token_type_hint": "access_token"},
                    auth=(CLIENT_ID, CLIENT_SECRET),
                )
                diagnostic.raise_for_status()
                body = diagnostic.json()
                raise RuntimeError(
                    "Keycloak token did not pass configured MCP claim checks; "
                    f"introspection_http={diagnostic.status_code}, "
                    f"error={body.get('error', 'unknown')}, "
                    f"description={body.get('error_description', 'no description')}"
                )
            if accepted.subject != "agent-a" or accepted.claims != {
                "tenant_id": "tenant-a",
                "roles": ["agent"],
            }:
                raise RuntimeError("Keycloak introspection claims did not map to the P05 principal")
            print("PASS Keycloak issued token; introspection accepted expected principal, tenant, role, audience, and scope")

            mcp_server = create_network_mcp_server(verifier, ISSUER, RESOURCE)
            app = mcp_server.streamable_http_app(
                stateless_http=True,
                json_response=True,
                transport_security=TransportSecuritySettings(
                    allowed_hosts=["127.0.0.1:28181"]
                ),
            )
            uv_server = uvicorn.Server(
                uvicorn.Config(app, log_level="critical", lifespan="on")
            )
            server_thread = threading.Thread(
                target=lambda: asyncio.run(uv_server.serve(sockets=[server_socket])),
                daemon=True,
            )
            server_thread.start()
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                try:
                    probe = await client.get(RESOURCE, timeout=0.2)
                    if probe.status_code in {401, 404, 405}:
                        break
                except httpx2.HTTPError:
                    await asyncio.sleep(0.1)
            else:
                raise RuntimeError("loopback MCP test server did not start")

            async with httpx2.AsyncClient(
                headers={"Authorization": f"Bearer {token}"}, timeout=5
            ) as authenticated_client:
                async with streamable_http_client(
                    RESOURCE, http_client=authenticated_client
                ) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(
                            "lookup_invoice", {"invoice_id": "inv-a-1"}
                        )
                        if result.is_error:
                            raise RuntimeError("Keycloak bearer could not call the MCP read tool")
            print("PASS Keycloak bearer called lookup_invoice over MCP Streamable HTTP TCP")

            revoke_response = await client.post(
                f"{ISSUER}/protocol/openid-connect/revoke",
                data={
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "token": token,
                    "token_type_hint": "access_token",
                },
            )
            revoke_response.raise_for_status()

            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if await verifier.verify_token(token) is None:
                    break
                await asyncio.sleep(0.25)
            else:
                raise RuntimeError("Keycloak continued to report the revoked token as active")

            denied = await client.post(
                RESOURCE,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json, text/event-stream",
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-11-25",
                        "capabilities": {},
                        "clientInfo": {"name": "keycloak-revocation-test", "version": "1"},
                    },
                },
            )
            if denied.status_code != 401:
                raise RuntimeError("MCP did not reject the Keycloak bearer after revocation")
            print("PASS Keycloak revoked token became inactive and MCP returned HTTP 401")
    finally:
        if uv_server is not None:
            uv_server.should_exit = True
        if server_thread is not None:
            server_thread.join(timeout=5)
        server_socket.close()


if __name__ == "__main__":
    try:
        asyncio.run(check())
    except Exception as exc:
        print(f"FAIL {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
