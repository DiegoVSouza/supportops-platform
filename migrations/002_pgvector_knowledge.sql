-- PostgreSQL 16+ with pgvector 0.8.7. Apply only through the configured migrator.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    tenant_id text NOT NULL,
    document_id text NOT NULL,
    title text NOT NULL,
    chunk_id text NOT NULL,
    text text NOT NULL,
    embedding vector(32) NOT NULL,
    search_vector tsvector GENERATED ALWAYS AS
        (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(text, ''))) STORED,
    PRIMARY KEY (tenant_id, document_id, chunk_id)
);

CREATE INDEX IF NOT EXISTS knowledge_chunks_embedding_hnsw
    ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS knowledge_chunks_search_gin
    ON knowledge_chunks USING gin (search_vector);
