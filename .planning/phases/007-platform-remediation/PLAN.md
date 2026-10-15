# Plan — Phase 007: Platform remediation

```yaml
project: p05
requirement_ids: [P05-007-001, P05-007-002, P05-007-003, P05-007-004, P05-007-005]
allowed_write_paths: [.planning/phases/007-platform-remediation/**, supportops_platform/**, tests/**, evals/**, scripts/**, openapi.yaml, pyproject.toml, uv.lock, docker-compose.yml, Dockerfile, infra/**, .github/workflows/**, docs/**, agent/**, shared/**, artifacts/evidence/**, artifacts/runs/**, artifacts/packages/**, docs/harness/**, README.md, README.pt-BR.md]
forbidden_changes: [sibling source imports or edits, silent API changes, weakened tests, fabricated evidence, live/paid LLM calls, deployment/apply, push/publication/PR/merge]
dependencies:
  - P00 approved installed wheel: supportops-foundation 1.0.1, source 607b7603bd40728ffa58745badac0ffd10c70090, SHA-256 DF4292756676D02490A908B609B8F9474F35F3C5F56131809F3E4A83659B4795
  - P01 approved installed wheel: supportops-agents 0.1.0, source af06f4c564d2e601ac8009ecb32ae7e529b72c83, SHA-256 9F360E98FC1DF9D9D10CCDAB51F0AF0CCEF5F1A17CD49CEFEC9E2E3A8A4BED8
  - P02 approved installed wheel: supportops-ai-toolkit 0.1.0, source 00a5f9b8e1f9c78ea26f09839d24847cfcfbf6f6, SHA-256 5B7F1BBD9DD015620D5CB9CBCF6B4B39B1D2DC668805B066E7A2D9A930D48A52
  - P03 approved installed wheel: supportops-obs 0.1.0, source 7d78bf63f42b03c510792773ad2c9915015120e9, SHA-256 e4e80cd664c97cf38b8fbe5557f10d4c8d247af275412569fb6a1bcbc0f11575
  - P04 approved installed wheel: supportops-async 0.1.1, source 6a074e906b080fdb837907237787f623f17c3e3c, SHA-256 250985c33e334b1e8f1c31bf8dcfe770ed8ff20419b96decaa9adf9d05010c1f; reverify because upstream is being remediated
  - PostgreSQL with pgvector, Redis, and LocalStack; absent service dependencies leave service acceptance INCOMPLETE
  - Current official MCP SDK/protocol docs and exact tested versions in docs/harness/sources.lock.json
  - Traceable replay cassettes; absent cassettes keep replay evaluation PENDING
llm_mode: fake
checks: ["uv run python scripts/check_fast.py", "uv run python scripts/verify_packages.py", "uv run python scripts/check_full.py", "service E2E with PostgreSQL/pgvector, Redis, and LocalStack", "fake adversarial and retrieval evaluations"]
evidence_directory: artifacts/evidence/
stop_condition: Missing services are INCOMPLETE and missing cassettes keep replay metrics PENDING; stop before unversioned contract changes or external actions.
```

## Context
Read the phase SPEC/VERIFY, `docs/intake/ORIGINAL-BRIEF.md`, original P05 brief, harness decisions/progress/features/agent card, current API/ADR/security docs, package provenance, and prior phase evidence. Never import sibling source.

## Tasks
1. Reconcile OpenAPI routes with the original brief; preserve compatibility or add ADR, version update, and consumer updates. Reconfirm installed wheel provenance and official MCP SDK/protocol versions in sources.lock.
2. Complete durable authenticated ticket path through approved installed wheels, P04 worker, P01 agent, PostgreSQL/pgvector, Redis, hybrid retrieval, network-authenticated MCP, approval, and persisted cited response; test tenant and injection protections.
3. Add integrated trace/dashboard/alert checks and required P02 adversarial/degraded CI gate. Run unit, package, service, E2E, and agent checks separately; update state/docs from evidence and retain pending metrics.

## Plan review
Coordinator review: accepted. Three observable tasks cover all five requirements; paths are confined to P05. Package/API changes require provenance and version controls. Service and replay dependencies have explicit INCOMPLETE/PENDING handling. No external actions are allowed.

## Stop condition
Finish only with command, exit code, and output saved for each executed gate. Do not mark absent service/replay/model gates PASS.
