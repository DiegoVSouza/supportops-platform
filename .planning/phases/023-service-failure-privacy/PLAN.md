# Plan — Reverify service failure privacy

## Controls

- `allowed_write_paths`:
  - `.planning/phases/023-service-failure-privacy/**`
  - `scripts/check_failure_privacy.py`
  - `scripts/check_services.py`
  - `artifacts/evidence/service-failure-privacy-023/**`
  - `docs/harness/progress.md`
  - `docs/harness/failures.md`
  - `docs/knowledge/worker-failure-privacy.md`
- `forbidden_changes`: product runtime/source, package metadata/lock, datasets/splits/rubric/graders/thresholds, campaign ledgers/registry, credentials, other projects/stacks, existing containers/networks/volumes, external effects, provider access, public deployment, and approvals.
- Mode/budget: `LLM_MODE=fake`; USD 0; no provider/API key/model call. Docker may create only project `p05-phase023-failure-privacy` and its owned temporary resources, then remove them. No image pull; stop if required images are not local.
- Isolated loopback ports: API 38220, PostgreSQL 36520, Redis 36420, MCP 38221, OTLP 36517, Jaeger 36686, Prometheus 39021, Grafana 33021. Before use, verify all are free and the Compose project has no resources. Capture all existing Docker inventories before/after.
- Validation: P05 focused regression, fast gate, full fake service gate with isolated namespace, phase-owned evidence prefix; exact exit/output and source hash. Inspect staged diff and secrets.
- Stop conditions: occupied port/project resource, changed pre-existing container identity/state/network/volume, source candidate drift, non-fake model mode, external network/provider attempt, service failure requiring product source edits, or inability to remove owned resources safely.

## Tasks

1. Add a deterministic service probe that injects only a synthetic sentinel error through the real worker persistence boundary and checks the authenticated API's legacy-error mask; prove sentinel absence without emitting response bodies/secrets.
2. Run the probe and full isolated fake service acceptance, reconcile before/after Docker inventories and candidate fingerprint, record docs/evidence, then review and commit only phase-owned paths.

## Plan check

PASS — project phase 023 follows phase 022; ownership, forbidden paths, budget, local service lifecycle, validation, and stop conditions are explicit. This is implementer plan-check; independent review remains PENDING.
