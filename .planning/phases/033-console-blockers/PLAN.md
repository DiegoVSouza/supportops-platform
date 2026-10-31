# Plan

1. Tests first in `tests/test_api_security.py`.
2. Implement in `api/app.py`, `async_tasks/durable.py` and `service_runtime.py`.
3. Bump to 0.4.5, regenerate `openapi.yaml`, write ADR-010, correct ADR-009.
4. Prove the Postgres path through the lab stack e2e and `scripts/check_services.py`.

allowed_write_paths: `supportops_platform/api/app.py`, `supportops_platform/async_tasks/durable.py`, `supportops_platform/service_runtime.py`, `supportops_platform/__init__.py`, `tests/test_api_security.py`, `pyproject.toml`, `uv.lock`, `openapi.yaml`, `scripts/export_openapi.py`, `scripts/check_wheel_consumer.py`, `docker-compose.services.yml`, `docs/decisions/**`, `docs/harness/**`, `README.md`, `.planning/phases/03*/**`, `artifacts/evidence/console-blockers-033/**`.

forbidden_changes: weakening tenant, approver or self-approval checks, migrations, provider or live calls, ledgers, removing a test.

llm_mode: fake. budget: USD 0. validation: `uv run --locked python -m pytest -o addopts= -q`. stop conditions: three failed attempts on one failure.
