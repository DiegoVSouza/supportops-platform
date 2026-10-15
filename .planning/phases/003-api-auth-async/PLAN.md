# Plan — API, authorization, and async tasks

## allowed_write_paths
- `supportops_platform/api/**`, `supportops_platform/auth/**`, `supportops_platform/async_tasks/**`
- `tests/api/**`, `tests/auth/**`, `tests/tenant/**`, `openapi.yaml`, `docs/**`, `artifacts/**`

## forbidden_changes
- No tenant bypass, no real refund/email effects, no API contract change without ADR and version update.
- No P04 direct source import; use approved installed artifact or local fake contract.

## Tasks
1. Define versioned OpenAPI schemas and tenant/principal authorization model.
2. Implement authenticated endpoints and tenant-scoped repository checks.
3. Connect the async adapter and enforce HITL for high refunds.
4. Test cross-tenant reads, invalid scopes, rate limits, approval state transitions, and crash/idempotency contracts.

## Stop condition
Stop API freeze if any required route/schema change lacks ADR; stop P04 real integration if artifact gate is not met.
