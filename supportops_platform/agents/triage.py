"""P01 orchestration adapter that injects tenant-scoped P05 RAG citations."""

from dataclasses import dataclass
from typing import Any, Mapping

from supportops_agents import get_runner
from supportops_agents.contracts import Ticket as AgentTicket, TriageResult
from supportops_agents.fakes import FakeLLMClient

from supportops_platform.contracts import Citation, Ticket
from supportops_platform.rag.retrieval import LocalRetriever
from supportops_toolkit.guardrails import ExecutionLimits, guard
from supportops_obs import LLMResponse, record_llm_call
from opentelemetry import trace
from threading import Lock


@dataclass(frozen=True)
class AgentTriageRun:
    result: TriageResult
    citations: tuple[Citation, ...]
    live_metrics: dict[str, int | float] | None = None


class _RetrievalAwareFakeClient:
    def __init__(self, citations: tuple[Citation, ...], refund=False) -> None:
        self._fake = FakeLLMClient({"billing_agent":[{"context":"Refund requires distinct human approval.","refund_amount":25.0}]} if refund else None)
        self._citations = citations
        self._limits = ExecutionLimits(max_steps=12,max_tokens=4096,max_seconds=30)
        self._lock=Lock()

    def complete(self, agent: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        with self._lock: self._limits.consume(steps=1,tokens=sum(len(str(v).split()) for v in payload.values()))
        with trace.get_tracer("p05.agent").start_as_current_span("llm.fake"):
            response = self._fake.complete(agent, payload)
            with self._lock: self._limits.consume(steps=0,tokens=len(str(response).split()))
            record_llm_call(LLMResponse("fake","fixture-model",0,0,0.0,0.0))
        if agent == "kb_researcher":
            context = "\n".join(
                f"[{citation.document_id}#{citation.chunk_id}] {citation.text}"
                for citation in self._citations
            ) or "No matching tenant-scoped knowledge documents were found."
            return {**response, "context": context}
        return response


def run_fake_triage(
    ticket: Ticket, retriever: LocalRetriever, *, max_steps: int = 12,
    runner_name: str = "core", resume_key: str | None = None, approved: bool | None = None,
) -> AgentTriageRun:
    """Run P01's fake core agent with only citations authorized for the ticket tenant."""
    citations = tuple(
        citation for citation in retriever.search(ticket.tenant_id, f"{ticket.subject}\n{ticket.body}", top_k=3)
        if guard(citation.text,role="support").action != "block"
    )
    runner = get_runner(runner_name)
    if runner_name=="langgraph": runner.refund_limit=20.0
    agent_ticket = AgentTicket(
        id=ticket.id,
        subject=ticket.subject,
        description=ticket.body,
        customer_id=ticket.customer_id,
    )
    client=_RetrievalAwareFakeClient(citations,refund=runner_name=="langgraph" and "refund" in (ticket.subject+ticket.body).lower())
    if runner_name=="langgraph" and approved is not None:
        result=runner.resume(agent_ticket,llm=client,approved=approved,resume_key=resume_key)
    elif runner_name=="langgraph":
        result=runner.run(agent_ticket,llm=client,max_steps=max_steps,resume_key=resume_key)
    else: result=runner.run(agent_ticket,llm=client,max_steps=max_steps)
    return AgentTriageRun(result=result, citations=citations)


def run_live_triage(ticket: Ticket, retriever: LocalRetriever, api_keys: list[str]) -> AgentTriageRun:
    """Run the opt-in real model against only the ticket tenant's approved citations."""
    from supportops_platform.agents.live_groq import GroqRAGClient
    citations=tuple(c for c in retriever.search(ticket.tenant_id,f"{ticket.subject}\n{ticket.body}",top_k=3)
                    if guard(c.text,role="support").action!="block")
    agent_ticket=AgentTicket(id=ticket.id,subject=ticket.subject,description=ticket.body,customer_id=ticket.customer_id)
    client=GroqRAGClient(api_keys,citations)
    result=get_runner("core").run(agent_ticket,llm=client,max_steps=4)
    metrics={"calls":client.calls,"input_tokens":client.input_tokens,"output_tokens":client.output_tokens,"estimated_cost_usd":client.estimated_cost_usd}
    return AgentTriageRun(result=result,citations=citations,live_metrics=metrics)
