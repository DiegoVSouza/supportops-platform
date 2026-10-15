# Agent card — p05

- Purpose: Triage tenant-scoped support tickets with cited knowledge and policy-authorized tools.
- Unit of work: One authenticated ticket request through bounded fake-mode orchestration, retrieval, approval checks, and persisted status/response.
- Verifiable success criterion: The request returns only tenant-authorized citations and tool results; sensitive refunds pause for a different approver; missing identity or degraded required checks fail closed.
- Pattern: agent
- Runtime: custom-loop
- Allowed tools: Tenant-scoped knowledge retrieval, read-only billing/CRM lookup, and refund proposal; no direct refund effect or outbound communication.
- Human approval points: Refunds above the configured threshold require a distinct authorized approver.
- Limits: `LLM_MODE=fake` in CI; bounded retrieval/tools/steps/time; no live provider calls without separate authorization. Local doubles do not prove PostgreSQL, Redis, queue, network MCP, or production behavior.
