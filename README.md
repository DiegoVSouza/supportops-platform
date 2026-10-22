# P05 — SupportOps Platform

An independently versioned, tenant-scoped support operations API with deterministic
RAG, an MCP tool boundary, asynchronous task contracts, human approval for refund
requests, and privacy-aware observability interfaces. Local fake mode is the default.

## Quick start

```powershell
uv sync --locked
$env:LLM_MODE = "fake"
uv run --locked python -m supportops_platform
```

In another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/healthz
```

The default API uses in-memory development storage and signed local demo tokens. See the
[architecture](docs/architecture.md), [security model](docs/harness/security.md), and
[package integration gate](docs/harness/package-integration.md). See also the
[test classification](docs/harness/test-classification.md). P00–P04 use approved
local wheels in the lock. The isolated Compose profile also exercises PostgreSQL,
pgvector, Redis, LocalStack SQS, P04 0.1.3 and P01 0.1.1 through an authenticated
durable service flow. See `docker-compose.services.yml` and phase 009 evidence. The
service stack uses local fixture credentials and ephemeral signing keys. No live LLM
or external refund effect runs.

## Validation

```powershell
uv run --locked pytest
uv run --locked python scripts/check_full.py
```

`check_full.py` executes unit, contract, package, fixture evaluation, Docker promtool,
service E2E and worker crash recovery gates. It reports INCOMPLETE and exits nonzero
when a required local gate is explicitly skipped. Review `artifacts/evidence/` for
saved command output and gate status. Model quality and cost/latency metrics remain
PENDING without traceable cassettes or comparable authorized runs.
For an in-process walkthrough of ticket intake, task recovery, RAG citations, and
human approval, run `uv run --locked python scripts/demo.py`.

## Status

API compatibility and authentication, tenant filtering, dual-control refund approval,
tenant-scoped hybrid RAG citations, PostgreSQL/pgvector migration and retrieval,
atomic Redis limits, durable API→P04 worker→P01 agent execution, TCP-hosted signed MCP,
checkpoint persistence and correlated traces passed local service checks. Local
crash-after-effect recovery confirmed one simulated effect row and eventual job
completion. External identity-provider acceptance, replay/model quality, cost and
comparable latency remain INCOMPLETE/PENDING. Hashed fake embeddings and deterministic
fixtures do not establish semantic quality or production readiness.
