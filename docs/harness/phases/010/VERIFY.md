# VERIFY — Transport recovery and durable authorization

| Gate | Command | Exit | Evidence | Status |
| --- | --- | ---: | --- | --- |
| Plan review | Manual against SPEC/PLAN and phase ownership | 0 | `artifacts/evidence/phase-010-planning-review.txt` | PASS |
| MCP exception classification and P04 retry | Pending implementation | — | `artifacts/evidence/phase-010-retry-focused.txt` | INCOMPLETE |
| Unit/package | `uv run --locked pytest` | — | `artifacts/evidence/phase-010-unit.txt` | INCOMPLETE |
| Service E2E/full gate | `uv run --locked python scripts/check_full.py` | — | `artifacts/evidence/phase-010-full-gate.txt` | INCOMPLETE |
| P05 0.4.1 wheel consumer | Offline build/install and real isolated PostgreSQL migration consumer | — | `artifacts/evidence/phase-010-wheel-*.txt` | INCOMPLETE |
| External identity; semantic/model quality/cost/comparable latency | Not configured or authorized | — | `docs/harness/feature_list.json` | INCOMPLETE / PENDING |

LLM mode remains fake. No publish, external deployment, Terraform apply, or paid model call is authorized or performed.
