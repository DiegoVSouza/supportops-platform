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

## 2026-10-27 — Phase 023 service verification

- The first isolated service rerun found two assertions still expected raw `authorization lease expired` prose. Phase 022 correctly maps it to `authorization_expired`; assertions now require that fixed code and retain failed-status, late-approval denial, and zero-effect checks. The corrected full service gate passed.
- A synthetic service-worker exception probe did not observe its trace in Jaeger; no trace-delivery claim is made for that probe. The in-memory exporter regression confirms exception events are disabled, and the full service gate independently verifies correlated traces for normal service execution.
- An offline Docker image build could not install non-vendored `uv` with `--network=none`; no image was created or pulled. The isolated gate used an already-local compatible image with current P05 source/scripts mounted read-only. No existing stack was targeted.

## 2026-10-27 — Phase 024 failure trace leaked exception status description

- The bounded Jaeger probe found the expected spans, but its content-free privacy assertion failed: an exception sentinel was present in the trace. The trace body and sentinel were not retained, and identifiers were not emitted. Do not query or replay that task.
- Offline reproduction with the locked OpenTelemetry SDK confirms `record_exception=False` suppresses exception events but leaves automatic exception status enabled by default; the ERROR status description contains the exception message. P05 spans need both `record_exception=False` and `set_status_on_exception=False`, with regressions covering status description and events. Evidence and the blocked service result are preserved under `artifacts/evidence/failure-trace-export-024/`.

## 2026-10-27 — Phase 025 status-description correction

- Added `set_status_on_exception=False` to every P05-owned span alongside `record_exception=False`. Offline regressions now check the worker and `agent.triage` spans' events, status descriptions, attributes and serialized representation; an AST invariant covers source and scripts. The isolated fake service probe observed both failure spans and confirmed sentinel absence. Full service/crash-recovery gate passed; the Jaeger artifact was reduced to names and counts. Phase 024 remains immutable FAIL; its task was not queried or replayed. Model evaluation and reviews remain pending.
