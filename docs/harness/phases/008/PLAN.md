# PLAN — PostgreSQL pgvector and authenticated TCP MCP gates

## Allowed write paths
artifacts/evidence/**; docs/harness/**; docs/harness/phases/008/**; docs/knowledge/**; README.md; README.pt-BR.md; scripts/** and tests/** only if required to make an existing gate runnable without changing public contracts

## Forbidden changes
No live/paid LLM, no external identity provider, no external publication/deploy/push, no Terraform apply, no sibling-source imports, no changes to shared kit/other repos, no root roadmap.

## Dependencies
Docker CLI/daemon; isolated PostgreSQL/pgvector and Redis; prior P04 LocalStack stack may be reused only through its published local package/API and loopback endpoint; no port collisions.

## Observable tasks
`n- 1. Review P05 architecture/dependencies and create isolated service configuration. `n- 2. Run PostgreSQL pgvector and TCP MCP tests. `n- 3. Attempt feasible product path and tracing/evaluation gates in fake mode. `n- 4. Reconcile evidence-backed state and docs.

## Checks
Migration and HNSW/GIN indexes plus hybrid tenant filtering against PostgreSQL; authenticated bearer MCP over TCP; product integration only if architecture and installed wheels permit; full fake-mode gate; OpenAPI check; trace/eval status.

## Stop condition
External identity, unimplemented durable queue integration, unavailable services, or absent cassettes stay INCOMPLETE/PENDING; do not alter contract without ADR/version/consumer updates.

## Review
Plan reviewed before execution: scope is evidence-first, tasks are observable, path ownership is explicit, and unavailable services cannot become PASS.
