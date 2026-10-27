# Failures

Record recurring builder or product failures here before fixing them.

## 2026-10-26 — Application restart without backing services

Observed: P05 API/worker restarted repeatedly with psycopg OperationalError (Name or service not known); PostgreSQL/Redis containers were exited after Docker restart. Cause: inconsistent restart policies, with on-failure only on application processes. Correction: consistent unless-stopped policy in Compose and the existing owned containers, followed by state-preserving dependency recovery. Explicitly stopped services still require manual startup. Evidence: artifacts/evidence/docker-restart-recovery/. No Docker daemon restart was forced because other projects share the daemon.
## 2026-10-26 — Phase 019 campaign accounting

- Unknown provider usage must retain its original call/token/cost reservation. P05 now has a regression for this path so a lost response cannot reduce cumulative usage to zero.
- P05 traces and RAG answers may contain tenant content. Campaign accounting stores only campaign/case/trial IDs and usage; no query, retrieved chunk, answer, citation, or tool arguments belong in the ledger or resume report.

## 2026-10-27 — Phase 022 worker failure privacy

- Local `FakeWorker` previously persisted `str(exc)`, and the authenticated task-status route could return the P04 backend worker's stored exception text. Fixed-code normalization now occurs before local failure persistence, at the P05 service wrapper, in durable task reads, and again at the API boundary. Existing history is not rewritten; read-time masking is tested.
- A new in-memory exporter regression reproduced exception text in the `worker.run` span because `start_as_current_span` defaulted to automatic exception recording. All P05-owned spans now set `record_exception=False`; an AST invariant covers all span call sites.
- Offline full gate passed 133 unit/contract/package/fake-control tests. Service-backed behavior remains INCOMPLETE because this validation intentionally did not run Docker or modify the active P05 stack.
