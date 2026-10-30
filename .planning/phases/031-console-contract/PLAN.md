# Plan

1. Tests first in `tests/test_api_security.py`: tenant isolation, scope denial, state filter, and payload shape of the new models.
2. Add `list_approvals` to `InMemoryStore` and `PostgresStore`, response models and the route in `api/app.py`.
3. Bump to 0.4.4, regenerate `openapi.yaml`, write ADR-009, update README, progress and decisions.

allowed_write_paths: `supportops_platform/api/app.py`, `supportops_platform/repositories.py`, `supportops_platform/persistence.py`, `supportops_platform/__init__.py`, `tests/test_api_security.py`, `pyproject.toml`, `uv.lock`, `openapi.yaml`, `scripts/export_openapi.py`, `scripts/check_wheel_consumer.py`, `docker-compose.services.yml`, `docs/decisions/ADR-009-console-contract.md`, `docs/harness/**`, `README.md`, `README.pt-BR.md`, `.planning/phases/031-console-contract/**`, `artifacts/evidence/console-contract-031/**`.

forbidden_changes: changing an existing payload or status code, weakening tenant or approver checks, new auth paths, migrations, provider or live calls, ledgers, committing secrets.

llm_mode: fake. budget: USD 0. validation: `uv run --locked pytest -q` and `uv run --locked python scripts/export_openapi.py --check`.

stop conditions: three failed attempts on one failure, or any existing test needing weakening.
