# Phase 024 — Export failure-path worker traces through isolated services

## Goal

Resolve the phase-023 gap where the real service worker sanitized a synthetic failure but the corresponding `worker.run`/`agent.triage` trace was not observed in Jaeger. Source comparison shows the probe made a single immediate Jaeger GET after OTLP collector flush while the normal service gate polls for eventual trace ingestion. Change the probe to bounded read-only polling, require the expected spans, and verify one fresh failure path without repeating the phase-023 task, key, or trace.

## Acceptance criteria

1. Offline coverage ties the persisted task trace context to the actual P05 worker failure spans and verifies `record_exception=False`, safe fixed error category, and no sentinel in span attributes/events.
2. A read-only diagnostic explains the prior `trace_export_observed=false` result without accessing old task content or replaying its request; diagnostics use only service names, trace IDs, operation names, typed keys, and export/readiness booleans.
3. After the candidate is committed, exactly one new synthetic failure task runs through the isolated P05 API, durable queue, installed P04 worker, and OTLP/Jaeger service path; the new trace contains the expected failure spans and no sentinel/private content.
4. The full locked fake acceptance and kill-after-effect recovery pass on phase-owned services. Existing Docker stacks, images, volumes, phase-023 task/trace, evaluation assets, and P00/P01 remain unchanged.
5. Human/independent review, model quality, external identity and promotion remain PENDING/INCOMPLETE.

## Constraints

- No provider/model requests, credentials, paid use, public listener, cloud effect, deployment, customer data, dataset/rubric/grader/threshold changes, live campaign, or approval inference.
- Use the already-local P05 image with current P05 source mounted read-only; no build, pull or external networking.
- Use a unique phase Compose project with loopback-only ports. Do not touch `p05-live-020` or `p05-remediation-009`.
- Preserve the historical phase-023 missing-trace result as FAIL for that probe; do not overwrite it.
