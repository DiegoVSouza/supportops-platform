# PLAN — Recover grouped MCP and SQS transport failures

allowed_write_paths: supportops_platform/service_runtime.py; supportops_platform/mcp/runtime.py; tests/**; scripts/**; docs/harness/phases/010/**; docs/harness/feature_list.json; docs/harness/progress.md; docs/harness/agent-card.md; docs/harness/sources.lock.json; docs/decisions/ADR-007-transport-retry-and-delegation.md; artifacts/evidence/**; pyproject.toml; supportops_platform/__init__.py; openapi.yaml; artifacts/packages/**

forbidden_changes: root roadmap; sibling source imports; shared kit; unrelated files/stacks; test weakening; external deploy/publish/push/PR/merge; Terraform apply; live/paid LLM; changing public routes or MCP schemas.

llm_mode: fake

dependencies: locked P04 0.1.3 worker package, current MCP/botocore stack, localhost closed-port test, Docker Compose services for E2E, existing wheel tooling. Confirm exception types against installed locked packages and official docs, record source versions.

## Observable tasks
1. Add regressions for real MCP loopback connection refusal through P04 retry and for permanent/mixed exception groups; prove authorization snapshot behavior on delayed resume.
2. Normalize only fully transient nested transport groups; handle SQS endpoint/read timeout in the standalone loop while preserving permanent errors.
3. Bump P05 to 0.4.1, add ADR-007 documenting retry and delegation snapshot boundaries, update docs/status and build/provenance the immutable wheel.
4. Run unit/package/service/E2E/full gates, save outputs, update phase verification and portfolio matrix with truthful classifications.

## Checks
Run focused red then green tests, `uv run --locked python scripts/check_fast.py`, `uv run --locked pytest`, package provenance and OpenAPI check, isolated service E2E, and `uv run --locked python scripts/check_full.py`. Save exact commands, exit codes and output under `artifacts/evidence/`. Explicitly stage task files and inspect staged diff/secrets before every commit.

## Stop condition
Stop only dependent service checks if Docker/required services are unavailable; save INCOMPLETE evidence and continue independent tests/docs. Keep external identity INCOMPLETE and semantic quality/model cost/latency PENDING. Do not claim universal exactly-once or production readiness.

## Plan review
Reviewed before code: paths are owned, four observable tasks are independently checkable, contract changes are excluded, immutable release versioning is explicit, and permanent auth failures stay fail-closed.
