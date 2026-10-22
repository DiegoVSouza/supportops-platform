# ADR-007 — Transport retry boundaries and durable authorization snapshot

Status: accepted and implemented in 0.4.1, 2026-10-22.

## Context

The MCP Python client uses structured concurrency; transport failures may arrive nested in `ExceptionGroup`. The P04 worker's retry contract only activates when P05 raises its typed `TransientFailure`. SQS endpoint/read timeouts are also recoverable for the standalone worker loop. A durable P05 job stores caller identity and may resume after a human approval delay.

## Decision

P05 recursively classifies grouped exceptions as transient only when every leaf is an explicit local dependency transport failure: network/timeout errors from MCP/httpx2, PostgreSQL/asyncpg connectivity/serialization errors, or botocore endpoint/connect/read/closed-connection errors. Mixed groups, authorization failures, botocore service `ClientError`, and other application failures remain permanent. The standalone service loop sleeps and retries only this same allowlist; unknown errors still stop the process.

A durable job uses an authorization snapshot (subject, tenant, roles, scopes) captured from the verified API principal at acceptance. Retries and approval resumes reuse that snapshot and mint a new signed MCP token with a 120-second lifetime. The snapshot does not observe external identity revocation. This is acceptable only for the isolated local fake-mode exercise; external identity/delegation remains INCOMPLETE and requires an explicit production issuer policy.

No route or MCP tool schema changed. P05 patch version 0.4.1 and its immutable wheel identify this behavior fix; 0.4.0 remains preserved with its original source/artifact provenance.

## Verification

`tests/test_service_retry_policy.py` verifies a real loopback connection refusal through the P04 worker retry transition, nested/mixed exception classification, auth permanence, and botocore transport/service errors. `scripts/check_services.py` reads the persisted job principal before and after delayed HITL resume and checks it is unchanged. Evidence is recorded in `artifacts/evidence/phase-010-*.txt`.
