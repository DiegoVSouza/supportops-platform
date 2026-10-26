# P05 execution plan

## Task 1 — Test RAG-to-agent contracts

Add mocked tests that verify only tenant-scoped citations reach the client, agent JSON contracts parse, no refund/MCP tool is exposed, and fake mode stays deterministic/offline.

## Task 2 — Implement bounded Groq-backed agent client

Add an optional pinned Groq SDK extra and an opt-in client for P01's Core runner. Store the system contract in `agent/prompts/`; send only one synthetic delivery ticket plus tenant-authorized retrieval evidence; capture only sanitized results.

## Task 3 — Verify one live RAG case

Run focused and full offline gates, then one model-list preflight and a single ticket workflow (up to four serial completions) with <=256 output tokens each and <=USD 0.01 estimated exposure. Evaluate answer grounding, tenant scope and safety. Preserve all failures and avoid re-running merely to tune the one sample.

## Ownership

`allowed_write_paths`: `docs/harness/phases/018-live-rag-agent/**`, `agent/prompts/live-groq.md`, `supportops_platform/agents/triage.py`, `scripts/run_live_groq_eval.py`, `tests/test_live_groq_eval.py`, `pyproject.toml`, `uv.lock`, `README.md`, `docs/harness/decisions.md`, `docs/harness/progress.md`, `artifacts/evidence/phase-018-groq-*`.

`forbidden_changes`: `harness-kit/**`, `.env`, other projects, RAG datasets, API schemas, MCP allowlists, refund tools, and unrelated tenant/security behavior.

## Runtime and stop conditions

- Explicit `LLM_MODE=live`; Groq `openai/gpt-oss-20b`; one synthetic tenant-A case; <=4 serial calls, <=256 output tokens each, 20s timeout, <=USD 0.01 estimated exposure within the configured USD 2/task ceiling.
- At most one bounded pass over unique configured keys per request; no retries for auth/model/validation/agent contract errors. No provider or model fallback.
- Stop on model unavailable, tenant/evidence assertion failure, tool/action attempt, quota exhaustion, or budget threshold.

## Validation

Use P05 focused tests and documented full check. Save commands, exit codes, sanitized output and run metadata in phase-018 evidence.
