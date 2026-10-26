# P05 live RAG agent evaluation

## Status

Implemented and verified. A ticket with a missing dispatch message correctly escalated under the local evidence; after aligning the case with an answerable received-message scenario, the cited tenant-scoped answer passed. Docker service checks remain unavailable.

## Goal and selection

Evaluate one synthetic, non-sensitive delivery question through P05 tenant-scoped retrieval and its P01-backed agent orchestration, replacing the current fake client only in an opt-in live path. P05 is the RAG SaaS product and currently reports that no live LLM/embedding provider is called.

## Requirements

- Use official Groq SDK and `openai/gpt-oss-20b`; authenticated model check before agent completions.
- Keep the run on one synthetic tenant-A ticket and local fixture documents; no real tenants, customer data, MCP tools, refunds, outbound communications, or external systems.
- Use only citations returned by `LocalRetriever` for the ticket tenant. Include retrieved text as untrusted evidence, instruct the agent to cite/use only this evidence, and evaluate tenant isolation, expected delivery-policy facts, and response safety.
- Implement agent-specific structured outputs for the P01 Core runner. Max four serial completions, 256 tokens each, 20s timeout, bounded key rotation only for retryable errors, no fallback.
- Require explicit `LLM_MODE=live`; load root `.env` silently. The P05 task budget is USD 2; set a per-run estimated exposure ceiling USD 0.01. Preserve fake runner and RAG fixtures.
- Record only case ID, retrieved document IDs, model, decision/assertions, usage, retries, sanitized error class and command/exit. Never persist prompt, completion, citations' raw text, or credentials.

## Acceptance

1. Offline tests prove citation tenant isolation, prompt construction from authorized citations, response parsing, retry/budget caps, and fake determinism.
2. Full P05 offline gate remains green.
3. One real ticket run returns a safe cited answer or a sanitized failed evaluation; no cross-tenant content or tool side effect occurs.
4. Metrics come only from the real run; cost is `PENDING` until actual billing is confirmed.

## Scope

P05-local agent adapter, prompt, tests, optional dependency, docs and artifacts. No kit/sibling changes, production data, provider embeddings, billing APIs, or outbound tools.

## Verified references

- Model capabilities: [Groq GPT-OSS 20B](https://console.groq.com/docs/model/openai/gpt-oss-20b).
- Free-plan limits and retry guidance: [Groq rate limits](https://console.groq.com/docs/rate-limits).
- Official Python SDK version: [groq-python 1.7.0](https://github.com/groq/groq-python/releases/tag/v1.7.0).
