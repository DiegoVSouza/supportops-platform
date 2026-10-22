import asyncio
import json
import os
from pathlib import Path
import re
import selectors

import httpx2
import psycopg
import uvicorn
from psycopg.rows import dict_row
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.server.auth.provider import AccessToken
from mcp.server.transport_security import TransportSecuritySettings
from supportops_platform.mcp.tools import create_network_mcp_server
from supportops_platform.rag.retrieval import PgVectorHybridRetriever, deterministic_fake_embedding

PG_DSN = "host=127.0.0.1 port=25432 dbname=supportops user=supportops password=local-test-only"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MCP_ISSUER = "https://issuer.example.test/"
MCP_RESOURCE = "http://127.0.0.1:28001/mcp"

class FetchAdapter:
    def __init__(self, connection):
        self.connection = connection
    async def fetch(self, query, *args):
        async with self.connection.cursor(row_factory=dict_row) as cursor:
            parameter_order = [int(index) - 1 for index in re.findall(r"\$(\d+)", query)]
            psycopg_query = re.sub(r"\$\d+", "%s", query)
            await cursor.execute(psycopg_query, tuple(args[index] for index in parameter_order))
            return await cursor.fetchall()

class TestTokenVerifier:
    async def verify_token(self, token):
        tenants = {"tenant-a-token": ("agent-a", "tenant-a"), "tenant-b-token": ("agent-b", "tenant-b")}
        identity = tenants.get(token)
        if identity is None:
            return None
        subject, tenant = identity
        return AccessToken(token=token, client_id="phase008", subject=subject,
            scopes=["billing:read"], resource=MCP_RESOURCE,
            claims={"tenant_id": tenant, "roles": ["agent"]})

async def postgres_gate():
    async with await psycopg.AsyncConnection.connect(PG_DSN) as connection:
        migration = (PROJECT_ROOT / "migrations/002_pgvector_knowledge.sql").read_text(encoding="utf-8")
        for statement in migration.split(";"):
            if statement.strip():
                await connection.execute(statement)
        version = await (await connection.execute("SELECT extversion FROM pg_extension WHERE extname='vector'")).fetchone()
        for tenant, doc_id, title, body in [
            ("tenant-a", "phase008-a", "Refund billing policy", "Refund billing payment reversal for tenant alpha."),
            ("tenant-b", "phase008-b", "Refund billing policy", "Refund billing payment reversal for tenant beta."),
        ]:
            vector = deterministic_fake_embedding(body)
            literal = "[" + ",".join(f"{value:.8f}" for value in vector) + "]"
            await connection.execute(
                "INSERT INTO knowledge_chunks(tenant_id,document_id,title,chunk_id,text,embedding) VALUES(%s,%s,%s,%s,%s,%s::vector) ON CONFLICT DO NOTHING",
                (tenant, doc_id, title, f"{doc_id}:0", body, literal),
            )
        indexes = await (await connection.execute("SELECT indexname FROM pg_indexes WHERE tablename='knowledge_chunks' ORDER BY indexname")).fetchall()
        index_names = {row[0] for row in indexes}
        expected = {"knowledge_chunks_embedding_hnsw", "knowledge_chunks_search_gin"}
        if not expected.issubset(index_names):
            raise AssertionError(f"indexes missing: {expected-index_names}")
        retriever = PgVectorHybridRetriever(FetchAdapter(connection))
        citations = await retriever.search("tenant-a", "refund billing payment", 5)
        if not citations or any(c.document_id != "phase008-a" for c in citations):
            raise AssertionError(f"tenant-filtered retrieval failed: {citations}")
        print(f"pgvector_service: PASS extension={version[0]} indexes={','.join(sorted(expected))} tenant_a_results={len(citations)} tenant_b_excluded=true embeddings=deterministic-fake")

async def mcp_tcp_gate():
    app = create_network_mcp_server(TestTokenVerifier(), MCP_ISSUER, MCP_RESOURCE).streamable_http_app(
        stateless_http=True, json_response=True,
        transport_security=TransportSecuritySettings(allowed_hosts=["127.0.0.1", "127.0.0.1:28001"]))
    service = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=28001, log_level="warning", access_log=False))
    serving = asyncio.create_task(service.serve())
    try:
        for _ in range(100):
            if service.started:
                break
            await asyncio.sleep(0.1)
        if not service.started:
            raise AssertionError("MCP TCP service did not start")
        for token, expected_error in [("tenant-a-token", False), ("tenant-b-token", True)]:
            headers = {"Authorization": f"Bearer {token}"}
            async with httpx2.AsyncClient(transport=httpx2.AsyncHTTPTransport(), base_url="http://127.0.0.1:28001", headers=headers, timeout=10) as http:
                async with streamable_http_client(MCP_RESOURCE, http_client=http) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool("lookup_invoice", {"invoice_id": "inv-a-1"})
                        if bool(result.is_error) != expected_error:
                            raise AssertionError(f"unexpected tenant result for {token}: {result}")
        async with httpx2.AsyncClient(base_url="http://127.0.0.1:28001", timeout=10) as http:
            response = await http.post("/mcp", headers={"Accept": "application/json, text/event-stream"}, json={
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "phase008", "version": "0"}},
            })
        if response.status_code != 401:
            raise AssertionError(f"missing bearer token returned HTTP {response.status_code}")
        print(f"mcp_tcp_auth: PASS endpoint=http://127.0.0.1:28001/mcp tenant_a_allowed=true tenant_b_denied=true missing_token_http={response.status_code} verifier=local-test-double")
    finally:
        service.should_exit = True
        await serving

async def main():
    await postgres_gate()
    await mcp_tcp_gate()

asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
