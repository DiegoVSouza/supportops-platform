# Specification

The web console (P06) is generated from `openapi.yaml`, and two gaps block it.

1. **Blind approvals.** No route lists pending approvals and the worker does not change `Ticket.status`, so an approver cannot see the refund amount before deciding. Add `GET /v1/approvals?state=pending`, tenant-scoped, requiring the `approver` role and `approval:decide`.
2. **Untyped responses.** Triage, tasks, refund, approval and feedback responses are bare `dict`, so a generated client gets `unknown`. Give them response models without changing their JSON.

Both changes are additive. Existing routes keep their payloads; optional keys that are omitted today stay omitted. ADR-009 records it and the package moves to 0.4.4.
