# Specification

Close the three console blockers from the lab production readiness list. ADR-010 records them.

1. **Rate limit.** OIDC tokens cannot be decoded in the middleware, so every console user shares the proxy IP bucket. Each verified subject gets its own limit after introspection. The middleware stays as a pre-authentication guard at ten times that limit per IP.
2. **Manual refund.** An approved `POST /v1/tickets/{id}/refund-approvals` executes nothing, because no job owns it. The request now creates a durable job waiting on its approval, so approval runs the effect with the requested amount and rejection ends without one. The response gains optional `task_id`.
3. **Least privilege.** The console requests every scope for every user. In OIDC mode the API now intersects token scopes with the scopes of the caller's roles.

Existing payloads, status codes and local demo tokens do not change.
