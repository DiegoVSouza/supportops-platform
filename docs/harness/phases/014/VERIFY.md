# VERIFY — Isolated full service gate

| Gate | Command | Exit | Evidence | Status |
| --- | --- | ---: | --- | --- |
| Harness documentation gate | `python scripts/harness/check.py --root . --project p05 --docs` from the lab root | 0 | `artifacts/evidence/phase-014-harness-docs-check.txt` | PASS |
| Fast | `uv run --locked python scripts/check_fast.py` | 0 | `artifacts/evidence/phase-014-fast.txt` | PASS |
| Full local acceptance, including service integration and crash recovery | `uv run --locked python scripts/check_full.py` (no `--skip-services`); isolated project `p05-full-gate-014`, dedicated `P05_*_PORT` values | 0 | `artifacts/evidence/phase-014-full-gate.txt`; `phase-014-service-summary.json` | PASS_LOCAL_FAKE_MODE; 103 tests |
| Isolated stack cleanup and pre-existing stack preservation | Docker inventory after full gate | 0 | `artifacts/evidence/phase-014-cleanup.txt` | PASS; temporary resources removed, 10 existing P05 services remain running |
| External identity acceptance and queued-job revocation | No configured external issuer or revocation contract | — | `docs/harness/feature_list.json` | INCOMPLETE |
| Replay/model quality/cost/comparable latency | No valid cassette for two configurations and no live run authorized | — | `docs/harness/feature_list.json` | PENDING |

The first service attempt exposed a hard-coded public MCP host in the integration checker; the test now uses the configured service address over Compose TCP. Diagnostic evidence is in `artifacts/evidence/phase-014-first-full-gate.txt`. The full local fake-mode PASS does not close external identity or model-evaluation gates.
