"""Run one Groq-backed task through an isolated Docker service stack."""

import argparse
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx
from groq import Groq
from run_live_groq_eval import MODEL, load_credentials

from supportops_platform.rag.postgres import PostgresRetriever
from supportops_platform.rag.retrieval import KnowledgeDocument

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-start", action="store_true")
    args = parser.parse_args()
    defaults = {
        "P05_COMPOSE_PROJECT": "p05-live-020",
        "P05_API_PORT": "58000",
        "P05_MCP_PORT": "58001",
        "P05_POSTGRES_PORT": "56432",
        "P05_REDIS_PORT": "56379",
        "P05_PROMETHEUS_PORT": "59091",
        "P05_JAEGER_PORT": "55686",
        "P05_GRAFANA_PORT": "53001",
        "P05_OTEL_PORT": "55317",
    }
    for name, value in defaults.items():
        os.environ.setdefault(name, value)
    result = {
        "provider": "groq",
        "model": MODEL,
        "status": "INCOMPLETE",
        "cost_usd": "PENDING",
        "started_at_utc": datetime.now(UTC).isoformat(),
    }
    stage = "configuration"
    try:
        if os.getenv("LLM_MODE", "fake") != "live":
            raise ValueError("explicit LLM_MODE=live required")
        keys = load_credentials()
        stage = "model_catalog"
        available = sum(
            any(
                item.id == MODEL
                for item in Groq(api_key=key, max_retries=0, timeout=20)
                .models.list()
                .data
            )
            for key in keys
        )
        if not keys or available != len(keys):
            raise RuntimeError("requested model not available for every configured key")
        result["model_available_key_count"] = available
        import check_services as services

        services.COMPOSE.extend(["-f", "docker-compose.live.yml"])
        services.ENV.update(
            {
                f"GROQ_API_KEY_{index}": os.environ[f"GROQ_API_KEY_{index}"]
                for index in range(1, 5)
            }
        )
        result["compose_project"] = services.PROJECT
        stage = "docker_start"
        if not args.no_start:
            if services.command(["ps", "-q"], silent=True):
                raise RuntimeError("refusing to replace a nonempty Compose project")
            services.command(["config", "--quiet"])
            services.command(["build", "api"])
            services.command(["up", "--no-build", "-d", "--wait"])
        health = services.wait_http(f"http://127.0.0.1:{services.API_PORT}/healthz")
        if health.get("llm_mode") != "live":
            raise RuntimeError("API did not start in live mode")
        stage = "database_fixture"
        retriever = PostgresRetriever(services.DSN)
        retriever.ingest(
            KnowledgeDocument(
                "shipping",
                "tenant-a",
                "Shipping guidance",
                "For a delayed parcel, use the carrier tracking link in the dispatch message. A support agent can help if the link is missing.",
            )
        )
        retriever.ingest(
            KnowledgeDocument(
                "private-b",
                "tenant-b",
                "Private",
                "Tenant B confidential account data.",
            )
        )
        owner = services.token()
        foreign = services.token("tenant-b")
        stage = "live_task"
        with httpx.Client(
            base_url=f"http://127.0.0.1:{services.API_PORT}", timeout=20
        ) as api:
            created = api.post(
                "/v1/tickets",
                headers=owner,
                json={
                    "customer_id": "customer-a",
                    "subject": "Where is my carrier tracking link?",
                    "body": "I received the dispatch message. Please explain how to use its carrier link to track the delayed parcel.",
                },
            )
            created.raise_for_status()
            request = {"ticket_id": created.json()["id"]}
            submit_headers = {**owner, "Idempotency-Key": "live-" + uuid4().hex}
            submitted = api.post("/v1/tasks", headers=submit_headers, json=request)
            submitted.raise_for_status()
            task_id = submitted.json()["id"]
            task = services.wait_task(api, task_id, owner, seconds=150)
            body = task["result"]
            repeated = api.post("/v1/tasks", headers=submit_headers, json=request)
            repeated.raise_for_status()
            usage = body.get("llm_usage", {})
            ids = [citation["document_id"] for citation in body.get("citations", [])]
            checks = {
                "api_live": health["llm_mode"] == "live",
                "worker_live": body.get("llm_mode") == "live",
                "actual_model": body.get("model") == MODEL,
                "real_usage": usage.get("input_tokens", 0) > 0
                and usage.get("output_tokens", 0) > 0,
                "four_calls": usage.get("calls") == 4,
                "tenant_scope": "private-b" not in ids,
                "shipping_retrieved": "shipping" in ids,
                "cited_answer": "[shipping#shipping:0]" in body.get("response", ""),
                "within_budget": usage.get("estimated_cost_usd", 1) <= 0.01,
                "idempotent_submission": repeated.json()["id"] == task_id,
                "foreign_task_denied": api.get(
                    "/v1/tasks/" + task_id, headers=foreign
                ).status_code
                == 404,
                "no_refund": "refund" not in body,
            }
        stage = "exported_trace"
        deadline = time.monotonic() + 40
        spans = []
        while time.monotonic() < deadline:
            response = httpx.get(
                f"http://127.0.0.1:{services.JAEGER_PORT}/api/traces/"
                + body["trace_id"],
                timeout=5,
            )
            data = (
                response.json().get("data", []) if response.status_code == 200 else []
            )
            spans = [span for trace in data for span in trace["spans"]]
            if sum(span["operationName"] == "llm.inference" for span in spans) >= 4:
                break
            time.sleep(1)
        names = {span["operationName"] for span in spans}
        checks["correlated_trace"] = {
            "api.request",
            "worker.run",
            "agent.triage",
            "llm.inference",
            "database.knowledge.hybrid_search",
        } <= names
        inference = [span for span in spans if span["operationName"] == "llm.inference"]
        checks["trace_provider"] = bool(inference) and all(
            any(
                tag["key"] == "supportops.llm.provider" and tag["value"] == "groq"
                for tag in span["tags"]
            )
            for span in inference
        )
        checks["trace_content_absent"] = all(
            tag["key"] != "supportops.llm.content"
            for span in spans
            for tag in span["tags"]
        )
        result.update(
            status="PASS" if all(checks.values()) else "FAIL",
            assertions=checks,
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            estimated_cost_usd=usage.get("estimated_cost_usd"),
            api_calls=usage.get("calls"),
            trace_id=body["trace_id"],
            trace_span_names=sorted(names),
        )
    except Exception as exc:
        result["error"] = {
            "class": type(exc).__name__,
            "stage": stage,
            "status": getattr(getattr(exc, "response", None), "status_code", None),
        }
    code = 0 if result["status"] == "PASS" else 1
    result.update(exit_code=code, finished_at_utc=datetime.now(UTC).isoformat())
    out = ROOT / "artifacts/evidence/live-docker"
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    (out / f"groq-services-{stamp}.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
