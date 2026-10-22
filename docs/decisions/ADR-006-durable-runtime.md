# ADR-006 — Durable local runtime and additive task result contract

Status: accepted and implemented in 0.4.0, 2026-10-22.

P05 0.3.0 installed upstream packages but served an in-memory product path. Version 0.4.0 adds a configured PostgreSQL repository, native asyncpg retrieval, Redis atomic rate limiting and a PostgreSQL submission outbox dispatched through the approved P04 0.1.3 wheel into isolated LocalStack SQS queues. Process restarts preserve accepted work, tenant identity, approvals and results. Duplicate dispatch is safe through P04 idempotency and the product effect ledger.

Existing routes and their response keys remain compatible. GET /v1/tasks/{id} adds result/error fields in the durable runtime; statuses include the existing needs_approval and succeeded states. X-Trace-ID is additive. API and MCP identities are separate signed tokens: delegated MCP tokens have audience/issuer/expiry validation and carry no extra role/scope. An external OAuth issuer is still a separate deployment concern.

All model/embedding behavior remains fake. Tool policy ignores model-provided identities, retrieved instructions cannot select tools, and refunds are simulated after distinct-principal approval. The local ledger does not guarantee exactly-once arbitrary external effects. No upstream public contract changes or sibling imports are required. OpenAPI consumers and version assertions are updated with the additive release.
