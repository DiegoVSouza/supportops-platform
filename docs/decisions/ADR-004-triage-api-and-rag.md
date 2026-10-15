# ADR-004: Tenant-scoped triage API and retrieval citations

- Status: accepted
- Date: 2026-10-15

## Context

P05 had local retrieval and a deterministic P01 runner, but the API did not invoke
them. MCP transport remains in-memory and has no authenticated transport middleware.
The API needs to bind retrieval and citations to the authenticated ticket tenant.

## Decision

Add `POST /v1/tickets/{ticket_id}/triage`, guarded by the `triage:run` scope. The
route loads the ticket through the tenant-aware repository, retrieves only that
tenant's documents, invokes the approved P01 runner in fake mode, and returns
citations with the agent trace. Bump the P05 package/OpenAPI version from 0.1.0 to
0.2.0. This route is deterministic local integration; it does not claim live model
quality or external service integration.

## Consequences

Consumers must grant `triage:run` and configure the tenant document corpus. MCP
consumers separately use server-injected principals under ADR-003. Network MCP auth,
PostgreSQL/SQS service integration, and real-model evaluation remain incomplete.
