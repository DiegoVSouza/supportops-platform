# VERIFY — Durable 15-minute authorization lease

| Gate | Command | Exit | Evidence | Status |
| --- | --- | ---: | --- | --- |
| Initial full-gate failure and transaction fix | `uv run --locked python scripts/check_full.py` in isolated project `p05-full-gate-016b` | 2 | `artifacts/evidence/phase-016-debug-full-gate.txt` | Fixed: expired status update was rolled back when the 409 exception was raised inside the transaction |
| Fast gate | `uv run --locked python scripts/check_fast.py` | 0 | `artifacts/evidence/phase-016-fast.txt` | PASS |
| Full service acceptance | `uv run --locked python scripts/check_full.py` with isolated ports/project | 0 | `artifacts/evidence/phase-016-full-gate.txt`; `artifacts/evidence/phase-016-final-service-summary.json` | PASS_LOCAL_FAKE_MODE; 104 tests; expiry and HITL lease checks pass |
| Harness docs gate | `python scripts/harness/check.py --root . --project p05 --docs` | 0 | `artifacts/evidence/phase-016-harness-docs-check.txt` | PASS (0 errors, 0 warnings) |

| Isolated Compose cleanup | `docker ps --filter name=p05-full-gate-016c` | 0 | `artifacts/evidence/phase-016-cleanup.txt` | PASS; no temporary containers remain |

No acceptance claim is made until commands and output are recorded.
