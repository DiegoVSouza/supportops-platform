# Phase 007 — Integrated platform remediation

## Objective
Align P05's API contract, durable service path, RAG/MCP security, tracing, and acceptance gates with the original brief and portfolio remediation criteria. Missing service evidence stays INCOMPLETE; replay/model metrics without runs stay PENDING.

## Requirements
- [ ] P05-007-001: Reconcile `openapi.yaml` with original `/healthz`, approval, and feedback routes. Intentional deviations require ADR, API version change, and consumer update.
- [ ] P05-007-002: Exercise authenticated fake-mode ticket processing through installed versioned P00–P04 wheels, durable P04 worker, P01 agent, tenant RAG, authorized MCP, approval, and persisted response/status. Service path uses PostgreSQL and Redis.
- [ ] P05-007-003: Implement embeddings/pgvector and hybrid retrieval; propagate trusted network MCP identity; verify tenant isolation, citations, and injection denial through the product path.
- [ ] P05-007-004: Correlate traces across API-to-database, exercise dashboards/alerts, include P02 adversarial/regression checks in CI, and prove degraded fixtures fail the required gate.
- [ ] P05-007-005: Keep replay/model/cost/latency PENDING without traceable cassettes or authorized live runs; update agent card, feature list, progress, architecture, threat model, runbook, and bilingual knowledge docs from evidence.

## Out of scope
Paid/live model calls, deployment, Terraform apply, publication, push, PR/merge, and changes outside P05. No production-readiness claim based on doubles or package installation.

## Acceptance criteria
- Original API routes are compatible or have documented ADR/version migration and updated consumers.
- An authenticated fake-mode ticket traverses the service-backed queue/worker and agent path with tenant-scoped citations, tool policy, HITL, and persistence; PostgreSQL/Redis claims require those services.
- Authenticated network MCP identity is trusted only from transport context; missing or unauthorized identity fails closed.
- API-path adversarial/degraded fixtures deny prohibited actions and make required CI fail when degraded.
- Without traceable replay inputs or authorized live runs, replay/model quality/cost/latency remain PENDING.
