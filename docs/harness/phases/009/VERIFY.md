# VERIFY — Durable local service runtime

| Layer | Command | Exit | Evidence | Status |
| --- | --- | ---: | --- | --- |
| Unit/contract/package, fixture quality, OpenAPI, provenance, Docker promtool and service E2E | `uv run --locked python scripts/check_full.py` | 0 | `artifacts/evidence/phase-009-full-gate-final.txt`; service summary and Jaeger trace JSON | PASS local fake-mode acceptance |
| Unit suite | `uv run --locked pytest` | 0 | `artifacts/evidence/phase-009-unit-final.txt` | 86 passed |
| Deliberately degraded fake evaluation | `uv run --locked python scripts/check_quality.py --degraded` | 1 (expected) | `artifacts/evidence/phase-009-full-gate-final.txt` | Regression rejected |
| Worker crash after effect commit | `docker compose -p p05-remediation-009 -f docker-compose.services.yml exec -T worker python scripts/check_worker_crash.py` | 0 | `artifacts/evidence/phase-009-crash-recovery.txt` | Job recovered; one product effect row |
| Required service omission | `uv run --locked python scripts/check_full.py --skip-services` | 2 | `artifacts/evidence/phase-009-required-services-omitted.txt` | INCOMPLETE fail-closed |
| P05 0.4.0 isolated wheel consumer and migration | `uv build --offline --wheel`; isolated `uv pip install`; resource load and `PostgresStore.migrate()` | 0 | `artifacts/evidence/phase-009-wheel-build.txt`; `phase-009-wheel-install.txt`; `phase-009-wheel-consumer.txt` | PASS; SHA-256 in sources lock |
| External identity provider and model evaluation | Not configured/authorized | — | `docs/harness/feature_list.json` | INCOMPLETE / PENDING |

`LLM_MODE=fake` was enforced. No live model, external refund, cloud deploy, or Terraform apply occurred.
