#!/usr/bin/env python3
"""Run deterministic local hit@k; this evaluates retrieval fixtures, not an LLM."""

import json
from pathlib import Path

from supportops_platform.rag.retrieval import KnowledgeDocument, LocalRetriever, hit_at_k

ROOT = Path(__file__).resolve().parents[1]
documents = [
    KnowledgeDocument("refund-policy", "tenant-a", "Refund policy", "Refunds above 50 dollars require approval."),
    KnowledgeDocument("delivery-policy", "tenant-a", "Delivery policy", "Track a delayed package with the carrier reference."),
    KnowledgeDocument("account-security", "tenant-a", "Account security", "Account takeover requires secure identity verification."),
    KnowledgeDocument("billing-dispute", "tenant-a", "Billing dispute", "Open an invoice payment dispute with billing support."),
    KnowledgeDocument("private-b", "tenant-b", "Private policy", "Tenant B account data is restricted."),
]
cases = json.loads((ROOT / "evals/retrieval/cases.json").read_text(encoding="utf-8"))
score = hit_at_k(LocalRetriever(documents), cases, k=3)
hits = round(score * len(cases))
print("evaluation=deterministic-local-retrieval")
print(f"cases={len(cases)}")
print(f"hit_at_3={hits}/{len(cases)} ({score:.3f})")
print("interpretation=fixture coverage only; not LLM quality")
