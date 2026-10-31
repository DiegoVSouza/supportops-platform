# ADR-010: Per-subject limits, role-bound scopes and owned manual refunds

## Status

Accepted.

## Context

Running behind the console exposed three problems. OIDC tokens cannot be decoded in the middleware, so all users shared one proxy IP bucket. Keycloak scopes belong to the client, so a console token carries every scope whatever the user's role. A manual refund request had no job, so approving it did nothing.

## Decision

- Limit each verified subject after introspection. Keep the IP limit before authentication at ten times the subject limit, because it now guards introspection rather than users.
- In OIDC mode, intersect token scopes with `ROLE_SCOPES`. An unknown role gets no scopes. Local demo tokens stay as issued.
- `POST /v1/tickets/{id}/refund-approvals` creates a durable job in `needs_approval` tied to the approval, and returns its `task_id`. Approval runs the effect with the requested amount inside the existing 15-minute authorization lease; after it the API answers 409 and the agent must request again.

## Compatibility

The new response field is optional, and existing fields do not change. OIDC callers whose role does not grant a scope now receive 403. Bump to 0.4.5.
