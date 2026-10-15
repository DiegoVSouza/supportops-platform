# ADR-005: Restore original API routes with compatibility aliases

Status: Accepted

## Context

The archived P05 brief defines `GET /healthz`, `POST /v1/tickets/{id}/approve`, and
`POST /v1/feedback`. The implemented 0.2.0 API instead exposed `/health`, an
approval-decision resource, and ticket-scoped feedback. Existing clients may use
those routes, so replacing them would break compatibility.

## Decision

Release API/package version 0.3.0 with the three original routes as additive
compatibility endpoints. Keep `/health` operational but omit it from OpenAPI.
Keep the newer approval and ticket-scoped feedback routes. Approval is resolved
against both the authenticated tenant and ticket; top-level feedback requires an
authenticated tenant that owns the ticket. The compatibility routes do not loosen
authorization or change the approval workflow.

## Consequences

Consumers can migrate without losing the established routes. OpenAPI 0.3.0 is the
published contract for this local source release. The package integration gate must
verify the installed wheel and downstream consumer before claiming package PASS.
Durable storage and service-backed end-to-end acceptance remain separate gates.
