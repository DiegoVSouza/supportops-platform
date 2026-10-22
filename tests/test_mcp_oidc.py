from __future__ import annotations

import asyncio
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import threading
import time
from urllib.parse import parse_qs

import httpx2
import pytest
import uvicorn
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.server.transport_security import TransportSecuritySettings

from supportops_platform.mcp.identity import IntrospectionTokenVerifier
from supportops_platform.mcp.runtime import oidc_settings
from supportops_platform.mcp.tools import create_network_mcp_server


class IssuerState:
    def __init__(self):
        self.active = True
        self.response = None
        self.calls = 0


def start_issuer(state: IssuerState):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            state.calls += 1
            expected = "Basic " + base64.b64encode(b"p05-resource:test-secret").decode()
            if self.path != "/introspect" or self.headers.get("Authorization") != expected:
                self.send_error(401)
                return
            length = int(self.headers.get("Content-Length", "0"))
            form = parse_qs(self.rfile.read(length).decode())
            if form.get("token") != ["external-user-token"]:
                self.send_error(400)
                return
            if state.response is not None:
                body = state.response
            elif state.active:
                body = {
                    "active": True,
                    "iss": self.server.issuer,
                    "aud": self.server.audience,
                    "sub": "agent-a",
                    "tenant_id": "tenant-a",
                    "roles": ["agent"],
                    "scope": "billing:read crm:read",
                    "exp": int(time.time()) + 300,
                }
            else:
                body = {"active": False}
            encoded = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    server.issuer = f"http://127.0.0.1:{port}/issuer"
    server.audience = "http://127.0.0.1:28001/mcp"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def verifier_for(state: IssuerState, issuer: str, audience: str):
    return IntrospectionTokenVerifier(
        endpoint=f"http://127.0.0.1:{state.server_port}/introspect",
        client_id="p05-resource",
        client_secret="test-secret",
        issuer=issuer,
        audience=audience,
    )


def test_introspection_accepts_only_active_expected_principal():
    async def run():
        state = IssuerState()
        issuer, _thread = start_issuer(state)
        state.server_port = issuer.server_address[1]
        verifier = verifier_for(state, issuer.issuer, issuer.audience)
        try:
            token = await verifier.verify_token("external-user-token")
            assert token is not None
            assert token.subject == "agent-a"
            assert token.resource == issuer.audience
            assert token.scopes == ["billing:read", "crm:read"]
            assert token.claims == {"tenant_id": "tenant-a", "roles": ["agent"]}
            assert state.calls == 1
        finally:
            issuer.shutdown()
            issuer.server_close()

    asyncio.run(run())


def test_introspection_maps_username_when_rfc7662_response_omits_optional_subject():
    async def run():
        state = IssuerState()
        issuer, _thread = start_issuer(state)
        state.server_port = issuer.server_address[1]
        state.response = {
            "active": True,
            "iss": issuer.issuer,
            "aud": issuer.audience,
            "username": "agent-a",
            "tenant_id": "tenant-a",
            "roles": ["agent"],
            "scope": "billing:read",
            "exp": int(time.time()) + 300,
        }
        verifier = verifier_for(state, issuer.issuer, issuer.audience)
        try:
            accepted = await verifier.verify_token("external-user-token")
            assert accepted is not None and accepted.subject == "agent-a"
        finally:
            issuer.shutdown()
            issuer.server_close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "response",
    [
        {"active": False},
        {"active": True, "iss": "https://wrong.example", "aud": "http://127.0.0.1:28001/mcp", "sub": "a", "tenant_id": "tenant-a", "roles": ["agent"], "scope": "billing:read", "exp": int(time.time()) + 300},
        {"active": True, "iss": "http://issuer.example", "aud": "wrong-resource", "sub": "a", "tenant_id": "tenant-a", "roles": ["agent"], "scope": "billing:read", "exp": int(time.time()) + 300},
        {"active": True, "iss": "http://issuer.example", "aud": "http://127.0.0.1:28001/mcp", "sub": "a", "tenant_id": "tenant-a", "roles": "agent", "scope": "billing:read", "exp": int(time.time()) + 300},
        {"active": True, "iss": "http://issuer.example", "aud": "http://127.0.0.1:28001/mcp", "sub": "a", "tenant_id": "tenant-a", "roles": ["agent"], "scope": "billing:read", "exp": int(time.time()) - 1},
    ],
)
def test_introspection_fails_closed_for_inactive_or_invalid_claims(response):
    async def run():
        state = IssuerState()
        state.response = response
        issuer, _thread = start_issuer(state)
        state.server_port = issuer.server_address[1]
        verifier = verifier_for(state, issuer.issuer, issuer.audience)
        try:
            assert await verifier.verify_token("external-user-token") is None
        finally:
            issuer.shutdown()
            issuer.server_close()

    asyncio.run(run())


def test_introspection_fails_closed_when_issuer_is_unreachable():
    async def run():
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        verifier = IntrospectionTokenVerifier(
            endpoint=f"http://127.0.0.1:{port}/introspect",
            client_id="p05-resource",
            client_secret="test-secret",
            issuer="http://issuer.example",
            audience="http://127.0.0.1:28001/mcp",
        )
        assert await verifier.verify_token("external-user-token") is None

    asyncio.run(run())


def test_remote_introspection_endpoint_requires_https():
    with pytest.raises(ValueError, match="must use HTTPS"):
        IntrospectionTokenVerifier(
            endpoint="http://auth.example.test/introspect",
            client_id="p05-resource",
            client_secret="test-secret",
            issuer="https://auth.example.test/issuer",
            audience="https://mcp.example.test/mcp",
        )


def test_oidc_runtime_configuration_requires_all_values(monkeypatch):
    names = (
        "MCP_OIDC_INTROSPECTION_URL",
        "MCP_OIDC_CLIENT_ID",
        "MCP_OIDC_CLIENT_SECRET",
        "MCP_OIDC_ISSUER",
        "MCP_OIDC_AUDIENCE",
    )
    for name in names:
        monkeypatch.delenv(name, raising=False)
    assert oidc_settings() is None
    monkeypatch.setenv(names[0], "https://issuer.example.test/introspect")
    with pytest.raises(RuntimeError, match="requires endpoint, client credentials"):
        oidc_settings()


def test_mcp_tcp_denies_token_after_issuer_revokes_it():
    async def run():
        state = IssuerState()
        issuer, _issuer_thread = start_issuer(state)
        state.server_port = issuer.server_address[1]
        resource_socket = socket.socket()
        resource_socket.bind(("127.0.0.1", 0))
        resource_socket.listen()
        resource_port = resource_socket.getsockname()[1]
        resource = f"http://127.0.0.1:{resource_port}/mcp"
        issuer.audience = resource
        verifier = verifier_for(state, issuer.issuer, resource)
        mcp_server = create_network_mcp_server(verifier, issuer.issuer, resource)
        app = mcp_server.streamable_http_app(
            stateless_http=True,
            json_response=True,
            transport_security=TransportSecuritySettings(
                allowed_hosts=[f"127.0.0.1:{resource_port}"]
            ),
        )
        uv_server = uvicorn.Server(uvicorn.Config(app, log_level="critical", lifespan="on"))
        thread = threading.Thread(
            target=lambda: asyncio.run(uv_server.serve(sockets=[resource_socket])), daemon=True
        )
        thread.start()
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                try:
                    response = httpx2.get(resource, timeout=0.1)
                    if response.status_code in {404, 405, 401}:
                        break
                except httpx2.HTTPError:
                    time.sleep(0.05)
            else:
                raise AssertionError("MCP TCP server did not start")

            async with httpx2.AsyncClient(headers={"Authorization": "Bearer external-user-token"}) as http:
                async with streamable_http_client(resource, http_client=http) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool("lookup_invoice", {"invoice_id": "inv-a-1"})
                        assert not result.is_error
            assert state.calls >= 2  # initialization and tool request are independently introspected

            state.active = False
            response = httpx2.post(
                resource,
                headers={"Authorization": "Bearer external-user-token", "Accept": "application/json, text/event-stream"},
                json={"jsonrpc": "2.0", "id": 9, "method": "initialize", "params": {
                    "protocolVersion": "2025-11-25", "capabilities": {},
                    "clientInfo": {"name": "revoked-token-test", "version": "1"},
                }},
                timeout=5,
            )
            assert response.status_code == 401
            assert state.calls >= 3
        finally:
            uv_server.should_exit = True
            thread.join(timeout=5)
            resource_socket.close()
            issuer.shutdown()
            issuer.server_close()

    asyncio.run(run())
