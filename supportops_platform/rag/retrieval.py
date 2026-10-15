"""Local bounded lexical retrieval. Retrieved text remains untrusted input."""

from __future__ import annotations

import re
import hashlib
import math
from dataclasses import dataclass

from supportops_platform.contracts import Citation, ContractError
from supportops_platform.integrations.toolkit import safe_retrieval_query

TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
MAX_DOCUMENTS = 100
MAX_DOCUMENT_BYTES = 64_000
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
EMBEDDING_DIMENSIONS = 32


def deterministic_fake_embedding(text: str) -> tuple[float, ...]:
    """Stable hashed-token vector for control-flow tests; not a semantic model."""
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for token in (part.lower() for part in TOKEN.findall(text)):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % EMBEDDING_DIMENSIONS
        vector[index] += 1.0 if digest[2] & 1 else -1.0
    norm = math.sqrt(sum(value * value for value in vector))
    return tuple(value / norm for value in vector) if norm else tuple(vector)


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != EMBEDDING_DIMENSIONS or len(right) != EMBEDDING_DIMENSIONS:
        raise ContractError("embedding dimension mismatch")
    return sum(a * b for a, b in zip(left, right, strict=True))


class PgVectorHybridSQL:
    """Versioned SQL contract for PostgreSQL pgvector + full-text candidate ranking."""

    QUERY = """SELECT tenant_id, document_id, title, chunk_id, text,
       0.5 * (1 - (embedding <=> $1::vector)) +
       0.5 * ts_rank_cd(search_vector, websearch_to_tsquery('simple', $2)) AS score
FROM knowledge_chunks
WHERE tenant_id = $3 AND search_vector @@ websearch_to_tsquery('simple', $2)
ORDER BY score DESC, document_id, chunk_id
LIMIT $4"""

    @staticmethod
    def vector_literal(embedding: tuple[float, ...]) -> str:
        if len(embedding) != EMBEDDING_DIMENSIONS or not all(math.isfinite(x) for x in embedding):
            raise ContractError("embedding must contain 32 finite dimensions")
        return "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"


class PgVectorHybridRetriever:
    """Asyncpg-compatible adapter; callers inject a connection and own its lifecycle."""

    def __init__(self, connection: object):
        self.connection = connection

    async def search(self, tenant_id: str, query: str, top_k: int = 3) -> list[Citation]:
        if not tenant_id:
            raise ContractError("tenant is required")
        if not 1 <= top_k <= 10:
            raise ContractError("top_k must be between 1 and 10")
        try:
            safe_query = safe_retrieval_query(query)
        except ValueError as exc:
            raise ContractError(str(exc)) from exc
        if not safe_query.strip():
            return []
        fetch = getattr(self.connection, "fetch", None)
        if fetch is None:
            raise ContractError("PostgreSQL connection must provide async fetch")
        rows = await fetch(
            PgVectorHybridSQL.QUERY,
            PgVectorHybridSQL.vector_literal(deterministic_fake_embedding(safe_query)),
            safe_query,
            tenant_id,
            top_k,
        )
        citations: list[Citation] = []
        for row in rows:
            if row["tenant_id"] != tenant_id:
                raise ContractError("database returned a cross-tenant knowledge row")
            citations.append(
                Citation(
                    document_id=row["document_id"],
                    title=row["title"],
                    chunk_id=row["chunk_id"],
                    text=row["text"],
                    score=float(row["score"]),
                )
            )
        return citations


@dataclass(frozen=True, slots=True)
class KnowledgeDocument:
    document_id: str
    tenant_id: str
    title: str
    text: str


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    document_id: str
    tenant_id: str
    title: str
    chunk_id: str
    text: str
    tokens: tuple[str, ...]
    embedding: tuple[float, ...]


def chunk_document(document: KnowledgeDocument) -> list[DocumentChunk]:
    if not document.document_id or not document.tenant_id or not document.title:
        raise ContractError("document identifiers and title are required")
    if len(document.text.encode("utf-8")) > MAX_DOCUMENT_BYTES:
        raise ContractError("document exceeds 64000-byte ingestion limit")
    text = document.text.strip()
    if not text:
        raise ContractError("document text cannot be empty")
    chunks: list[DocumentChunk] = []
    start = 0
    ordinal = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        content = text[start:end].strip()
        if content:
            chunks.append(
                DocumentChunk(
                    document_id=document.document_id,
                    tenant_id=document.tenant_id,
                    title=document.title,
                    chunk_id=f"{document.document_id}:{ordinal}",
                    text=content,
                    tokens=tuple(token.lower() for token in TOKEN.findall(content)),
                    embedding=deterministic_fake_embedding(content),
                )
            )
            ordinal += 1
        if end == len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


class LocalRetriever:
    """Deterministic hybrid lexical/vector retrieval with tenant scope and bounded top-k."""

    def __init__(self, documents: list[KnowledgeDocument]):
        if len(documents) > MAX_DOCUMENTS:
            raise ContractError("knowledge base exceeds 100-document limit")
        if len({doc.document_id for doc in documents}) != len(documents):
            raise ContractError("document IDs must be unique")
        self.chunks = [chunk for doc in documents for chunk in chunk_document(doc)]

    def search(self, tenant_id: str, query: str, top_k: int = 3) -> list[Citation]:
        if not tenant_id:
            raise ContractError("tenant is required")
        if not 1 <= top_k <= 10:
            raise ContractError("top_k must be between 1 and 10")
        try:
            query = safe_retrieval_query(query)
        except ValueError as exc:
            raise ContractError(str(exc)) from exc
        query_tokens = tuple(token.lower() for token in TOKEN.findall(query))
        if not query_tokens:
            return []
        query_set = set(query_tokens)
        query_embedding = deterministic_fake_embedding(query)
        ranked: list[tuple[float, DocumentChunk]] = []
        for chunk in self.chunks:
            if chunk.tenant_id != tenant_id:
                continue
            tokens = chunk.tokens
            if not tokens:
                continue
            counts = {token: tokens.count(token) for token in query_set}
            matched = sum(count > 0 for count in counts.values())
            if not matched:
                continue
            lexical = sum(min(count, 3) for count in counts.values()) / len(tokens) ** 0.5
            lexical = min(1.0, lexical)
            vector = max(0.0, cosine_similarity(query_embedding, chunk.embedding))
            score = 0.7 * lexical + 0.3 * vector
            ranked.append((score, chunk))
        ranked.sort(key=lambda item: (-item[0], item[1].document_id, item[1].chunk_id))
        return [
            Citation(
                document_id=chunk.document_id,
                title=chunk.title,
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                score=score,
            )
            for score, chunk in ranked[:top_k]
        ]


def hit_at_k(retriever: LocalRetriever, cases: list[dict[str, str]], k: int = 3) -> float:
    if not cases:
        raise ContractError("evaluation cases cannot be empty")
    hits = 0
    for case in cases:
        hits += any(
            citation.document_id == case["expected_document_id"]
            for citation in retriever.search(case["tenant_id"], case["query"], k)
        )
    return hits / len(cases)
