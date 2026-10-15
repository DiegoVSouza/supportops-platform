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
Invoke-RestMethod http://127.0.0.1:8080/health
```

The API uses in-memory development storage and explicit fixture tokens. See the
[architecture](docs/architecture.md), [security model](docs/harness/security.md), and
[package integration gate](docs/harness/package-integration.md). Local doubles do not
count as integration with P00–P04. No live LLM or external effects run in this demo.

## Validation

```powershell
uv run --locked pytest
uv run --locked python scripts/check_full.py
```

`check_full.py` returns exit code 2 while required versioned package integrations are
not approved. Review `artifacts/evidence/` for saved command output and gate status.

## Status

API authentication, tenant filtering, refund approval transitions, and request bounds
have local tests. Database durability, queue recovery, end-to-end traces, the P01/P02/
P03/P04 artifact integrations, replay evaluation, and service-backed deployment
checks remain incomplete or pending. No model metrics are claimed.
