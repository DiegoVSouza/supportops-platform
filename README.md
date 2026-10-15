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

The API uses in-memory development storage and signed local demo tokens. See the
[architecture](docs/architecture.md), [security model](docs/harness/security.md), and
[package integration gate](docs/harness/package-integration.md). See also the
[test classification](docs/harness/test-classification.md). P00–P04 use approved
local wheels in the lock. P04's SQLite/in-memory API is covered by a consumer contract;
the P03 0.3.1 wheel is provenance-checked with the other integrations. PostgreSQL/SQS service checks remain incomplete. Fake mode creates a process-local random JWT
key; configure `JWT_SECRET` when local tokens must survive restarts. No live LLM or
external effects run.

## Validation

```powershell
uv run --locked pytest
uv run --locked python scripts/check_full.py
```

`check_full.py` reports incomplete service-backed gates. Review `artifacts/evidence/`
for saved command output and gate status.
For an in-process walkthrough of ticket intake, task recovery, RAG citations, and
human approval, run `uv run --locked python scripts/demo.py`.

## Status

API compatibility and authentication, tenant filtering, dual-control refund approval,
tenant-scoped hybrid RAG citations, and MCP Streamable HTTP bearer auth over an
in-process ASGI transport have local tests. P00–P04 wheel adapters are installed and
verified. PostgreSQL/pgvector, Redis/queue durability, TCP-hosted MCP, replay evaluation,
and service-backed deployment checks remain incomplete. Hashed fake embeddings and
the deterministic retrieval fixture are not semantic or model quality metrics.
