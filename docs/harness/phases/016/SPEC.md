# SPEC — Bound durable job authorization to 15 minutes

P05 currently persists the caller's verified subject, tenant, roles, and scopes in durable jobs with no expiry. Apply the user's selected 15-minute authorization lease, measured from initial API acceptance and never extended by retries or approval waits.

Acceptance:
- New durable jobs receive an immutable expiry at creation, 15 minutes after acceptance.
- Expired jobs are not dispatched or executed; the worker checks the lease before processing and before the simulated refund effect.
- HITL approval after expiry does not resume the job. The API returns HTTP 409, records the job as failed with a safe explanation, and requires a new task submission with fresh authorization and a new idempotency key.
- Retries and recovery preserve the original expiry. Existing rows are backfilled from `created_at + 15 minutes`.
- Tests exercise pre-dispatch expiry, expired HITL resume, and no effect after expiry. Full local services, package, API, and documentation gates pass.

No token or client secret is stored to support revocation checks. The lease bounds the persisted authorization snapshot; it does not claim instantaneous revocation. No external provider calls, model evaluation, publish, or deployment.
