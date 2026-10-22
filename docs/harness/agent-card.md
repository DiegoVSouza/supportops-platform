# Agent card — p05

- Purpose: Triage tenant-scoped support tickets through authenticated fake-mode orchestration, tenant-scoped PostgreSQL hybrid retrieval, and signed TCP MCP tools.
- Unit of work: One authenticated ticket request through bounded fake-mode orchestration, retrieval, approval checks, and persisted status/response.
- Verifiable success criterion: API and MCP transport identity are verified before access; retrieval citations, tool results, and approvals remain tenant-scoped; sensitive refunds require a distinct approver; missing identity or failed mandatory checks fail closed. Local loopback TCP tests pass; external identity provider remains unverified.
- Pattern: agent
- Runtime: custom-loop
- Allowed tools: Tenant-scoped knowledge retrieval, read-only billing/CRM lookup, and refund proposal; no direct refund effect or outbound communication.
- Human approval points: Refunds above the configured threshold require a distinct authorized approver.
- Limits: `LLM_MODE=fake` in CI; deterministic hashed vectors are not semantic embeddings; bounded retrieval/tools/steps/time; no live provider calls without separate authorization. The local service gate proves PostgreSQL/pgvector, Redis, LocalStack, TCP MCP, and durable worker flow. It does not prove external identity, semantic model quality, or production behavior.

## Phase 008 service evidence

The migration and hybrid SQL were exercised against PostgreSQL 16 with pgvector 0.8.7. The test confirmed HNSW and GIN indexes and excluded another tenant's document, using deterministic fake vectors and a psycopg test adapter. The authenticated MCP Streamable HTTP server was reached over loopback TCP; a local test verifier allowed the matching tenant, denied cross-tenant access, and returned HTTP 401 for a missing token. This does not verify an external identity provider or the product's native asyncpg path. The durable API-to-worker-to-agent flow remains INCOMPLETE; semantic quality and production model metrics remain PENDING.


## Phase 009 service acceptance

The isolated Compose demo passed durable API submission/restart, P04 worker recovery after a committed simulated effect, P01 LangGraph checkpoint resume, signed tenant-scoped MCP over TCP, PostgreSQL/pgvector retrieval, Redis limits, HITL, and correlated traces. Semantic/model quality, cost, comparable latency and external identity-provider acceptance remain PENDING/INCOMPLETE.
