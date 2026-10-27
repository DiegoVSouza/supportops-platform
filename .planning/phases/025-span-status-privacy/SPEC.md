# Phase 025 — Prevent exception messages in span status

## Goal

Close the failure-trace leak found in phase 024. P05-owned spans must not export exception event payloads or automatic exception status descriptions. Preserve useful span names and explicitly allowlisted attributes while reducing exception outcome to fixed application error categories outside the span payload.

## Acceptance criteria

1. Every P05-owned `start_as_current_span` call explicitly disables both `record_exception` and `set_status_on_exception`.
2. An in-memory SDK regression drives a synthetic exception through the real `ServiceWorker` span boundaries and asserts the sentinel is absent from span events, status descriptions, attributes, and serialized spans; safe task failure codes remain intact.
3. AST coverage rejects any P05 span call missing either privacy option. A separate control demonstrates the default SDK status behavior so the regression protects the identified cause.
4. Fast, focused, complete offline locked checks pass. Candidate source is committed before service startup.
5. One new isolated fake service failure task (never the phase-024 task) verifies the actual API/worker/OTLP path. Jaeger readback is GET-only and bounded; no raw response is written. The complete isolated fake gate and kill-after-effect recovery pass.
6. Compose lifecycle and before/after inventories prove only the unique phase project changed and its resources were removed.
7. Phase 024 remains FAIL/INCOMPLETE and immutable. No human review, independent review, model-quality approval, external identity acceptance, campaign approval, or promotion is inferred.

## Constraints

- No provider/model call, credential access, paid use, external networking, customer data, public listener, deployment, source import from siblings, package/lock change, or mutation of existing P05 stacks.
- Use only the cached local `supportops-platform:groq-live` image and read-only P05 source/script mounts; no build or pull. Use a unique Compose project and dedicated free loopback ports.
- The synthetic sentinel and raw trace remain transient in process/isolated telemetry only. Evidence contains typed status/counts, command output, and hashes, never response bodies or secret values.
- A leak, uncertain task identity, reused namespace, provider route, unrelated resource change, or cleanup uncertainty stops the phase; never retry a semantic failure.
