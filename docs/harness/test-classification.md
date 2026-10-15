# Validation classes

## Unit tests

`tests/test_rag.py` covers bounded chunking, tenant filtering, stable citations, and
the deterministic retrieval fixture. `tests/test_async_tasks.py` covers local task
state, retries, and idempotency. `tests/test_package_integrations.py` also checks the
loop guard and toolkit guard at their package boundaries.

## Local integration tests

`tests/test_api_security.py` uses FastAPI `TestClient` for JWT, tenant, refund, task,
feedback, triage, and limit behavior. `tests/test_mcp_tools.py` runs the official SDK
client and server in memory. `tests/test_package_integrations.py` imports the approved
P00–P03 wheels. `tests/test_p04_package_integration.py` runs P04 0.1.1 against SQLite
and an in-memory broker. These checks validate installed local contracts, not external
service operation.

## End-to-end tests

No service-backed E2E test is available. PostgreSQL/SQS task recovery and authenticated
network MCP transport remain `INCOMPLETE`; the current demo uses process-local doubles.

## Agent and retrieval evaluations

`scripts/eval_retrieval.py` evaluates four deterministic retrieval fixtures. Its
`hit_at_3=4/4` output is fixture coverage only, not agent or LLM quality. Agent behavior
is tested with the P01 fake runner; no replay cassette, degraded-output regression
threshold, or authorized live evaluation is available. Those evaluation gates remain
`PENDING`.

The full local command is `uv run --locked python scripts/check_full.py`. Its output and
exit code are saved in `artifacts/evidence/followup-full-gate.txt`.
