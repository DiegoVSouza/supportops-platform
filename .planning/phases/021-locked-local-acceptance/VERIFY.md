# Verify

- [x] Locked offline layers pass (127 tests, 2 deprecation warnings); failed global-Python evidence retained.
- [x] Full fake service gate exits 0 with security, correlated traces and crash recovery.
- [x] Existing container identities/states preserved (before/after diff empty); temporary containers, volumes and network removed.
- [x] No provider access; campaign and promotion remain INCOMPLETE.
- [x] Evidence includes commands/exits; progress/knowledge updated and staged diff reviewed.

Executed `uv run --locked python scripts/check_full.py` with `P05_COMPOSE_PROJECT=p05-locked-acceptance-021`, `P05_EVIDENCE_PREFIX=locked-acceptance/phase-021`, `LLM_MODE=fake`, and free loopback API/Postgres/Redis/MCP/OTEL/Jaeger/Prometheus/Grafana ports 38120/36420/36320/38121/35320/35620/39020/33020. Result: exit 0, local fake acceptance PASS. Independent clean-context review and real model/campaign gates remain pending.

Evidence directory: `artifacts/evidence/locked-acceptance/`.
