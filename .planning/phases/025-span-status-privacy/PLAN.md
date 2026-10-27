# Phase 025 plan

## Ownership

`allowed_write_paths`:

- `.planning/phases/025-span-status-privacy/**`
- `supportops_platform/service_runtime.py`
- `scripts/check_failure_privacy.py`
- `tests/test_service_retry_policy.py`
- `artifacts/evidence/span-status-privacy-025/**`
- `docs/harness/progress.md`
- `docs/harness/failures.md`
- `docs/harness/feature_list.json`
- `docs/knowledge/worker-failure-privacy.md`

`forbidden_changes`: `.env*`, dependency/package metadata or locked wheels, model/provider dispatch, campaign ledgers/config, datasets/splits/rubrics/graders/thresholds, prior phase evidence or phase 024 history, P04/sibling/root-lab source, existing P05 stacks, unrelated containers/images/volumes/networks, customer content, provider/external network, paid usage, external identity/deployment/publication, and approvals.

## Tasks

1. Add an in-memory regression for automatic exception status descriptions, fix all P05 span call sites to set `record_exception=False, set_status_on_exception=False`, strengthen the AST invariant, and update the one-shot privacy probe only if its diagnostic needs adjustment. Run plan check, fast gate, focused tests and full offline locked gate. Review and commit the candidate before starting services.
2. Preflight cached image identity, ports, unique Compose namespace, loopback binds and Docker inventories. Start only `p05-span-status-privacy-025`, run one fresh synthetic failure task through the real isolated API/worker, and do GET-only bounded Jaeger verification without persisting trace content. Stop immediately on a leak or uncertain outcome; never replay.
3. Run the complete fake service gate and kill-after-effect recovery on that same phase-owned stack. Reconcile resource identities/counts, clean only the phase project, record sanitized evidence and hashes, update state/failure/knowledge docs, review staged diff/secrets, and commit evidence.

## Validation commands

- `uv run --locked python scripts/check_fast.py`
- `PYTHONPATH=. uv run --locked pytest -q tests/test_service_retry_policy.py tests/test_async_tasks.py`
- `PYTHONPATH=. uv run --locked pytest -q tests`
- `docker compose -p p05-span-status-privacy-025 -f docker-compose.services.yml -f .planning/phases/025-span-status-privacy/compose.override.yml config --quiet`
- `P05_COMPOSE_PROJECT=p05-span-status-privacy-025 P05_COMPOSE_OVERRIDE=.planning/phases/025-span-status-privacy/compose.override.yml P05_EVIDENCE_DIRECTORY=span-status-privacy-025 P05_SKIP_BUILD=1 LLM_MODE=fake uv run --locked python scripts/check_full.py`
- Capture exact command, exit code, sanitized output, source/image digests, and Docker inventory before/after under `artifacts/evidence/span-status-privacy-025/`.

## Budget and stop conditions

- USD 0, zero provider/model calls; local fake synthetic task only. No credentials read. No image build/pull or external endpoint.
- Reuse only the cached image digest `sha256:0af6c40c175c5fa2f5278c01dac843b3978635ab36b9ee947071c75649203f30`. Ports: API 38225, PostgreSQL 36525, Redis 36425, MCP 38226, OTLP 36522, Jaeger 36691, Prometheus 39026, Grafana 33026; verify all are free at execution time.
- Stop before startup if image differs, a port is occupied, namespace is nonempty, compose bind is not loopback, or existing stack inventory cannot be preserved. Stop on any sentinel appearance, missing/ambiguous spans, export timeout, non-fake mode, provider/external route, unrelated resource mutation, or uncertain cleanup. Preserve the result; never resubmit the failed task.
- Human/independent/model-quality/campaign/promotion gates remain pending until performed independently.
