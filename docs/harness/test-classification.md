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

Phase 009 exercises native asyncpg against PostgreSQL/pgvector, Redis limits, durable
API submission through the P04 worker and P01 agent, authenticated MCP over loopback
TCP, API restart recovery, distinct approval resume and worker death after the simulated
effect commit. See `artifacts/evidence/phase-009-full-gate-final.txt`. External identity
provider acceptance remains INCOMPLETE.

## Agent and retrieval evaluations

`scripts/eval_retrieval.py` evaluates four deterministic retrieval fixtures. Its
`hit_at_3=4/4` output is fixture coverage only, not agent or LLM quality. Agent behavior
is tested with the P01 fake runner; no replay cassette, degraded-output regression
threshold now rejects a deliberately degraded fake execution. This proves regression
gate wiring only; semantic and model quality remain `PENDING` without replay cassettes
or authorized comparable model runs.

The full local command is `uv run --locked python scripts/check_full.py`. Its output and
exit code are saved in `artifacts/evidence/followup-full-gate.txt`.
