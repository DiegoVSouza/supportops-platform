# ADR-003: Bind offline MCP calls to an injected principal

- Status: Accepted
- Date: 2026-10-15

## Context

The first MCP mock accepted `tenant_id` as a tool argument. A caller could choose a
tenant in model-controlled input, so the field was not an authenticated identity
boundary. The in-memory SDK transport has no configured authentication middleware.

## Decision

Remove `tenant_id` from tool inputs. `create_mock_mcp_server` now receives an optional
`authenticated_principal` from trusted application code and closes over it. Every
handler fails closed if that principal is absent, then delegates to the gateway's
scope, role, and tenant checks. Keep the server explicitly offline; do not expose this
closure-based identity binding as a network-authenticated MCP service.

The public tool schema changed incompatibly, so the MCP server contract version moves
from 0.1.0 to 0.2.0. In-memory consumers must stop sending `tenant_id` and configure a
verified principal out of band.

## Consequences

- Model-controlled arguments cannot select a tenant.
- An unauthenticated call fails closed.
- Cross-tenant invoice lookup is denied by the gateway.
- Network transport authentication remains `INCOMPLETE`.
