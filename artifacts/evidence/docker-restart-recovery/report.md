# P05 Docker recovery

## Diagnosis

P05 API and worker repeatedly failed at startup with `psycopg.OperationalError: [Errno -2] Name or service not known`. Their PostgreSQL dependency was stopped after Docker restart. Application services used `on-failure`; infrastructure services had no restart policy. Docker Engine 29.1.3 and Compose v5.0.1 were observed. Sanitized error lines are in `diagnosis.json`; initial state and policies are in `before.json`.

## Repair

`docker-compose.services.yml` now uses `unless-stopped` for all nine services. Applied the same policy to the 19 existing containers owned by `p05-remediation-009` and `p05-live-020`, started their dependencies, and restarted application processes without recreating containers or volumes. Operation commands and exit codes are in `operations.json`. The live worker was explicitly stopped before recovery and remains stopped to prevent unapproved provider dispatch. Fake API and worker modes were verified directly.

## Verification

- Fast gate: exit 0 (`fast-gate.txt`).
- Effective Compose configuration: exit 0; all nine restart policies are `unless-stopped`, all runtime defaults remain fake (`configuration-health.json`).
- Existing API health endpoints on loopback ports 28000 and 58000 returned HTTP 200. PostgreSQL and Redis became healthy. Fake worker restart count remained stable.
- Existing container identities and owned volume names are preserved; `recovery-verification.json` contains the checks. No operation targeted an unrelated project.
- Full isolated fake gate: PASS, exit 0 (`full-gate.txt`, `full-gate-exit.json` and `service-service-summary.json`). Selected project `p05-recovery-021`, loopback ports 38100..38107. Its service test exercises API restart, worker recovery, PostgreSQL/Redis, RAG/MCP, tenant/auth/injection/refund simulation, idempotency, alerts and traces.

The isolated project left no containers, volumes or networks (`isolated-cleanup.json`).

## Limits

No Docker daemon restart was forced because the daemon hosts unrelated stacks. Actual restart policies and application recovery were checked; automatic recovery after a future daemon restart was not directly simulated. `unless-stopped` respects explicit manual stops, including the live worker. Existing application images were retained. No live task, provider call, real refund, external message or campaign was dispatched by this work. Independent clean-context review remains PENDING; broad model evaluation, budget and promotion gates remain unchanged.
