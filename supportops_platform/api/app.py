"""HTTP API with explicit local fake credentials and tenant-bound persistence."""

import os
import asyncio
from opentelemetry import propagate, trace
from secrets import token_urlsafe
from collections import deque
from threading import Lock
from time import monotonic

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from jwt.exceptions import InvalidTokenError

from supportops_platform import __version__
from supportops_platform.agents.triage import run_fake_triage
from supportops_platform.auth.jwt import decode_principal
from supportops_platform.mcp.identity import IntrospectionTokenVerifier
from supportops_platform.contracts import AuthorizationLeaseExpired, Principal, Ticket
from supportops_platform.async_tasks.queue import LocalTaskQueue
from supportops_platform.obs.metrics import MetricsRegistry
from supportops_platform.integrations.observability import configure_telemetry, prometheus_metrics
from supportops_platform.repositories import AuthorizationError, InMemoryStore
from supportops_platform.rag.retrieval import LocalRetriever


class TicketCreate(BaseModel):
    customer_id: str = Field(min_length=1, max_length=100)
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10_000)


class RefundRequest(BaseModel):
    amount_cents: int = Field(gt=0, le=5000)


class ApprovalDecision(BaseModel):
    decision: str


class TicketApprovalDecision(BaseModel):
    approval_id: str | None = Field(default=None, min_length=1, max_length=100)
    decision: str = "approved"


class TaskCreate(BaseModel):
    ticket_id: str = Field(min_length=1, max_length=100)


class TicketFeedback(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=1000)


class FeedbackSubmission(TicketFeedback):
    ticket_id: str = Field(min_length=1, max_length=100)


def create_app(
    store: InMemoryStore | None = None,
    requests_per_minute: int = 60,
    token_secret: str | None = None,
    retriever: LocalRetriever | None = None,
    task_queue=None,
    rate_limiter=None,
    token_verifier=None,
) -> FastAPI:
    if requests_per_minute < 1:
        raise ValueError("requests_per_minute must be positive")
    secret = token_secret or os.getenv("JWT_SECRET")
    if secret is None and os.getenv("LLM_MODE", "fake") == "fake":
        secret = token_urlsafe(48)
    if secret is None:
        raise ValueError("JWT_SECRET is required outside fake mode")
    if len(secret) < 32:
        raise ValueError("JWT_SECRET must contain at least 32 characters")
    if store is None and os.getenv("P05_RUNTIME") == "services":
        from supportops_platform.service_runtime import create_components
        store, retriever, task_queue, rate_limiter = create_components()
    app = FastAPI(title="SupportOps Platform", version=__version__)
    configure_telemetry()
    app.state.store = store or InMemoryStore()
    app.state.retriever = retriever or LocalRetriever([])
    app.state.task_queue = task_queue or LocalTaskQueue()
    app.state.rate_limiter = rate_limiter
    app.state.metrics = MetricsRegistry()
    app.state.token_secret = secret
    auth_mode = os.getenv("API_AUTH_MODE", "local")
    if auth_mode not in {"local", "oidc"}:
        raise ValueError("API_AUTH_MODE must be local or oidc")
    if token_verifier is not None:
        auth_mode = "oidc"
    if auth_mode == "oidc" and token_verifier is None:
        names = {
            "endpoint": "API_OIDC_INTROSPECTION_URL",
            "client_id": "API_OIDC_CLIENT_ID",
            "client_secret": "API_OIDC_CLIENT_SECRET",
            "issuer": "API_OIDC_ISSUER",
            "audience": "API_OIDC_AUDIENCE",
        }
        values = {key: os.getenv(name) for key, name in names.items()}
        if not all(values.values()):
            raise ValueError("API OIDC mode requires all API_OIDC_* settings")
        token_verifier = IntrospectionTokenVerifier(**values, required_scopes=())
    app.state.auth_mode = auth_mode
    app.state.token_verifier = token_verifier
    app.state.rate_limit = requests_per_minute
    app.state.request_times = {}
    app.state.request_times_lock = Lock()
    bearer_scheme = HTTPBearer(auto_error=False)

    async def principal(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> Principal:
        if credentials is None:
            raise HTTPException(status_code=401, detail="bearer token required", headers={"WWW-Authenticate": "Bearer"})
        try:
            if app.state.auth_mode == "oidc":
                accepted = await app.state.token_verifier.verify_token(credentials.credentials)
                if accepted is None:
                    raise InvalidTokenError("external token is inactive or invalid")
                claims = accepted.claims
                return Principal(
                    subject=accepted.subject,
                    tenant_id=claims["tenant_id"],
                    roles=frozenset(claims["roles"]),
                    scopes=frozenset(accepted.scopes),
                )
            return decode_principal(credentials.credentials, app.state.token_secret)
        except InvalidTokenError as exc:
            raise HTTPException(status_code=401, detail="invalid token", headers={"WWW-Authenticate": "Bearer"}) from exc

    @app.get("/healthz")
    @app.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__, "llm_mode": os.getenv("LLM_MODE", "fake")}

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        package_metrics, _ = prometheus_metrics()
        local_metrics = app.state.metrics.render().encode("utf-8")
        return Response(
            package_metrics + local_metrics,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    @app.get("/v1/tickets")
    def list_tickets(actor: Principal = Depends(principal)) -> list[Ticket]:
        if "ticket:read" not in actor.scopes:
            raise HTTPException(status_code=403, detail="ticket:read scope required")
        return app.state.store.list_tickets(actor)

    @app.post("/v1/tickets", status_code=201)
    def create_ticket(
        payload: TicketCreate, actor: Principal = Depends(principal)
    ) -> Ticket:
        if "ticket:write" not in actor.scopes:
            raise HTTPException(status_code=403, detail="ticket:write scope required")
        return app.state.store.add_ticket(actor, Ticket(tenant_id=actor.tenant_id, **payload.model_dump()))

    @app.get("/v1/tickets/{ticket_id}")
    def get_ticket(ticket_id: str, actor: Principal = Depends(principal)) -> Ticket:
        if "ticket:read" not in actor.scopes:
            raise HTTPException(status_code=403, detail="ticket:read scope required")
        try:
            return app.state.store.get_ticket(actor, ticket_id)
        except AuthorizationError as exc:
            raise HTTPException(status_code=404, detail="ticket not found") from exc

    @app.post("/v1/tickets/{ticket_id}/triage")
    def triage_ticket(ticket_id: str, actor: Principal = Depends(principal)) -> dict[str, object]:
        if "triage:run" not in actor.scopes:
            raise HTTPException(status_code=403, detail="triage:run scope required")
        try:
            ticket = app.state.store.get_ticket(actor, ticket_id)
            execution = run_fake_triage(ticket, app.state.retriever)
        except AuthorizationError as exc:
            raise HTTPException(status_code=404, detail="ticket not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "ticket_id": ticket.id,
            "decision": {
                "action": execution.result.decision.action,
                "category": execution.result.decision.category,
                "response": execution.result.decision.response,
                "approved": execution.result.decision.approved,
                "reason": execution.result.decision.reason,
            },
            "trace": [
                {"step": step.step, "agent": step.agent, "action": step.action, "detail": step.detail}
                for step in execution.result.trace
            ],
            "citations": [
                {
                    "document_id": citation.document_id,
                    "title": citation.title,
                    "chunk_id": citation.chunk_id,
                    "text": citation.text,
                    "score": citation.score,
                }
                for citation in execution.citations
            ],
            "stop_reason": execution.result.stop_reason,
            "llm_mode": "fake",
        }

    @app.post("/v1/tickets/{ticket_id}/feedback", status_code=201)
    def submit_feedback(
        ticket_id: str, payload: TicketFeedback, actor: Principal = Depends(principal)
    ) -> dict[str, str]:
        try:
            feedback_id = app.state.store.add_feedback(
                actor, ticket_id, payload.rating, payload.comment
            )
        except AuthorizationError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"id": feedback_id, "status": "recorded"}

    @app.post("/v1/feedback", status_code=201)
    def submit_feedback_compat(
        payload: FeedbackSubmission, actor: Principal = Depends(principal)
    ) -> dict[str, str]:
        try:
            feedback_id = app.state.store.add_feedback(
                actor, payload.ticket_id, payload.rating, payload.comment
            )
        except AuthorizationError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"id": feedback_id, "status": "recorded"}

    @app.post("/v1/tickets/{ticket_id}/approve")
    def approve_ticket(
        ticket_id: str,
        payload: TicketApprovalDecision,
        actor: Principal = Depends(principal),
    ) -> dict[str, str]:
        try:
            approval = app.state.store.decide_ticket_approval(
                actor, ticket_id, payload.approval_id, payload.decision
            )
        except AuthorizationError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if hasattr(app.state.task_queue, "resume"):
            try:
                app.state.task_queue.resume(approval.id)
            except AuthorizationLeaseExpired as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"id": approval.id, "state": approval.state}

    @app.post("/v1/tickets/{ticket_id}/refund-approvals", status_code=202)
    def request_refund(
        ticket_id: str,
        payload: RefundRequest,
        actor: Principal = Depends(principal),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, object]:
        try:
            approval = app.state.store.request_refund(
                actor, ticket_id, payload.amount_cents, idempotency_key or ""
            )
        except AuthorizationError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"id": approval.id, "state": approval.state, "action": approval.action}

    @app.post("/v1/approvals/{approval_id}/decision")
    def decide_approval(
        approval_id: str,
        payload: ApprovalDecision,
        actor: Principal = Depends(principal),
    ) -> dict[str, str]:
        try:
            approval = app.state.store.decide_approval(actor, approval_id, payload.decision)
        except AuthorizationError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if hasattr(app.state.task_queue, "resume"):
            try:
                app.state.task_queue.resume(approval.id)
            except AuthorizationLeaseExpired as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"id": approval.id, "state": approval.state}

    @app.post("/v1/tasks", status_code=202)
    def enqueue_triage_task(
        payload: TaskCreate,
        actor: Principal = Depends(principal),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, object]:
        if "task:write" not in actor.scopes:
            raise HTTPException(status_code=403, detail="task:write scope required")
        try:
            app.state.store.get_ticket(actor, payload.ticket_id)
            task = app.state.task_queue.enqueue(
                actor, "triage", {"ticket_id": payload.ticket_id}, idempotency_key or ""
            )
        except AuthorizationError as exc:
            raise HTTPException(status_code=404, detail="ticket not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"id": task.id, "status": task.status.value, "attempts": task.attempts}

    @app.get("/v1/tasks/{task_id}")
    def get_task(task_id: str, actor: Principal = Depends(principal)) -> dict[str, object]:
        if "task:read" not in actor.scopes:
            raise HTTPException(status_code=403, detail="task:read scope required")
        try:
            task = app.state.task_queue.get(actor, task_id)
        except AuthorizationError as exc:
            raise HTTPException(status_code=404, detail="task not found") from exc
        result = {"id": task.id, "status": task.status.value, "attempts": task.attempts}
        if hasattr(task, "result"):
            result.update(result=task.result, error=task.last_error)
        return result

    @app.middleware("http")
    async def request_size_limit(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "invalid content length"})
            if length < 0:
                return JSONResponse(status_code=400, content={"detail": "invalid content length"})
            if length > 1_000_000:
                return JSONResponse(status_code=413, content={"detail": "request too large"})
        now = monotonic()
        bucket = request.client.host if request.client else "unknown"
        if app.state.rate_limiter is not None:
            authorization=request.headers.get("authorization", "")
            if authorization.startswith("Bearer "):
                try:
                    actor=decode_principal(authorization[7:],app.state.token_secret)
                    bucket=actor.tenant_id+":"+actor.subject
                except InvalidTokenError:
                    pass
            try:
                allowed=await asyncio.to_thread(app.state.rate_limiter.allow,bucket,app.state.rate_limit)
            except Exception:
                return JSONResponse(status_code=503,content={"detail":"rate-limit service unavailable"})
            if not allowed:
                return JSONResponse(status_code=429,content={"detail":"rate limit exceeded"})
        else:
            limited=False
            with app.state.request_times_lock:
                events = app.state.request_times.setdefault(bucket, deque())
                while events and events[0] <= now - 60:
                    events.popleft()
                limited=len(events) >= app.state.rate_limit
                if not limited: events.append(now)
            if limited:
                return JSONResponse(status_code=429,content={"detail":"rate limit exceeded"})
        response = await call_next(request)
        app.state.metrics.record_request(request.method, response.status_code)
        return response

    @app.middleware("http")
    async def trace_request(request: Request, call_next):
        with trace.get_tracer("p05.api").start_as_current_span("api.request",context=propagate.extract(dict(request.headers))) as span:
            span.set_attribute("http.request.method",request.method)
            span.set_attribute("llm.mode","fake")
            response=await call_next(request)
            response.headers["X-Trace-ID"]=format(span.get_span_context().trace_id,"032x")
            return response

    return app


app = create_app()
