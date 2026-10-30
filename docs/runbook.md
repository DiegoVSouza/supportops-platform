# Local Operations Runbook

## Fake-mode demonstration

Run from this repository with Python 3.13 and the committed lock:

```powershell
uv sync --locked
$env:LLM_MODE = "fake"
uv run --locked python scripts/demo.py
```

This uses process-local API state, deterministic ticket/knowledge fixtures, and no
provider calls. It does not prove service durability or semantic retrieval quality.

## Local verification

```powershell
uv run --locked pytest
uv run --locked python scripts/verify_packages.py
uv run --locked python scripts/check_full.py
```

`check_full.py` executes unit, package, fixture, Docker promtool, service and crash
recovery gates. Missing required services or an explicit `--skip-services` returns
INCOMPLETE/nonzero. Use the isolated Compose stack on loopback ports; it requires
PostgreSQL with pgvector, Redis and LocalStack. Fixture model quality remains PENDING.

## MCP transport boundary

The Streamable HTTP server requires a `TokenVerifier` and `AuthSettings`; configure
the production resource URL and an allowlist for the actual serving host when mounting
the returned ASGI app. Identity comes from the MCP SDK verified access-token context.
Never accept tenant, roles, or scopes from tool/model arguments. The local test uses
the SDK Streamable HTTP client over ASGI transport and is not a deployed network test.

## Retrieval boundary

The PostgreSQL migration is `migrations/002_pgvector_knowledge.sql`. It requires
pgvector 0.8.7, the `vector` extension, a `vector(32)` embedding, cosine distance, HNSW,
and full-text GIN. The 32-dimensional hashed fake embedding is test-only; replace it
with a versioned real embedding model and evaluate against traceable data before
claiming semantic retrieval quality. No service or live model evaluation is recorded.

## Roll back a migration

`migrations/down/` reverses each file. Migrations run automatically at start, so first stop the API and worker and deploy the previous image, or they will reapply them. Take a `pg_dump` before running a down file: 002 and 003 destroy data, and 004 only drops a column. Apply them newest first with `psql -f`. The up, down, up cycle is proven by `python scripts/harness/check_migrations.py` in the lab root.

## Readiness

`/healthz` means the process is alive. `/readyz` means PostgreSQL and Redis answer, and returns 503 with the failed dependency name otherwise. Route traffic on `/readyz`; restart on `/healthz`.
