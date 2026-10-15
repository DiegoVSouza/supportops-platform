# Verify — API, authorization, and async

- [x] OpenAPI v1 is versioned 0.2.0, includes ticket, approval, feedback, health, metrics, task, and triage paths, and passes the generated-contract check.
- [x] JWT signature/expiry, scope denial, tenant isolation, and bounded request behavior are covered by API tests.
- [x] Refund approvals store requester identity, deny self-approval, and permit a separate authorized approver once.
- [x] P04 0.1.1 is locked, installed offline, hash-verified, and exercised through its local API/worker contract.
- [ ] PostgreSQL and SQS service-backed recovery/idempotency — INCOMPLETE; local SQLite/in-memory broker tests are doubles.
- [x] Commands, exit codes, and outputs are saved under `artifacts/evidence/`.

Evidence: `artifacts/evidence/followup-full-gate.txt`, `artifacts/evidence/followup-package-gate.txt`.
