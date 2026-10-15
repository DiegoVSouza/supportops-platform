"""P01 orchestration adapter that injects tenant-scoped P05 RAG citations."""

from dataclasses import dataclass
from typing import Any, Mapping

from supportops_agents import get_runner
from supportops_agents.contracts import Ticket as AgentTicket, TriageResult
from supportops_agents.fakes import FakeLLMClient

from supportops_platform.contracts import Citation, Ticket
from supportops_platform.rag.retrieval import LocalRetriever


@dataclass(frozen=True)
class AgentTriageRun:
    result: TriageResult
    citations: tuple[Citation, ...]


class _RetrievalAwareFakeClient:
    def __init__(self, citations: tuple[Citation, ...]) -> None:
        self._fake = FakeLLMClient()
        self._citations = citations

    def complete(self, agent: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        response = self._fake.complete(agent, payload)
        if agent == "kb_researcher":
            context = "\n".join(
                f"[{citation.document_id}#{citation.chunk_id}] {citation.text}"
                for citation in self._citations
            ) or "No matching tenant-scoped knowledge documents were found."
            return {**response, "context": context}
        return response


def run_fake_triage(
    ticket: Ticket, retriever: LocalRetriever, *, max_steps: int = 12
) -> AgentTriageRun:
    """Run P01's fake core agent with only citations authorized for the ticket tenant."""
    citations = tuple(
        retriever.search(ticket.tenant_id, f"{ticket.subject}\n{ticket.body}", top_k=3)
    )
    runner = get_runner("core")
    agent_ticket = AgentTicket(
        id=ticket.id,
        subject=ticket.subject,
        description=ticket.body,
        customer_id=ticket.customer_id,
    )
    result = runner.run(
        agent_ticket, llm=_RetrievalAwareFakeClient(citations), max_steps=max_steps
    )
    return AgentTriageRun(result=result, citations=citations)
