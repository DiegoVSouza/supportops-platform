# Commands and results

All commands ran from `projects/p05`; no credential values or provider responses are recorded.

Text outputs were normalized only by removing trailing whitespace introduced by Docker Compose; command/status lines and substantive output are unchanged.

| Command | Exit | Result |
| --- | ---: | --- |
| `uv run --locked python -m py_compile scripts/check_failure_privacy.py scripts/check_services.py` | 0 | Probe/test harness compiles. |
| `uv run --locked pytest tests/test_service_retry_policy.py tests/test_api_security.py tests/test_async_tasks.py -q` | 0 | 38 focused tests passed. |
| `uv run --locked python scripts/check_fast.py` | 0 | `check-fast: OK`. |
| `docker build --network=none --tag p05-phase023-failure-privacy:local .` | 1 | Offline build stopped at non-vendored `uv==0.12.7`; no image created. |
| `docker run --rm --network none --entrypoint python supportops-platform:groq-live -c "from importlib.metadata import version; print(version('supportops-platform')); print(version('supportops-async')); print(version('supportops-obs'))"` | 0 | Existing local image has P05 0.4.3, `supportops-async` 0.1.4, and `supportops-obs` 0.3.1, matching the locked project. |
| `docker compose -p p05-phase023-failure-privacy -f docker-compose.services.yml -f .planning/phases/023-service-failure-privacy/compose.override.yml up --no-build -d --wait` | 0 | Isolated fake services became healthy. |
| `docker compose ... exec -T api python scripts/check_failure_privacy.py` | 0 | Worker persistence and authenticated API masking passed; direct probe trace not observed. |
| `uv run --locked python scripts/check_full.py` with isolated Compose env recorded in `full-verified-command.txt` | 0 | 133 tests and all service/E2E/crash-recovery controls passed; `check-full: PASS`. |
| `uv run --locked python scripts/check_fast.py` | 0 | Final fast gate passed after service assertion correction. |

The phase-owned `docker compose ... down --volumes --remove-orphans` returned 0. The resulting container, network, and volume inventory reconciliation is in `.planning/phases/023-service-failure-privacy/evidence/docker-inventory-reconciliation.json`.
