# Plan

1. Implement an injectable fixture-accounted Core client using P05-owned identity/retrieval contracts, strict worker outputs, usage receipts and durable reservations.
2. Test installed Core execution, tenant refusal, expiry/revocation before and between calls, injection refusal, uncertainty/restart and privacy. Run locked focused/fast/full offline gates with fresh scratch and save all commands/exits/output.

allowed_write_paths: .planning/phases/027-accounted-identity-boundary/**; supportops_platform/agents/accounted.py; tests/test_accounted_identity.py; artifacts/evidence/accounted-identity-027/**; docs/harness/progress.md.
forbidden_changes: legacy live guards, historical ledgers/results/manifests, sibling source imports, real IdP or customer data, provider calls/credentials/budgets, Docker lifecycle, refunds, weaker tests and human approval. Fake mode, zero calls/USD 0 paid. max_tries: 3 per failure, no replay of uncertain work. Stop on unexpected external access or uncertainty. Plan-check: implementer self-assessment. Offline acceptance is not HTTP/queue/MCP/live/service acceptance.
