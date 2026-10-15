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

The API uses in-memory development storage and signed local demo tokens. See the
[architecture](docs/architecture.md), [security model](docs/harness/security.md), and
[package integration gate](docs/harness/package-integration.md). P00–P03 use approved
local wheels; P04 has a tested diagnostic adapter but stays outside the locked gate
because of its FastAPI version conflict. Fake mode creates a process-local random JWT
key; configure `JWT_SECRET` when local tokens must survive restarts. No live LLM or
external effects run.

## Validation

```powershell
uv run --locked pytest
uv run --locked python scripts/check_full.py
```

`check_full.py` returns exit code 2 while the P04 dependency gate is incomplete. Review
`artifacts/evidence/` for saved command output and gate status.
For an in-process walkthrough of ticket intake, task recovery, RAG citations, and
human approval, run `uv run --locked python scripts/demo.py`.

## Status

API authentication, tenant filtering, refund approval transitions, bounded lexical
retrieval, and the in-memory MCP SDK contract have local tests. P00–P03 wheel adapters
are installed and verified. P04's local API diagnostic passes, but its exact FastAPI
dependency conflicts with P05's lock, so the package integration gate remains
incomplete. Database durability, replay evaluation, and service-backed deployment
checks remain pending. The deterministic fixture evaluation is not a model metric.
