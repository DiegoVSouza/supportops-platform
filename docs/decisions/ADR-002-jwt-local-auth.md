# ADR-002: Verify scoped JWTs at the API boundary

- Status: Accepted for the local platform API
- Date: 2026-10-15

## Context

The API needs a stable principal boundary before tenant filters, task access, or
refund approvals. A token label looked sufficient for an initial fake, but it could
not verify signatures, expiry, or issuer and did not exercise the documented JWT
acceptance criteria.

## Decision

Verify HS256 JWTs with PyJWT 2.15.1, a configured `JWT_SECRET` of at least 32
characters, fixed issuer `supportops-platform`, required expiry and identity claims,
and an algorithm allowlist. Extract tenant, roles, and scopes only from the verified
claims. Fake mode creates a process-local random signing key when `JWT_SECRET` is absent;
restarting invalidates local demo tokens. Outside fake mode, the configured environment
secret is required. Production key issuance and rotation remain the responsibility of an
external identity provider and are not implemented here.

## Consequences

- Invalid signature, expiry, issuer, or claim shape is rejected with HTTP 401.
- Scope and role checks remain explicit at the route and tool boundary.
- The OpenAPI document advertises HTTP bearer authentication.
- This change is before the API v1 freeze. Any later incompatible change requires a
  new ADR and API version update.
