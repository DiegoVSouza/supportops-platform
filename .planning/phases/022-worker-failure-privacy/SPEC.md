# Phase 022 — Safe worker failure reporting

Status: IMPLEMENTED — OFFLINE CONTROL PASS. Service-stack verification and external identity remain INCOMPLETE; model quality and human/independent review remain PENDING.

## Goal

Prevent exception content from entering new P05 worker failure state, worker span events, or authenticated task-status responses. Preserve bounded retry behavior by converting transient service failures to the existing P04 `TransientFailure` contract with a fixed message. Convert permanent runner errors to the P04 `PermanentFailure` contract with a fixed allowlisted code. Normalize local fake-worker failures and mask legacy or package-originated raw errors at the P05 API boundary.

## Findings and constraints

- `LocalTaskQueue.fail` stores arbitrary reason text, and `FakeWorker` currently passes `str(exc)`.
- The real P05 `ServiceWorker` uses the installed P04 0.1.4 worker. P04 worker failure text is stored in its task record and read by `DurableQueue.get`; the P05 API returns this as `last_error`.
- P05 `ServiceWorker._run_job` creates `worker.run` spans with the OpenTelemetry default `record_exception=True`. The span context manager can capture exception type/message/stack before `run_job` wraps the error, so worker span exceptions must be explicitly disabled.
- P05's service wrapper already classifies transient transport exceptions. Preserve its exception-group policy and retry behavior, but pass only fixed messages into the installed P04 worker.
- Existing records may contain exception text. Do not rewrite or delete history in this phase; mask non-allowlisted text on the authenticated P05 task-status response.
- Keep API route schema, task statuses, attempt counts, queue caps, database migrations, retries, idempotency, trace fields, dataset, grading, and campaign configuration unchanged.
- Do not touch the running Docker stacks. No provider, credentials, external network/service, customer data, paid spend, or external effect is in scope. Existing MCP protocol tests may use ephemeral pytest-owned loopback listeners; the transport-policy regression may attempt only closed `127.0.0.1:9`. USD 0.

## Acceptance criteria

1. P05 local queue and fake worker persist only a fixed allowlisted error code for new failures; exception content is absent.
2. All P05-owned spans disable automatic exception-event capture. P05 `ServiceWorker.run_job` keeps allowlisted transient failures retryable and wraps permanent errors using only a fixed code before handing them to the installed P04 worker.
3. `DurableQueue.get` and the authenticated `/v1/tasks/{id}` boundary return only allowlisted error codes or `null`; legacy/raw stored values never appear in API responses.
4. Tests exercise the real P04 worker class with P05's service wrapper, local queue failure, durable-read adapter, and authenticated API response. No external service or provider is required.
5. Locked focused tests and fast gate pass. Full offline gate runs with `--skip-services`; service integration stays INCOMPLETE, and prior service evidence/stacks remain untouched.
6. Human review, independent review, external IdP acceptance, semantic model evaluation, broad campaign, canary, and promotion remain PENDING/INCOMPLETE.

## Out of scope

P04 package changes or new wheel provenance, DB migrations, public API schema changes, prompt/RAG/retrieval changes, dataset/rubric/campaign edits, exporter/collector/endpoints or telemetry payload schemas, retries/caps changes, Docker or service lifecycle, provider calls, external identity, release publication, deployment, or promotion.
