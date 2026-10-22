"""Native asyncpg hybrid query and bounded PostgreSQL ingestion; no placeholder shim."""

import asyncio
import asyncpg
import psycopg
from supportops_obs.instrumentation import traced_operation

from .retrieval import PgVectorHybridRetriever, PgVectorHybridSQL, chunk_document


class PostgresRetriever:
    def __init__(self, dsn):
        self.dsn = dsn

    @traced_operation("database", name="knowledge.ingest")
    def ingest(self, document):
        chunks = chunk_document(document)
        with psycopg.connect(self.dsn) as conn:
            conn.execute("DELETE FROM knowledge_chunks WHERE tenant_id=%s AND document_id=%s",
                         (document.tenant_id, document.document_id))
            for chunk in chunks:
                conn.execute("INSERT INTO knowledge_chunks(tenant_id,document_id,title,chunk_id,text,embedding) "
                             "VALUES(%s,%s,%s,%s,%s,%s::vector)",
                             (chunk.tenant_id, chunk.document_id, chunk.title, chunk.chunk_id,
                              chunk.text, PgVectorHybridSQL.vector_literal(chunk.embedding)))
        return len(chunks)

    @traced_operation("database", name="knowledge.hybrid_search")
    def search(self, tenant_id, query, top_k=3):
        async def retrieve():
            conn = await asyncpg.connect(self.dsn, timeout=5)
            try: return await PgVectorHybridRetriever(conn).search(tenant_id, query, top_k)
            finally: await conn.close()
        return asyncio.run(retrieve())
