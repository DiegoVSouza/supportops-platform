# Plan — Observability and benchmarks

## allowed_write_paths
- `supportops_platform/obs/**`, `supportops_platform/agents/**`
- `benchmarks/**`, `tests/observability/**`, `tests/benchmarks/**`, `docs/**`, `artifacts/**`, `infra/**`

## forbidden_changes
- No P03 source import; install approved package artifact or use a test-only double.
- No real provider benchmark, external publish, or unsupported numerical claim.

## Tasks
1. Define trace context propagation and privacy-safe attributes.
2. Instrument API/queue/worker/agent/LLM/tool/database boundaries and loop detection.
3. Add dashboard/alerts and two replay configuration comparisons.
4. Save trace, benchmark inputs/results, and evidence; use PENDING without real runs.

## Stop condition
Stop integration if P03 artifact is not approved; do not represent unit spans as an end-to-end trace.
