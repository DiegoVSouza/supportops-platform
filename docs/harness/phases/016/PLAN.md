# PLAN — Durable 15-minute authorization lease

## allowed_write_paths
- `migrations/004_authorization_lease.sql`, `supportops_platform/persistence.py`, `supportops_platform/contracts.py`
- `supportops_platform/async_tasks/durable.py`, `supportops_platform/service_runtime.py`, `supportops_platform/api/app.py`
- `scripts/check_services.py`, `tests/**`
- `docs/harness/phases/016/**`, `docs/harness/security.md`, `docs/harness/feature_list.json`, `docs/harness/progress.md`
- `artifacts/evidence/phase-016-*`

## forbidden_changes
- Do not persist bearer tokens, client secrets, refresh tokens, or expand scopes on resume.
- Do not extend expiry on retry, duplicate delivery, or approval.
- Do not change public routes or claim immediate external revocation.
- No live model/provider call, package publish, or deployment.

## Tasks
1. Add migration 004 to set and backfill immutable `authorization_expires_at` at 15 minutes from job creation.
2. Reject expired jobs at pending dispatch, worker execution, and approval resume; return an actionable HTTP 409 for an expired resume.
3. Ensure the simulated irreversible effect checks the lease in the same database transaction that records the effect.
4. Add service evidence for pre-dispatch expiry, expired HITL resume, unchanged expiry through retry/recovery, and no effect after expiry.
5. Run P05 fast/full gates and lab documentation checks; reconcile security docs and feature status.

## Verification
- `uv run --locked python scripts/check_fast.py`
- `uv run --locked python scripts/check_full.py` with isolated Compose project and free ports
- `python scripts/harness/check.py --root . --project p05 --docs`

Plan review: accepted; policy selected by user on 2026-10-22.
