"""TCP MCP application and bounded authenticated client for the service runtime."""

import asyncio
import json
import os
from urllib.parse import urlsplit

import httpx2
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.server.transport_security import TransportSecuritySettings
from opentelemetry import propagate, trace

from .identity import JWTTokenVerifier
from .tools import create_network_mcp_server


class TracedMCP:
    def __init__(self, app): self.app=app
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http": return await self.app(scope,receive,send)
        headers={k.decode():v.decode() for k,v in scope["headers"]}
        with trace.get_tracer("p05.mcp").start_as_current_span("mcp.request",context=propagate.extract(headers)):
            return await self.app(scope,receive,send)


def settings():
    return (os.environ["MCP_SIGNING_SECRET"],os.environ["MCP_ISSUER"],os.environ["MCP_URL"])


def create_mcp_app():
    from supportops_platform.integrations.observability import configure_telemetry
    configure_telemetry()
    secret,issuer,resource=settings()
    server=create_network_mcp_server(JWTTokenVerifier(secret,issuer,resource),issuer,resource)
    host=urlsplit(resource).netloc
    app=server.streamable_http_app(stateless_http=True,json_response=True,
                                  transport_security=TransportSecuritySettings(allowed_hosts=[host,'127.0.0.1:28001','localhost:28001']))
    return TracedMCP(app)


def call_tool(actor, name, arguments):
    if name not in {"lookup_invoice","lookup_customer","propose_refund"}:
        raise PermissionError("tool is not allowlisted")
    secret,issuer,resource=settings()
    token=JWTTokenVerifier(secret,issuer,resource).issue(actor.subject,actor.tenant_id,actor.roles,actor.scopes)
    carrier={}
    propagate.inject(carrier)
    async def invoke():
        async with httpx2.AsyncClient(headers={**carrier,"Authorization":"Bearer "+token},timeout=10) as http:
            async with streamable_http_client(resource,http_client=http) as (read,write):
                async with ClientSession(read,write) as session:
                    await session.initialize()
                    result=await session.call_tool(name,arguments)
                    if result.is_error: raise PermissionError("MCP tool denied or failed")
                    return json.loads(result.content[0].text)
    with trace.get_tracer("p05.mcp").start_as_current_span("mcp.client."+name):
        return asyncio.run(asyncio.wait_for(invoke(),timeout=15))
