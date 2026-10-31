# ADR-009: Extend the API contract for the web console

## Status

Accepted.

## Context

P06 is a browser console generated from `openapi.yaml`. Approvers could not list pending approvals. The worker does mark a ticket `needs_approval`, but no route exposed the amount, so a refund had to be decided without seeing it. Several responses were bare dictionaries, which give a generated client no types.

## Decision

- Add `GET /v1/approvals?state=pending|approved|rejected`. It requires the `approver` role and the `approval:decide` scope, the same rule as deciding, is tenant-scoped, and omits `idempotency_key` and `tenant_id`.
- Replace bare dictionary responses with named models. Keys that were omitted stay omitted through `response_model_exclude_unset`.
- Bump the package to 0.4.4.

## Compatibility

Additive. No existing path, status code or payload changes, so existing callers are unaffected. The source fingerprint changes, so the accepted live operations of phases 029 and 030 describe the earlier source.
