# Progress

- Kit initialization completed.

## 2026-10-15 — Intake and plan review

- Original acceptance criteria were reconciled into six local phases with SPEC, PLAN, and VERIFY before product code.
- Coordinator plan review: accepted. Every phase plan declares local path ownership, forbidden changes, 2–4 tasks, verification, and stop condition.
- Intake baseline used earlier P00–P04 wheel versions. This historical state was superseded by the phase 007 package install and consumer evidence below.
- The RAG profile is enabled; governance is full because the platform is multi-tenant, handles private ticket data, and has an irreversible refund action.

## 2026-10-15 — Local API and retrieval components

- API baseline and contracts committed as `549ab1f`; tenant scope, rate bounds, pending refund approval, and idempotency are exercised by unit/API tests.
- RAG/MCP local implementation includes deterministic tenant-scoped retrieval, API citations, and principal-injected in-memory MCP tools.
- Baseline local API tests passed; runtime persistence, service-backed task-broker delivery, authenticated network MCP transport, replay evaluation, and degraded-agent regression were then INCOMPLETE or PENDING. Current package/API status is recorded in phase 007 below.

## 2026-10-15 — Roadmap remediation phase 007

- Phase 007 was created and reviewed before product changes. Its five acceptance requirements cover API reconciliation, approved wheel integration, service path, retrieval/MCP security, observability, and evidence-backed state.
- The initial phase-007 note listed P00/P02/P04 releases as not installed and P01/P03 provenance as pending. Those statements are superseded by the verified artifact manifest below.
- PostgreSQL/pgvector, Redis, LocalStack, Docker runtime, authenticated network MCP, dashboard/alert E2E, and replay/model evaluation remain INCOMPLETE or PENDING until their respective checks run.

## 2026-10-15 — Phase 007 local remediation evidence

- API package is 0.3.0. ADR-005 restores `/healthz`, `/v1/tickets/{ticket_id}/approve`, and `/v1/feedback` additively; `/health` remains a hidden compatibility alias. OpenAPI export check passes.
- Approved local wheels pin P01 0.1.1, P02 0.2.0, P03 0.3.1, and P04 0.1.2 alongside P00 1.0.1. Provenance is recorded in `sources.lock.json`; P05 package consumers and `verify_packages.py` pass.
- Deterministic hashed vectors are fake control-flow fixtures, not semantic embeddings. Local hybrid retrieval and the tenant-scoped PostgreSQL pgvector/full-text adapter contract pass. The migration declares pgvector 0.8.7, cosine distance, HNSW, and GIN indexes; PostgreSQL service execution remains INCOMPLETE and semantic quality remains PENDING.
- MCP 2.3.0 Streamable HTTP bearer verification derives tenant/roles/scopes from trusted SDK request context. Authenticated and cross-tenant calls pass using the official SDK client over in-process ASGI; TCP-hosted service/identity-provider acceptance remains INCOMPLETE.
- Fake/local checks, package gate, and full gate were rerun; exact outputs are saved in `artifacts/evidence/remediation-*.txt`. PostgreSQL/Redis/LocalStack E2E, dashboard/alert E2E, replay/model evaluation remain INCOMPLETE/PENDING.
- `docker info` was attempted for service integration and exited 1 because Docker Desktop's Linux engine pipe was unavailable. No Compose or service E2E was run.

## 2026-10-21 — pgvector and authenticated MCP service gates

- PostgreSQL 16 with pgvector 0.8.7 applied the migration and verified the HNSW and GIN indexes. Hybrid retrieval returned the matching tenant's row and excluded another tenant using deterministic fake vectors. The script used a psycopg adapter for the repository's asyncpg-style placeholders because native asyncpg is absent from the lock; native driver integration remains INCOMPLETE.
- Authenticated MCP Streamable HTTP ran over loopback TCP. The local verifier allowed the matching tenant, denied cross-tenant retrieval, and rejected a missing bearer with HTTP 401. External identity-provider acceptance remains INCOMPLETE.
- The full gate remains INCOMPLETE: local tests, package provenance and OpenAPI pass, but the API still lacks a durable PostgreSQL/Redis queue-to-P04 worker-to-P01 agent product path. Semantic evaluation, replay, model quality, cost and comparable latency remain PENDING. Evidence: `artifacts/evidence/phase-008-service-gates-rerun.txt` and `phase-008-full-gate-rerun.txt`.


## 2026-10-22 � Phase 009 durable local runtime

- ADR-006 and version 0.4.0 add PostgreSQL product state/outbox, native asyncpg pgvector retrieval, Redis atomic rate limiting, signed delegated MCP tokens, P04 0.1.3 queue/worker, P01 0.1.1 LangGraph, approval resume and fake-only execution.
- Unit/contract/package suite: 86 passed. Native asyncpg/pgvector migration and hybrid tenant retrieval, cross-process Redis, authenticated loopback MCP, durable API restart, HITL, indirect-injection blocks, correlated trace, dashboard/alert and non-root services passed. Worker kill after a committed simulated effect recovered the job with exactly one product ledger row.
- Fake control quality gate passed ten fixtures; deliberately degraded control returned exit 1 and was rejected. Semantic/model quality, cost and comparable latency remain PENDING. External identity provider remains INCOMPLETE.
- Full evidence: `artifacts/evidence/phase-009-full-gate-final.txt`; crash evidence: `phase-009-crash-recovery.txt`; versioned API contract: `openapi.yaml`; decision: `docs/decisions/ADR-006-durable-runtime.md`.

- P05 0.4.0 wheel was built from source commit `4807292`, installed in an isolated target, and its packaged migration 003 was loaded/applied against the real PostgreSQL 16/pgvector 0.8.7 service. SHA-256 and artifact commit are recorded in `docs/harness/sources.lock.json`; see `phase-009-wheel-*.txt`.
