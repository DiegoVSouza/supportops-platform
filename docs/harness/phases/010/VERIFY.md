# VERIFY — Transport recovery and durable authorization

| Gate | Command | Exit | Evidence | Status |
| --- | --- | ---: | --- | --- |
| Plan review | Manual against SPEC/PLAN and phase ownership; `git diff --check` | 0 | `artifacts/evidence/phase-010-planning-review.txt` | PASS |
| Regression reproduced before fix | `uv run --locked pytest tests/test_service_retry_policy.py` | 1 expected | `artifacts/evidence/phase-010-retry-red.txt` | PASS; demonstrates old P04 status `failed` |
| Focused policy and P04 worker retry | `uv run --locked pytest tests/test_service_retry_policy.py` | 0 | `artifacts/evidence/phase-010-retry-green.txt` | PASS; 7 passed, including real loopback MCP refusal, nested/mixed groups, auth permanence, AWS classes and loop backoff |
| Unit/contract/package | `uv run --locked pytest` | 0 | `artifacts/evidence/phase-010-unit.txt` | PASS; 92 passed |
| Fast gate | `uv run --locked python scripts/check_fast.py` | 0 | `artifacts/evidence/phase-010-fast.txt` | PASS |
| Approved package provenance | `uv run --locked python scripts/verify_packages.py` | 0 | `artifacts/evidence/phase-010-package-gate.txt` | PASS; approved P00-P04 wheels and consumer checks |
| OpenAPI contract | `uv run --locked python scripts/export_openapi.py --check` | 0 | `artifacts/evidence/phase-010-openapi-check.txt` | PASS; API package version 0.4.1 |
| Status/provenance JSON | Validate feature inventory and package source lock | 0 | `artifacts/evidence/phase-010-doc-validation.txt` | PASS |
| Full fake-mode local gate | `uv run --locked python scripts/check_full.py` | 0 | `artifacts/evidence/phase-010-full-gate.txt`; `artifacts/evidence/phase-010-service-summary.json` | PASS local acceptance; services, auth snapshot and crash recovery verified |
| Missing required services | `uv run --locked python scripts/check_full.py --skip-services` | 2 expected | `artifacts/evidence/phase-009-required-services-omitted.txt` | INCOMPLETE fail-closed |
| P05 0.4.1 wheel consumer | Offline build/install and packaged migration against real isolated PostgreSQL/pgvector | 0 | `artifacts/evidence/phase-010-wheel-build.txt`; `phase-010-wheel-install.txt`; `phase-010-wheel-consumer.txt` | PASS; source/artifact commits and SHA-256 in sources lock |
| External identity/revocation | Not configured | — | `docs/harness/feature_list.json` | INCOMPLETE |
| Replay/model quality/cost/comparable latency | No traceable cassette or authorized comparable model run | — | `docs/harness/feature_list.json` | PENDING |

`LLM_MODE=fake` was enforced. No live model, external refund, cloud deploy, Terraform apply, or publication occurred. Local ledgers do not establish exactly-once external effects or production readiness.
