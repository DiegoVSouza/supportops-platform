# Agent card — p05

- Purpose: Triage tenant-scoped support tickets through authenticated, bounded fake-mode orchestration, cited hybrid retrieval, and policy-authorized MCP tools.
- Unit of work: One authenticated ticket request through bounded fake-mode orchestration, retrieval, approval checks, and persisted status/response.
- Verifiable success criterion: API and MCP transport identity are verified before access; retrieval citations, tool results, and approvals remain tenant-scoped; sensitive refunds require a distinct approver; missing identity or failed mandatory checks fail closed. Local ASGI transport tests do not prove TCP deployment.
- Pattern: agent
- Runtime: custom-loop
- Allowed tools: Tenant-scoped knowledge retrieval, read-only billing/CRM lookup, and refund proposal; no direct refund effect or outbound communication.
- Human approval points: Refunds above the configured threshold require a distinct authorized approver.
- Limits: `LLM_MODE=fake` in CI; deterministic hashed vectors are not semantic embeddings; bounded retrieval/tools/steps/time; no live provider calls without separate authorization. In-memory API/queue and ASGI MCP tests do not prove PostgreSQL/pgvector, Redis, LocalStack, deployed network identity, production behavior, or model quality.
