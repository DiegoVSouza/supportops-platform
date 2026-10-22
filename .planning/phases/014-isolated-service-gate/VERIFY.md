# Verify

Run `uv run --locked python scripts/check_fast.py` and `uv run --locked python scripts/check_full.py` with a fresh `P05_COMPOSE_PROJECT`, phase-specific `P05_EVIDENCE_PREFIX`, and verified-free loopback ports. The full command must omit `--skip-services`. Save each command, exit code, and output in `artifacts/evidence/phase-014-fast.txt` and `phase-014-full-gate.txt`.

Confirm the unique Compose project has no remaining containers or volumes after the run. Record cleanup evidence in `artifacts/evidence/phase-014-cleanup.txt`. Do not report external identity, model quality, cost, or latency as complete based on this local fake-mode gate.
