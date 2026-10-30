# Plan

1. Tests first for `/readyz`: healthy, failed dependency, absent from the schema.
2. Add `ping` to `PostgresStore` and `RedisRateLimiter`, and the route. Add the down SQL.
3. Document rollback in `docs/runbook.md`.

allowed_write_paths: `supportops_platform/api/app.py`, `supportops_platform/persistence.py`, `supportops_platform/auth/rate_limit.py`, `tests/test_api_security.py`, `migrations/down/**`, `docs/runbook.md`, `docs/harness/progress.md`, `.planning/phases/032-readiness/**`, `artifacts/evidence/readiness-032/**`.

forbidden_changes: public contract, `openapi.yaml`, existing migrations, provider calls.

llm_mode: fake. budget: USD 0. validation: `uv run --locked python -m pytest -o addopts= -q`. stop conditions: three failed attempts on one failure.
