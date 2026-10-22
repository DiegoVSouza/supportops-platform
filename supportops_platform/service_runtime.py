"""Configured service components and P04 worker entry point; fake LLM only."""

from dataclasses import asdict
import os
import time
import psycopg
import asyncpg
import httpx2
from botocore.exceptions import ConnectionClosedError, ConnectTimeoutError, EndpointConnectionError, ReadTimeoutError
from botocore.exceptions import ConnectionClosedError, ConnectTimeoutError, EndpointConnectionError, ReadTimeoutError

from opentelemetry import propagate, trace
from supportops_async.worker import Worker
from supportops_async.worker.runner import TransientFailure
from supportops_obs import flush_telemetry, record_agent_execution, metrics_registry
from supportops_toolkit.guardrails import guard

from .agents.triage import run_fake_triage
from .async_tasks.durable import DurableQueue
from .auth.rate_limit import RedisRateLimiter
from .mcp.runtime import call_tool
from .persistence import PostgresStore
from .rag.postgres import PostgresRetriever


def create_components():
    if os.getenv("LLM_MODE","fake") != "fake": raise ValueError("service runtime requires LLM_MODE=fake")
    dsn=os.environ["P05_POSTGRES_DSN"]
    store=PostgresStore(dsn)
    store.migrate()
    queue=DurableQueue(dsn,os.environ["P05_LOCALSTACK_ENDPOINT"],os.getenv("P05_QUEUE_NAME","p05-tasks"))
    return store,PostgresRetriever(dsn),queue,RedisRateLimiter(os.environ["P05_REDIS_URL"])


_TRANSIENT_TRANSPORT_ERRORS = (
    TimeoutError,
    ConnectionError,
    httpx2.TransportError,
    psycopg.OperationalError,
    psycopg.errors.SerializationFailure,
    psycopg.errors.DeadlockDetected,
    asyncpg.PostgresConnectionError,
    asyncpg.InterfaceError,
    EndpointConnectionError,
    ReadTimeoutError,
    ConnectTimeoutError,
    ConnectionClosedError,
)


def _is_transient_transport_error(exc):
    """Accept an exception group only when every leaf is a transient transport error."""
    if isinstance(exc, BaseExceptionGroup):
        return bool(exc.exceptions) and all(_is_transient_transport_error(item) for item in exc.exceptions)
    return isinstance(exc, _TRANSIENT_TRANSPORT_ERRORS)


_TRANSIENT_TRANSPORT_ERRORS = (
    TimeoutError,
    ConnectionError,
    httpx2.TransportError,
    psycopg.OperationalError,
    psycopg.errors.SerializationFailure,
    psycopg.errors.DeadlockDetected,
    asyncpg.PostgresConnectionError,
    asyncpg.InterfaceError,
    EndpointConnectionError,
    ReadTimeoutError,
    ConnectTimeoutError,
    ConnectionClosedError,
)


def _is_transient_transport_error(exc):
    """Accept an exception group only when every leaf is a transient transport error."""
    if isinstance(exc, BaseExceptionGroup):
        return bool(exc.exceptions) and all(_is_transient_transport_error(item) for item in exc.exceptions)
    return isinstance(exc, _TRANSIENT_TRANSPORT_ERRORS)


def _run_once_with_retry(worker, *, sleep=time.sleep):
    """Retry one worker poll after allowlisted dependency outages; surface other failures."""
    try:
        return worker.run_once()
    except Exception as exc:
        if not _is_transient_transport_error(exc):
            raise
        print("temporary worker dependency failure; retrying", flush=True)
        sleep(1)
        return False


class ServiceWorker:
    def __init__(self, store, retriever, queue):
        self.store,self.retriever,self.queue=store,retriever,queue
        self.worker=Worker(queue.backend,queue.broker,runner=self.run_job,
                           worker_id="p05-"+str(os.getpid()),heartbeat_interval_seconds=1,visibility_timeout_seconds=5)

    def run_job(self,payload,step):
        try: return self._run_job(payload,step)
        except Exception as exc:
            if not _is_transient_transport_error(exc):
                raise
            raise TransientFailure("temporary service dependency failure") from exc

    def _run_job(self,payload,step):
        job=self.queue.job(payload["job_id"])
        if payload.get("generation",0)!=job["generation"]: return {"superseded":True}
        with trace.get_tracer("p05.worker").start_as_current_span("worker.run",context=propagate.extract(job["trace_context"])):
            actor=self.queue.actor(job)
            ticket=self.store.get_ticket(actor,job["ticket_id"])
            if job["status"] in {"succeeded","needs_approval"}:
                return job["result"]
            verdict=guard(ticket.subject+"\n"+ticket.body,role="support")
            if verdict.action == "block":
                result={"response":"Request blocked by safety policy.","citations":[],"blocked":True}
                self.queue.finish(job["id"],"succeeded",result,generation=job["generation"])
                return result
            prior_approval=self.store.approval(actor,job["approval_id"]) if job["approval_id"] else None
            approved=(prior_approval.state=="approved") if prior_approval and prior_approval.state!="pending" else None
            with trace.get_tracer("p05.worker").start_as_current_span("agent.triage"):
                execution=run_fake_triage(ticket,self.retriever,runner_name="langgraph",resume_key=job["id"],approved=approved)
                record_agent_execution(steps=len(execution.result.trace),success=True,task_type="triage")
            customer=call_tool(actor,"lookup_customer",{"customer_id":ticket.customer_id})
            invoice_id="inv-a-1" if actor.tenant_id=="tenant-a" else "inv-b-1"
            invoice=call_tool(actor,"lookup_invoice",{"invoice_id":invoice_id})
            result={"response":execution.result.decision.response,
                    "citations":[asdict(c) for c in execution.citations],
                    "stop_reason":execution.result.stop_reason,"customer":customer,"invoice":invoice,
                    "llm_mode":"fake","runner":"P01 installed langgraph","trace_id":format(trace.get_current_span().get_span_context().trace_id,"032x")}
            if "refund" in (ticket.subject+" "+ticket.body).lower():
                approval=self.store.approval(actor,job["approval_id"]) if job["approval_id"] else None
                if approval is None:
                    proposal=call_tool(actor,"propose_refund",{"ticket_id":ticket.id,"amount_cents":2500})
                    approval=self.store.request_refund(actor,ticket.id,proposal["amount_cents"],"job:"+job["id"])
                result["approval_id"]=approval.id
                result["approval_state"]=approval.state
                if approval.state=="pending":
                    self.queue.finish(job["id"],"needs_approval",result,approval.id,generation=job["generation"])
                    return result
                if approval.state=="approved": result["refund"]=self.store.simulated_refund(job["id"],approval.amount_cents)
            self.queue.finish(job["id"],"succeeded",result,generation=job["generation"])
            return result

    def run_once(self):
        self.queue.reconcile_approvals()
        self.queue.dispatch_pending()
        return self.worker.run_once()


def main():
    from .integrations.observability import configure_telemetry
    configure_telemetry()
    if os.getenv("P05_METRICS_PORT"):
        from prometheus_client import start_http_server
        start_http_server(int(os.environ["P05_METRICS_PORT"]),addr="0.0.0.0",registry=metrics_registry())
    store,retriever,queue,_=create_components()
    worker=ServiceWorker(store,retriever,queue)
    try:
        while True:
            _run_once_with_retry(worker)
            flush_telemetry()
            time.sleep(.1)
    finally: flush_telemetry()


if __name__=="__main__": main()
