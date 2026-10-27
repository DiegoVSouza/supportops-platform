# Phase 024 plan

## Ownership

Allowed write paths:

- `.planning/phases/024-failure-trace-export/**`
- `scripts/check_failure_privacy.py`
- `supportops_platform/async_tasks/durable.py`
- `supportops_platform/service_runtime.py`
- `supportops_platform/integrations/observability.py`
- `tests/test_service_retry_policy.py`
- `artifacts/evidence/failure-trace-export-024/**`
- `docs/harness/progress.md`
- `docs/harness/failures.md`
- `docs/harness/feature_list.json`
- `docs/knowledge/worker-failure-privacy.md`

Forbidden changes:

- `.env*`, runtime model/provider dispatch/budget/campaign config, datasets/splits/rubrics/graders/thresholds, historical phase-023 or prior evidence, package lock unless a separate SDD phase is created, P04 source, sibling source imports, root lab files, unrelated projects/stacks/images/volumes, tenant/customer data, paid/provider/network use, external identity/deploy/publication, or approvals.

## Tasks

1. Reproduce the trace-context/export diagnosis offline from P05-owned code and tests; identify the exact cause behind phase 023's zero-span readback. Add regression coverage for the failure trace contract and content-free probe output. If code changes are required outside listed paths or package metadata, stop and make a separate ownership phase.
2. Implement the smallest P05-owned correction, run fast, focused and complete offline locked checks, review staged diff/secrets, and commit the candidate before starting services.
3. With the cached `supportops-platform:groq-live` image and read-only P05 source mounts, start only `p05-phase024-failure-trace`, run one fresh synthetic failure probe with a unique key/trace, verify Jaeger spans and sentinel absence, then run full fake service acceptance and kill-after-effect recovery. Reconcile all Docker inventories, clean only the phase project, update docs/evidence and commit. A failed probe is recorded and not replayed.

## Validation

- `uv run --locked python scripts/check_fast.py`
- `PYTHONPATH=. uv run --locked pytest -q tests/test_service_retry_policy.py tests/test_async_tasks.py`
- `PYTHONPATH=. uv run --locked pytest -q tests`
- `LLM_MODE=fake uv run --locked python scripts/check_full.py` in isolated fake mode after service setup, per existing harness contract.
- `docker compose -p p05-phase024-failure-trace -f docker-compose.yml -f .planning/phases/024-failure-trace-export/compose.override.yml config --quiet`
- `docker compose ... up --no-build --pull never -d --wait`; run one new, one-shot service failure probe, check trace by GET only, then full fake acceptance and phase-owned cleanup.
- Verify image `supportops-platform:groq-live` remains `sha256:0af6c40c175c5fa2f5278c01dac843b3978635ab36b9ee947071c75649203f30`; compare pre/post 102 containers, 21 networks, 89 volumes and exact unrelated identities/states.

## Budget and stop conditions

- USD 0 and zero model/provider calls; local fake service calls only. Existing image only; no build or pull.
- Stop before startup if a required port is occupied, phase namespace is nonempty, cached image/source compatibility differs, old evidence/fingerprints differ, any bind is non-loopback, or P05 service configuration routes outside the isolated project.
- Stop on any unexplained trace gap, span/private content leak, fake-mode mismatch, service/full-gate failure, unrelated Docker mutation, or uncertain cleanup. Preserve logs and do not retry the new semantic failure task.
- No human/independent/model-quality/identity/promotion approval is inferred.
