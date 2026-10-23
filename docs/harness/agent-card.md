# Agent card — p05

- Purpose: Triage tenant-scoped support tickets through authenticated fake-mode orchestration, tenant-scoped PostgreSQL hybrid retrieval, and signed TCP MCP tools.
- Unit of work: One authenticated ticket request through bounded fake-mode orchestration, retrieval, approval checks, and persisted status/response.
- Verifiable success criterion: API and MCP transport identity are verified before access; retrieval citations, tool results, and approvals remain tenant-scoped; sensitive refunds require a distinct approver; missing identity or failed mandatory checks fail closed. Local protocol and Keycloak 26.8.1 revocation tests pass over MCP loopback TCP; external identity provider remains unverified.
- Pattern: agent
- Runtime: custom-loop
- Allowed tools: Tenant-scoped knowledge retrieval, read-only billing/CRM lookup, and refund proposal; no direct refund effect or outbound communication.
- Human approval points: Refunds above the configured threshold require a distinct authorized approver.
- Limits: `LLM_MODE=fake` in CI; deterministic hashed vectors are not semantic embeddings; bounded retrieval/tools/steps/time; no live provider calls without separate authorization. The local service gate proves PostgreSQL/pgvector, Redis Streams, TCP MCP, and durable worker flow. It does not prove external identity, semantic model quality, or production behavior.

## Phase 008 service evidence

The migration and hybrid SQL were exercised against PostgreSQL 16 with pgvector 0.8.7. The test confirmed HNSW and GIN indexes and excluded another tenant's document, using deterministic fake vectors and a psycopg test adapter. The authenticated MCP Streamable HTTP server was reached over loopback TCP; a local test verifier allowed the matching tenant, denied cross-tenant access, and returned HTTP 401 for a missing token. This does not verify an external identity provider or the product's native asyncpg path. The durable API-to-worker-to-agent flow remains INCOMPLETE; semantic quality and production model metrics remain PENDING.


## Phase 009 service acceptance

The isolated Compose demo passed durable API submission/restart, P04 worker recovery after a committed simulated effect, P01 LangGraph checkpoint resume, signed tenant-scoped MCP over TCP, PostgreSQL/pgvector retrieval, Redis limits, HITL, and correlated traces. Semantic/model quality, cost, comparable latency and external identity-provider acceptance remain PENDING/INCOMPLETE.


## Phase 010 retry and identity boundary

- MCP, PostgreSQL, Redis/SQS transport errors are retried only when explicitly classified as temporary; authorization and unknown failures remain fail-closed.
- Durable jobs retain the verified acceptance-time subject, tenant, roles, and scopes through delayed approval resume. This local snapshot does not track identity-provider revocation; external issuer/delegation remains INCOMPLETE.

## Phase 011 external MCP token verification

- Optional `MCP_OIDC_*` configuration uses an authorization server's RFC 7662 introspection endpoint for direct network MCP callers. Introspection runs for each MCP request; a token reported inactive is rejected. Internal worker delegation continues using the short-lived local signer. P05 0.4.2 includes this behavior.
- A disposable Keycloak 26.8.1 issuer token called an allowlisted MCP read tool over TCP, then received HTTP 401 after provider revocation. No external issuer is configured, API bearer verification remains local HS256, and revocation is not propagated to queued work after acceptance; those gates remain INCOMPLETE.

## Phase 010 release

- P05 0.4.2 is a local versioned wheel with immutable source/artifact provenance and an isolated PostgreSQL migration consumer smoke. This local package gate is not a production-readiness signal.
