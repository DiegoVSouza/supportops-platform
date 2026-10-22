# PLAN — Complete remaining authorized local remediation

allowed_write_paths: supportops_platform/**; scripts/**; tests/**; migrations/**; artifacts/**; docs/**; infra/**; agent/**; evals/**; .github/workflows/**; .gitignore; .dockerignore; pyproject.toml; uv.lock; openapi.yaml; docker-compose*.yml; Dockerfile; .env.example; README.md; README.pt-BR.md

forbidden_changes: root roadmap, sibling source imports, shared kit changes, unrelated preexisting files/stacks, test weakening, external deploy/publish/push/PR/merge, Terraform apply, live/paid LLM.

llm_mode: fake

dependencies: Docker daemon and isolated local PostgreSQL/pgvector, Redis, LocalStack, Prometheus/Grafana/Jaeger/OTel; existing locked tools and approved P00–P04 wheels. Verify variable APIs in official docs and sources.lock.json.

## Observable tasks
1. Add ADR-006/version 0.4.0, durable repositories, native retrieval and atomic Redis limits with regression tests.
2. Connect authenticated API submission, P04 outbox/SQS worker, P01 agent, signed TCP MCP, persisted results and approval resume.
3. Implement cross-process trace propagation, fixture regression/adversarial gates, isolated service stack and E2E checks.
4. Run local/package/service/E2E gates, update OpenAPI and bilingual architecture/security/runbook/knowledge and status.

## Checks
Fast gate before each commit; meaningful red/green tests for changed behavior; unit/contract, package integration, service integration and E2E evidence separately; full gate and staged diff/secret review. Clean-context final verification follows the configured Builder review.

## Stop condition
Stop only the affected check for an unavailable dependency and save INCOMPLETE evidence; continue independent implementation. Leave cassettes/live/external-identity acceptance PENDING/INCOMPLETE. Do not claim external exactly-once from the local ledger.

## Plan review
Reviewed before code: four or fewer observable tasks; owned paths and package boundaries explicit; real-service and negative authorization checks included; public changes scoped in ADR; no missing gate can silently pass.
