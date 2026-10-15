"""P01 orchestration adapter used only with the deterministic fake client."""

from supportops_agents import get_runner
from supportops_agents.contracts import Ticket as AgentTicket
from supportops_agents.fakes import FakeLLMClient

from supportops_platform.contracts import Ticket


def run_fake_triage(ticket: Ticket, *, max_steps: int = 12):
    """Run P01's core supervisor with fake responses; no external model is called."""
    runner = get_runner("core")
    agent_ticket = AgentTicket(
        id=ticket.id,
        subject=ticket.subject,
        description=ticket.body,
        customer_id=ticket.customer_id,
    )
    return runner.run(agent_ticket, llm=FakeLLMClient(), max_steps=max_steps)
