"""One tenant-scoped RAG case through the Core agent with Groq."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from groq import Groq

from supportops_platform.agents.live_groq import MODEL
from supportops_platform.agents.triage import run_live_triage
from supportops_platform.contracts import Ticket
from supportops_platform.rag.retrieval import KnowledgeDocument, LocalRetriever

PROJECT = Path(__file__).resolve().parents[1]
LAB = Path(__file__).resolve().parents[3]


def load_credentials() -> list[str]:
    for line in (LAB / ".env").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            name = name.strip()
            if (
                name.startswith("GROQ_API_KEY")
                and value.strip()
                and name not in os.environ
            ):
                os.environ[name] = value.strip().strip("\"'")
    return list(
        dict.fromkeys(
            os.getenv(n, "").strip()
            for n in [f"GROQ_API_KEY_{i}" for i in range(1, 5)]
            if os.getenv(n, "")
        )
    )


def available_model_keys(api_keys: list[str]) -> list[str]:
    available = []
    for key in api_keys:
        client = Groq(api_key=key, max_retries=0, timeout=20)
        if any(m.id == MODEL for m in client.models.list().data):
            available.append(key)
    return available


def evaluation_case() -> tuple[Ticket, LocalRetriever]:
    retriever = LocalRetriever(
        [
            KnowledgeDocument(
                "shipping",
                "tenant-a",
                "Shipping guidance",
                "For a delayed parcel, use the carrier tracking link in the dispatch message. A support agent can help if the link is missing.",
            ),
            KnowledgeDocument(
                "private-b",
                "tenant-b",
                "Private",
                "Tenant B confidential account data.",
            ),
        ]
    )
    ticket = Ticket(
        tenant_id="tenant-a",
        customer_id="synthetic-customer",
        subject="Where is my carrier tracking link?",
        body="I received the dispatch message. Please explain how to use the carrier link in that message to track the delayed parcel.",
        id="synthetic-p05-001",
    )
    return ticket, retriever


def evaluate_run(run) -> dict[str, object]:
    citations = run.citations
    response = run.result.decision.response
    checks = {
        "tenant_scope": all(c.document_id != "private-b" for c in citations),
        "shipping_evidence": any(c.document_id == "shipping" for c in citations),
        "approved": run.result.decision.approved is True,
        "responded": run.result.decision.action == "respond",
        "citation_in_answer": "[shipping#shipping:0]" in response,
        "four_agent_steps": len(run.result.trace) == 4,
    }
    code = 0 if all(checks.values()) else 1
    metrics = run.live_metrics or {}
    return dict(
        status="PASS" if code == 0 else "FAIL",
        failure_category=None if code == 0 else "rag_agent_assertion_mismatch",
        assertions=checks,
        step_count=len(run.result.trace),
        citation_ids=[f"{c.document_id}#{c.chunk_id}" for c in citations],
        api_calls=metrics.get("calls"),
        input_tokens=metrics.get("input_tokens"),
        output_tokens=metrics.get("output_tokens"),
        estimated_cost_usd=metrics.get("estimated_cost_usd"),
    )


def write_result(result: dict[str, object], code: int) -> None:
    evidence_dir = PROJECT / "artifacts" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    (evidence_dir / f"phase-018-groq-{timestamp}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (evidence_dir / f"phase-018-groq-{timestamp}.txt").write_text(
        f"Command: LLM_MODE=live uv run --extra live --group dev python scripts/run_live_groq_eval.py\nExit code: {code}\nSanitized result: {json.dumps(result, sort_keys=True)}\n",
        encoding="utf-8",
    )


def main() -> int:
    result = {
        "provider": "groq",
        "model": MODEL,
        "status": "INCOMPLETE",
        "exit_code": 1,
        "started_at_utc": datetime.now(UTC).isoformat(),
        "budget_cap_usd": 0.01,
        "cost_usd": "PENDING",
    }
    code = 1
    try:
        if os.getenv("LLM_MODE", "").lower() != "live":
            raise RuntimeError("explicit LLM_MODE=live required")
        api_keys = load_credentials()
        result["credential_count"] = len(api_keys)
        available = available_model_keys(api_keys)
        result["model_available_key_count"] = len(available)
        if not available:
            raise RuntimeError("requested model unavailable in authenticated catalog")
        ticket, retriever = evaluation_case()
        run = run_live_triage(ticket, retriever, available)
        result.update(evaluate_run(run))
        code = 0 if result["status"] == "PASS" else 1
    except Exception as exc:
        result["error"] = {"class": type(exc).__name__}
        code = 1
    result.update(exit_code=code, finished_at_utc=datetime.now(UTC).isoformat())
    write_result(result, code)
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
