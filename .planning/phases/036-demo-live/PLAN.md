# Plan — 036 demo-live-v1

allowed_write_paths: `supportops_platform/agents/demo_live.py`, `agents/triage.py`, `api/app.py`, `service_runtime.py`, `tests/test_demo_live.py`, `openapi.yaml`, `artifacts/evidence/demo-live-v1/**`, `.planning/phases/036-demo-live/**`, `docs/harness/*`.
forbidden_changes: removing either guard, a live call, a credential in any file, weakening a test.

1. Ledger (memory and Postgres) and key ring. 2. Client with the accounted receipt contract. 3. Route from `run_configured_triage`. 4. `llm_steps` in API and worker result, OpenAPI regenerated. 5. Tests with a fake transport; Postgres tests against a throwaway server. 6. Regenerate the P06 client (separate commit in P06).
