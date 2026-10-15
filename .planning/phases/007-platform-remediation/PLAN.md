# Plan — Phase 007: Platform remediation

```yaml
project: p05
requirement_ids: [P05-007-001, P05-007-002, P05-007-003, P05-007-004, P05-007-005]
allowed_write_paths: [.planning/phases/007-platform-remediation/**, supportops_platform/**, tests/**, evals/**, scripts/**, openapi.yaml, pyproject.toml, uv.lock, docker-compose.yml, Dockerfile, infra/**, .github/workflows/**, docs/**, agent/**, shared/**, artifacts/evidence/**, artifacts/runs/**, artifacts/packages/**, docs/harness/**, README.md, README.pt-BR.md]
forbidden_changes: [sibling source imports or edits, silent API changes, weakened tests, fabricated evidence, live/paid LLM calls, deployment/apply, push/publication/PR/merge]
dependencies:
  - P00 approved installed wheel: supportops-foundation 1.0.1, source 607b7603bd40728ffa58745badac0ffd10c70090, SHA-256 DF4292756676D02490A908B609B8F9474F35F3C5F56131809F3E4A83659B4795
  - P01 approved local wheel: supportops-agents 0.1.1, source 4c70b1ea3e23606dfe60ffae77567417de53a3f7, artifact commit 14eea0ae9b32e90f52493a8cdcb8db44a98681ff, SHA-256 DD77E9B91F2D9BA7AC84178BBB557E0EA50BDE954554A528B4632DEC18DDB51F; P05 version assertion passed
  - P02 approved local wheel: supportops-ai-toolkit 0.2.0, source b4966c54fa3feda3ff1eae36ee872e5c407a4102, SHA-256 7126517f9c64202b034b8a067dedf29e1313bb3139f15a984e93660654eb4d10; P05 version assertion passed
  - P03 approved local wheel: supportops-obs 0.3.1, source e191f17d4649f40d6dea7057d3b52729dbbb1389, artifact commit 25311bc49937a80e17c700b00a95ade9fb5ce9b8, SHA-256 82b3a79aacd0ac4faa1082087c0237487264b2a6497d9b77b79c1d6bb86f66a8; P05 consumer test passes
  - P04 approved local wheel: supportops-async 0.1.2, source 3aa96ec9d3fa2f85f771d9b5aaa4c5ab3641034d, artifact commit d9f01a83bc49990c583250dec8b1d6f5c87923b0, SHA-256 a41c2a5a6c797e3913a510321d6859b5ab3be73b3f796eb7e9b1ea76fe6f5fd8; P05 idempotency/worker consumer test passed
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
1. Reconcile OpenAPI routes with the original brief; preserve compatibility or add ADR, version update, and consumer updates. Verify exact local wheel provenance and official MCP SDK/protocol versions in sources.lock.
2. Complete the feasible fake-mode integration: approved installed wheels, P04 worker, P01 agent, tenant-scoped pgvector/hybrid retrieval contract, and Streamable HTTP MCP authentication from verified transport identity; retain service E2E as INCOMPLETE until PostgreSQL/pgvector and Redis run.
3. Add integrated trace/dashboard/alert checks and required P02 adversarial/degraded CI gate. Run unit, package, service, E2E, and agent checks separately; update state/docs from evidence and retain pending metrics.

## Plan review
Coordinator review: accepted. Three observable tasks cover all five requirements; paths are confined to P05. Package/API changes require provenance and version controls. Service and replay dependencies have explicit INCOMPLETE/PENDING handling. No external actions are allowed.

## Stop condition
Finish only with command, exit code, and output saved for each executed gate. Do not mark absent service/replay/model gates PASS.
