# Verify — Phase 007: Integrated platform remediation

## Required truths and checks
1. OpenAPI includes original required routes or every intentional deviation has ADR, API version change, and consumer update — compare with `docs/intake/ORIGINAL-BRIEF.md`, export OpenAPI, and run API contract tests.
2. P00–P04 integrations use installed versioned wheels with source commit/version/SHA-256 and consumer tests — `uv run python scripts/verify_packages.py`.
3. Authenticated ticket path traverses durable P04 worker and P01 agent, uses PostgreSQL/Redis in service-backed mode, and persists status/response/citations — service E2E with dependencies running.
4. pgvector/embedding and hybrid retrieval preserve tenant filtering, citation provenance, and deterministic lexical tests — retrieval/API tests plus service integration.
5. MCP network transport propagates authenticated trusted principal; absent/unauthorized identity fails closed — network MCP contract/security tests; in-memory tests alone do not satisfy this requirement.
6. Tool injection/tenant isolation are denied through API/agent path; degraded fixture makes full gate fail — adversarial tests and `uv run python scripts/check_full.py`.
7. One trace correlates API, queue, worker, agent, LLM boundary, MCP/tool, and database; dashboards/alerts run against local stack — service integration evidence.
8. Feature list, progress, agent card, architecture, threat model, runbook, and bilingual knowledge docs match saved evidence; absent service gates are INCOMPLETE and replay/model/cost/latency without valid runs are PENDING.

## Evidence rules
Save each executed command, exit code, and output under `artifacts/evidence/`, classified as unit/contract, package integration, service integration/E2E, or agent evaluation. Missing services/cassettes are INCOMPLETE/PENDING with the exact attempted check; do not infer PASS.

## Result (filled during execution)
- [ ] 1: INCOMPLETE — comparison and contract checks pending.
- [ ] 2: INCOMPLETE — package gate rerun pending.
- [ ] 3: INCOMPLETE — service-backed E2E pending.
- [ ] 4: INCOMPLETE — pgvector service path pending.
- [ ] 5: INCOMPLETE — authenticated network MCP path pending.
- [ ] 6: INCOMPLETE — adversarial/degraded full gate pending.
- [ ] 7: INCOMPLETE — integrated trace/dashboard run pending.
- [ ] 8: INCOMPLETE — execution/state reconciliation pending; model metrics PENDING absent approved runs.
