"""Opt-in Groq backend for tenant-scoped, tool-free RAG triage."""

from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any, Mapping

from supportops_obs import LLMResponse, record_llm_call

from supportops_platform.contracts import Citation

MODEL = "openai/gpt-oss-20b"
CAP_USD = 0.01
INPUT_RATE = 0.075
OUTPUT_RATE = 0.30
FIELDS = {
    "classifier": "category, summary, escalate",
    "kb_researcher": "context",
    "billing_agent": "context, escalate",
    "responder": "response, approved",
}
POLICY = (
    Path(__file__).resolve().parents[2] / "agent" / "prompts" / "live-groq.md"
).read_text(encoding="utf-8")


def _new_groq(**kwargs):
    raise RuntimeError("accounted_guard_required")


def retry_delay(attempt: int, status: int | None, headers) -> float:
    try:
        delay = (
            float(headers.get("retry-after"))
            if status == 429 and headers.get("retry-after")
            else min(0.25 * 2**attempt + random.random() * 0.1, 2)
        )
    except (TypeError, ValueError):
        delay = min(0.25 * 2**attempt + random.random() * 0.1, 2)
    if not 0 <= delay <= 2:
        raise RuntimeError("retry-after exceeds the 2 second bound") from None
    return delay


class GroqRAGClient:
    def __init__(
        self,
        keys: list[str],
        citations: tuple[Citation, ...],
        *,
        max_output_tokens: int = 256,
    ):
        if not keys or max_output_tokens < 1:
            raise ValueError("credentials and output-token cap are required")
        self.keys = list(dict.fromkeys(keys))[:4]
        self.citations = citations
        self.max_output_tokens = max_output_tokens
        self.input_tokens = 0
        self.output_tokens = 0
        self.estimated_cost_usd = 0.0
        self.calls = 0
        self.actual_model = MODEL

    def complete(self, agent: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        if agent not in FIELDS:
            raise ValueError("unknown support agent")
        cited = [
            {"id": f"{x.document_id}#{x.chunk_id}", "text": x.text}
            for x in self.citations
        ]
        if agent == "kb_researcher":
            payload = {**payload, "tenant_authorized_citations": cited}
        if agent == "responder":
            payload = {
                **payload,
                "citation_rule": "Use only supplied tenant citations; cite a supporting source ID in brackets. If evidence is insufficient, say so. Do not claim live lookup or refund.",
            }
        prompt = {
            "agent": agent,
            "required_keys": FIELDS[agent].split(", "),
            "input": payload,
        }
        messages = [
            {
                "role": "user",
                "content": POLICY + "\n" + json.dumps(prompt, ensure_ascii=False),
            }
        ]
        request_tokens = max(
            1, len(json.dumps(messages, ensure_ascii=False).encode("utf-8"))
        )
        worst = (
            (request_tokens * INPUT_RATE + self.max_output_tokens * OUTPUT_RATE)
            / 1_000_000
            * len(self.keys)
        )
        if self.estimated_cost_usd + worst > CAP_USD:
            raise RuntimeError("live request blocked by project budget")
        for attempt, key in enumerate(self.keys):
            try:
                started = time.perf_counter()
                response = _new_groq(
                    api_key=key, max_retries=0, timeout=20
                ).chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_completion_tokens=self.max_output_tokens,
                    temperature=1,
                    reasoning_effort="low",
                )
                data = json.loads(response.choices[0].message.content or "")
                if not isinstance(data, dict):
                    raise ValueError("model output must be an object")
                self.input_tokens += response.usage.prompt_tokens
                self.output_tokens += response.usage.completion_tokens
                self.estimated_cost_usd += (
                    response.usage.prompt_tokens * INPUT_RATE
                    + response.usage.completion_tokens * OUTPUT_RATE
                ) / 1_000_000
                if self.estimated_cost_usd > CAP_USD:
                    raise RuntimeError("observed usage exceeded project budget")
                self.calls += 1
                self.actual_model = getattr(response, "model", MODEL)
                if self.actual_model != MODEL:
                    raise RuntimeError("provider returned an unexpected RAG model")
                record_llm_call(
                    LLMResponse(
                        "groq",
                        self.actual_model,
                        response.usage.prompt_tokens,
                        response.usage.completion_tokens,
                        (
                            response.usage.prompt_tokens * INPUT_RATE
                            + response.usage.completion_tokens * OUTPUT_RATE
                        )
                        / 1_000_000,
                        time.perf_counter() - started,
                        content=None,
                    )
                )
                return data
            except Exception as exc:
                if isinstance(exc, (ValueError, RuntimeError)):
                    raise
                status = getattr(exc, "status_code", None)
                transient = status in {408, 409, 429, 500, 502, 503, 504} or type(
                    exc
                ).__name__ in {"Timeout", "APIConnectionError"}
                if not transient or attempt + 1 >= len(self.keys):
                    raise RuntimeError(
                        f"Groq request failed ({type(exc).__name__}, status={status})"
                    ) from None
                headers = getattr(getattr(exc, "response", None), "headers", {})
                delay = retry_delay(attempt, status, headers)
                time.sleep(delay)
        raise AssertionError("unreachable retry state")
