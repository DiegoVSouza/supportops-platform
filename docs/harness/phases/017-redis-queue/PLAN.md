# PLAN — P05 Redis queue transport

allowed_write_paths: `supportops_platform/async_tasks/**`; `supportops_platform/service_runtime.py`; `supportops_platform/__init__.py`; `pyproject.toml`; `uv.lock`; `docker-compose.services.yml`; `openapi.yaml`; `artifacts/packages/**`; `scripts/**`; `tests/**`; `docs/harness/**`; `docs/decisions/**`; `docs/architecture.md`; `docs/knowledge/**`; `README.md`; `artifacts/evidence/phase-017-*`.

forbidden: change API/MCP contracts, weaken tenant/auth/lease controls, persist bearer tokens in Redis, use live LLMs, or modify another project.

1. Upgrade the P04 wheel dependency to the tested Redis Streams implementation and update lock/provenance.
2. Configure `DurableQueue` to use the shared Redis URL and a P05 namespace while retaining PostgreSQL outbox and durable state.
3. Verify delivery, retry/reclaim, task idempotency, crash recovery, authorization expiry and human approval against real PostgreSQL and Redis.
4. Run P05 fast/full gates, package checks and lab harness checks; update feature/progress state and evidence.

LLM mode: fake. Stop if crash recovery, authorization expiry or Redis persistence cannot be verified.

Plan review: accepted; Redis carries delivery only, PostgreSQL remains authoritative.
