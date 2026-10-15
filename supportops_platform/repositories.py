"""In-memory tenant-aware repositories used by deterministic local development."""

from __future__ import annotations

from .contracts import Approval, Principal, Ticket


class AuthorizationError(PermissionError):
    """An authenticated principal is not authorized for the requested resource."""


class InMemoryStore:
    def __init__(self) -> None:
        self.tickets: dict[str, Ticket] = {}
        self.approvals: dict[str, Approval] = {}
        self.idempotency: dict[tuple[str, str], str] = {}

    def add_ticket(self, principal: Principal, ticket: Ticket) -> Ticket:
        if ticket.tenant_id != principal.tenant_id:
            raise AuthorizationError("ticket tenant does not match principal")
        self.tickets[ticket.id] = ticket
        return ticket

    def get_ticket(self, principal: Principal, ticket_id: str) -> Ticket:
        ticket = self.tickets.get(ticket_id)
        if ticket is None or ticket.tenant_id != principal.tenant_id:
            raise AuthorizationError("ticket not found")
        return ticket

    def list_tickets(self, principal: Principal) -> list[Ticket]:
        return sorted(
            (t for t in self.tickets.values() if t.tenant_id == principal.tenant_id),
            key=lambda t: t.created_at,
        )

    def request_refund(
        self,
        principal: Principal,
        ticket_id: str,
        amount_cents: int,
        idempotency_key: str,
    ) -> Approval:
        self.get_ticket(principal, ticket_id)
        if "refund:request" not in principal.scopes:
            raise AuthorizationError("missing refund:request scope")
        if amount_cents <= 0 or amount_cents > 5000:
            raise ValueError("refund must be between 1 and 5000 cents")
        if not idempotency_key or len(idempotency_key) > 128:
            raise ValueError("a valid idempotency key is required")
        idem = (principal.tenant_id, idempotency_key)
        prior_id = self.idempotency.get(idem)
        if prior_id:
            prior = self.approvals[prior_id]
            if prior.ticket_id != ticket_id or prior.amount_cents != amount_cents:
                raise ValueError("idempotency key reused with different request")
            return prior
        approval = Approval(
            tenant_id=principal.tenant_id,
            ticket_id=ticket_id,
            action="issue_refund",
            amount_cents=amount_cents,
            idempotency_key=idempotency_key,
        )
        self.approvals[approval.id] = approval
        self.idempotency[idem] = approval.id
        return approval

    def decide_approval(self, principal: Principal, approval_id: str, decision: str) -> Approval:
        approval = self.approvals.get(approval_id)
        if approval is None or approval.tenant_id != principal.tenant_id:
            raise AuthorizationError("approval not found")
        if "approval:decide" not in principal.scopes or "approver" not in principal.roles:
            raise AuthorizationError("approver role and approval:decide scope required")
        if decision not in {"approved", "rejected"}:
            raise ValueError("decision must be approved or rejected")
        if approval.state != "pending":
            raise ValueError("approval is already decided")
        approval.state = decision
        return approval
