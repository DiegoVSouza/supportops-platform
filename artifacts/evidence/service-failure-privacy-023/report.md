# Phase 023 — Isolated service failure privacy

Status: **PASS for local fake/service controls; model quality and promotion remain PENDING/INCOMPLETE.**

## What was verified

- Through the actual `ServiceWorker`, P05 mapped a synthetic `ValueError` to `invalid_input` before the installed P04 task store persisted it. The task failure outbox contains only the safe code; the private sentinel is absent.
- The actual authenticated task API masked a deliberately seeded legacy backend error to `worker_failure`; the unauthenticated request returned 401. The sentinel did not appear in the API response.
- The probe did not observe its own `worker.run`/`agent.triage` trace in Jaeger (`trace_export_observed=false`). No trace delivery claim is made for the injected failure. The phase 022 in-memory exporter regression passes, and the full service acceptance separately observed correlated traces for normal service execution.
- Full locked acceptance: 133 tests passed, retrieval fixture, package provenance, OpenAPI, positive and negative fake controls, and isolated PostgreSQL/Redis/API/worker/MCP/telemetry service E2E and kill-after-effect recovery; exit 0. `check_fast.py` passed. Model-quality assertions remain `PENDING` because these are fake fixtures.

## Isolation and provenance

- Product source, package metadata/lock, and evaluation data/rubric are unchanged from the phase 022 candidate at `7bb496d16ad3ba0b175037a6a658f45a88eba61d`. Only test/service-check harness code and phase documentation changed.
- Services ran in `p05-phase023-failure-privacy`, fake mode, with dedicated free loopback ports and the already-local `supportops-platform:groq-live` image (`sha256:0af6c40c175c5fa2f5278c01dac843b3978635ab36b9ee947071c75649203f30`). Current P05 source/scripts were bind-mounted read-only. No image was pulled, provider/key/paid usage/customer data was used, or external endpoint connection succeeded. The attempted `--network=none` build failed before image creation because `uv==0.12.7` is not vendored; details are retained in phase evidence.
- Before/after inventory: 102 containers, 21 networks, and 89 volumes. Container identities and normalized states match; network and volume inventories match. No phase-owned resource remains. The exact status text for unrelated `gossett_backend` advanced from `Restarting (1) 56 seconds ago` to `Restarting (1) 21 seconds ago`; this container was not targeted.
- The service run exposed two stale test expectations for raw authorization-expiry prose. They now require `authorization_expired`, preserving the no-effect and denied-late-approval assertions. Initial failed runs remain in evidence.

## Remaining gates

Real-model quality, campaign dispatch/approval/quota, human and independent review, and promotion remain `PENDING`/`INCOMPLETE`. This local verification is not live readiness or promotion approval.

## Evidence

- Full gate command/output: `full-verified-command.txt`, `full-verified-output.txt`.
- Fast gate: `fast-committed-source-command.txt`, `fast-committed-source-output.txt`.
- Focused tests and initial failures: `focused-command.txt`, `focused-output.txt`, `full-output.txt`, `full-retry-output.txt`.
- Targeted service probe: `targeted-service-retry2.txt`.
- Docker snapshots and comparison: `../../../.planning/phases/023-service-failure-privacy/evidence/`.
