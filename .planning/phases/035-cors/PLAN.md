# Plan

1. Write `tests/test_cors.py` first (red: module missing).
2. Add `supportops_platform/api/cors.py` and wire `create_app(cors_origins=...)` / `CORS_ALLOWED_ORIGINS`.
3. Run `scripts/check_fast.py`.

allowed_write_paths: `supportops_platform/api/**`, `tests/test_cors.py`, `.planning/phases/035-cors/**`, `artifacts/evidence/cors-035/**`, `docs/harness/**`.

forbidden_changes: business rules, auth checks, the OpenAPI contract, a wildcard origin, removing or weakening a test.

llm_mode: fake. budget: USD 0. validation: `python scripts/check_fast.py`. A version bump, wheel and Fly redeploy belong to the lab deployment phase and need the owner's go.
