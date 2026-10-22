# Agent card — p05

- Purpose: Triage tenant-scoped support tickets through authenticated, bounded fake-mode orchestration, cited hybrid retrieval, and policy-authorized MCP tools.
- Unit of work: One authenticated ticket request through bounded fake-mode orchestration, retrieval, approval checks, and persisted status/response.
- Verifiable success criterion: API and MCP transport identity are verified before access; retrieval citations, tool results, and approvals remain tenant-scoped; sensitive refunds require a distinct approver; missing identity or failed mandatory checks fail closed. Local ASGI transport tests do not prove TCP deployment.
- Pattern: agent
- Runtime: custom-loop
- Allowed tools: Tenant-scoped knowledge retrieval, read-only billing/CRM lookup, and refund proposal; no direct refund effect or outbound communication.
- Human approval points: Refunds above the configured threshold require a distinct authorized approver.
- Limits: `LLM_MODE=fake` in CI; deterministic hashed vectors are not semantic embeddings; bounded retrieval/tools/steps/time; no live provider calls without separate authorization. In-memory API/queue and ASGI MCP tests do not prove PostgreSQL/pgvector, Redis, LocalStack, deployed network identity, production behavior, or model quality.

## Phase 008 service evidence

The migration and hybrid SQL were exercised against PostgreSQL 16 with pgvector 0.8.7. The test confirmed HNSW and GIN indexes and excluded another tenant's document, using deterministic fake vectors and a psycopg test adapter. The authenticated MCP Streamable HTTP server was reached over loopback TCP; a local test verifier allowed the matching tenant, denied cross-tenant access, and returned HTTP 401 for a missing token. This does not verify an external identity provider or the product's native asyncpg path. The durable API-to-worker-to-agent flow remains INCOMPLETE; semantic quality and production model metrics remain PENDING.
