"""Local bounded lexical retrieval. Retrieved text remains untrusted input."""

from __future__ import annotations

import re
from dataclasses import dataclass

from supportops_platform.contracts import Citation, ContractError

TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
MAX_DOCUMENTS = 100
MAX_DOCUMENT_BYTES = 64_000
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80


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
                )
            )
            ordinal += 1
        if end == len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


class LocalRetriever:
    """Term-frequency retrieval that enforces tenant scope and bounded top-k."""

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
        query_tokens = tuple(token.lower() for token in TOKEN.findall(query))
        if not query_tokens:
            return []
        query_set = set(query_tokens)
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
            score = sum(min(count, 3) for count in counts.values()) / len(tokens) ** 0.5
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
