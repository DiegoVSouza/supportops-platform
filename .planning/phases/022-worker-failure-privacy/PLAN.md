# Plan — Safe worker failure reporting

## Execution controls

- `llm_mode`: `fake`; zero provider calls, credentials, network, Docker, services, external effects, or paid spend.
- `allowed_write_paths`:
  - `.planning/phases/022-worker-failure-privacy/**`
  - `supportops_platform/async_tasks/failures.py`
  - `supportops_platform/async_tasks/queue.py`
  - `supportops_platform/async_tasks/durable.py`
  - `supportops_platform/service_runtime.py`
  - `supportops_platform/api/app.py`
  - `tests/test_async_tasks.py`
  - `tests/test_api_security.py`
  - `tests/test_service_retry_policy.py`
  - `docs/architecture.md`
  - `docs/harness/failures.md`
  - `docs/harness/feature_list.json`
  - `docs/harness/progress.md`
  - `docs/knowledge/P05-async.md`
  - `artifacts/evidence/worker-failure-privacy/**`
- `forbidden_changes`: `openapi.yaml`, database schema/migrations, public routes or response schema, task status/retry/idempotency contracts, prompts/tools/refund behavior, RAG sources/corpus, datasets/rubrics/eval ledgers, campaign budgets/approvals, package versions/wheels/provenance, `.env*`, Docker/Compose/Terraform configuration or scripts, existing evidence, running containers/volumes/networks, other repositories, harness-kit, provider/credential/network/service access, paid spend, deployment/publication/push, customer data, or external effects.
- Budget: USD 0; no provider calls or token consumption.
- Validation: `uv run --locked pytest` for async queue, API security, service retry policy and durable error tests; `uv run --locked python scripts/check_fast.py`; `uv run --locked python scripts/check_full.py --skip-services`. Save exact commands, exit codes, sanitized output and protected artifact hashes. Do not invoke Docker or service lifecycle commands.
- Stop conditions: if sanitization requires a public schema change, P04 wheel replacement, retry-policy change, DB migration, live provider/service, or editing historical task/evaluation data, stop that dependency and document the exact proposal.

## Tasks

1. **Add red failure-privacy regressions** — prove local fake, actual installed P04 worker handoff, durable task read, and authenticated API behavior never expose exception text; retain transient retry coverage.
2. **Normalize errors at producer and response boundaries** — add a fixed error-code helper, sanitize LocalTaskQueue/FakeWorker and P05 ServiceWorker wrapping, and mask unallowlisted durable errors in `DurableQueue.get` and API serialization.
3. **Verify and document offline limits** — run locked focused, fast and full offline checks; compare protected artifacts/config; document service and semantic gates as INCOMPLETE/PENDING; inspect and commit only planned paths.

## Plan check

Self-check against P05's actual local task API, `ServiceWorker.run_job`, installed P04 0.1.4 worker boundary, durable task read, locked fake tests and prior phase 021. This phase does not modify or republish the P04 package. Existing transient exception-group allowlisting is preserved. The current SDD ID 022 is unused and follows the highest existing phase 021. No independent review or human approval has been performed.
