"""P00 domain-contract adapter; tenant ownership remains P05's repository concern."""

from supportops_foundation.domain import Ticket as FoundationTicket
from supportops_foundation.testkit.fixtures import supportops_fixture

from supportops_platform.contracts import Ticket


def to_foundation_ticket(ticket: Ticket) -> FoundationTicket:
    return FoundationTicket(
        id=ticket.id,
        customer_id=ticket.customer_id,
        subject=ticket.subject,
        body=ticket.body,
        created_at=ticket.created_at,
        status=ticket.status,
    )


def seeded_foundation_fixture(seed: int = 7):
    return supportops_fixture(seed)
