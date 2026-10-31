"""HTTP API with explicit local fake credentials and tenant-bound persistence."""

import asyncio
import os
from collections import deque
from datetime import datetime
from secrets import token_urlsafe
from threading import Lock
from time import monotonic
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from opentelemetry import propagate, trace
from pydantic import BaseModel, Field

from supportops_platform import __version__
from supportops_platform.agents.triage import configured_llm_mode, run_configured_triage
from supportops_platform.async_tasks.queue import LocalTaskQueue
from supportops_platform.api.cors import ALLOWED_HEADERS, ALLOWED_METHODS, EXPOSED_HEADERS, parse_cors_origins
from supportops_platform.async_tasks.failures import failure_code
from supportops_platform.auth.jwt import decode_principal
from supportops_platform.contracts import AuthorizationLeaseExpired, Principal, Ticket
from supportops_platform.integrations.observability import (
    configure_telemetry,
    prometheus_metrics,
)
from supportops_platform.mcp.identity import IntrospectionTokenVerifier
from supportops_platform.obs.metrics import MetricsRegistry
from supportops_platform.rag.retrieval import LocalRetriever
from supportops_platform.repositories import AuthorizationError, InMemoryStore


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


class ApprovalView(BaseModel):
    id: str
    ticket_id: str
    action: str
    amount_cents: int
    state: str
    requested_by: str
    created_at: datetime


class ApprovalState(BaseModel):
    id: str
    state: str


class RefundAccepted(ApprovalState):
    action: str
    task_id: str | None = None


class FeedbackRecorded(BaseModel):
    id: str
    status: str


class TaskView(BaseModel):
    id: str
    status: str
    attempts: int
    result: dict[str, object] | None = None
    error: str | None = None


class TriageDecisionView(BaseModel):
    action: Literal["respond", "escalate"]
    category: str
    response: str
    approved: bool
    reason: str


class TriageStepView(BaseModel):
    step: int
    agent: str
    action: str
    detail: str


class CitationView(BaseModel):
    document_id: str
    title: str
    chunk_id: str
    text: str
    score: float


class TriageView(BaseModel):
    ticket_id: str
    decision: TriageDecisionView
    trace: list[TriageStepView]
    citations: list[CitationView]
    stop_reason: str
    llm_mode: str
    llm_usage: dict[str, int | float | str] | None = None


# Keycloak scopes are requested per client, not per role, so a browser token can
# carry scopes its user's role must not exercise.
ROLE_SCOPES = {
    "agent": frozenset({
        "ticket:read", "ticket:write", "task:read", "task:write", "triage:run",
        "billing:read", "crm:read", "refund:request", "feedback:write",
    }),
    "approver": frozenset({"ticket:read", "task:read", "approval:decide"}),
}
PREAUTH_LIMIT_MULTIPLIER = 10


def role_scopes(roles: frozenset[str]) -> frozenset[str]:
    return frozenset().union(*(ROLE_SCOPES.get(role, frozenset()) for role in roles))


def create_app(
    store: InMemoryStore | None = None,
    requests_per_minute: int = 60,
    token_secret: str | None = None,
    retriever: LocalRetriever | None = None,
    task_queue=None,
    rate_limiter=None,
    token_verifier=None,
    triage_handler=None,
    cors_origins: str | None = None,
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

    def allow_locally(bucket: str, limit: int) -> bool:
        now = monotonic()
        with app.state.request_times_lock:
            events = app.state.request_times.setdefault(bucket, deque())
            while events and events[0] <= now - 60:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(now)
        return True

    async def enforce_subject_limit(actor: Principal) -> None:
        bucket = f"subject:{actor.tenant_id}:{actor.subject}"
        if app.state.rate_limiter is None:
            allowed = allow_locally(bucket, app.state.rate_limit)
        else:
            try:
                allowed = await asyncio.to_thread(
                    app.state.rate_limiter.allow, bucket, app.state.rate_limit
                )
            except Exception as exc:
                raise HTTPException(
                    status_code=503, detail="rate-limit service unavailable"
                ) from exc
        if not allowed:
            raise HTTPException(status_code=429, detail="rate limit exceeded")

    async def principal(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> Principal:
        if credentials is None:
            raise HTTPException(
                status_code=401,
                detail="bearer token required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            if app.state.auth_mode == "oidc":
                accepted = await app.state.token_verifier.verify_token(
                    credentials.credentials
                )
                if accepted is None:
                    raise InvalidTokenError("external token is inactive or invalid")
                claims = accepted.claims
                roles = frozenset(claims["roles"])
                actor = Principal(
                    subject=accepted.subject,
                    tenant_id=claims["tenant_id"],
                    roles=roles,
                    scopes=frozenset(accepted.scopes) & role_scopes(roles),
                )
            else:
                return decode_principal(credentials.credentials, app.state.token_secret)
        except InvalidTokenError as exc:
            raise HTTPException(
                status_code=401,
                detail="invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        await enforce_subject_limit(actor)
        return actor

    @app.get("/healthz")
    @app.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "version": __version__,
            "llm_mode": os.getenv("LLM_MODE", "fake"),
        }

    @app.get("/readyz", include_in_schema=False)
    def ready() -> JSONResponse:
        checks = {"postgres": app.state.store, "redis": app.state.rate_limiter}
        failed = []
        for name, dependency in checks.items():
            ping = getattr(dependency, "ping", None)
            if ping is None:
                continue
            try:
                ping()
            except Exception:
                failed.append(name)
        if failed:
            return JSONResponse(status_code=503, content={"status": "unavailable", "failed": failed})
        return JSONResponse(content={"status": "ready"})

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
        return app.state.store.add_ticket(
            actor, Ticket(tenant_id=actor.tenant_id, **payload.model_dump())
        )

    @app.get("/v1/tickets/{ticket_id}")
    def get_ticket(ticket_id: str, actor: Principal = Depends(principal)) -> Ticket:
        if "ticket:read" not in actor.scopes:
            raise HTTPException(status_code=403, detail="ticket:read scope required")
        try:
            return app.state.store.get_ticket(actor, ticket_id)
        except AuthorizationError as exc:
            raise HTTPException(status_code=404, detail="ticket not found") from exc

    @app.post("/v1/tickets/{ticket_id}/triage", response_model_exclude_unset=True)
    def triage_ticket(
        ticket_id: str, actor: Principal = Depends(principal)
    ) -> TriageView:
        if "triage:run" not in actor.scopes:
            raise HTTPException(status_code=403, detail="triage:run scope required")
        try:
            ticket = app.state.store.get_ticket(actor, ticket_id)
            execution = (triage_handler(ticket, app.state.retriever, actor=actor)
                         if triage_handler is not None else run_configured_triage(ticket, app.state.retriever))
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
                {
                    "step": step.step,
                    "agent": step.agent,
                    "action": step.action,
                    "detail": step.detail,
                }
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
            "llm_mode": configured_llm_mode(),
            **(
                {"llm_usage": execution.live_metrics}
                if execution.live_metrics is not None
                else {}
            ),
        }

    @app.post("/v1/tickets/{ticket_id}/feedback", status_code=201)
    def submit_feedback(
        ticket_id: str, payload: TicketFeedback, actor: Principal = Depends(principal)
    ) -> FeedbackRecorded:
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
    ) -> FeedbackRecorded:
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
    ) -> ApprovalState:
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

    @app.post(
        "/v1/tickets/{ticket_id}/refund-approvals",
        status_code=202,
        response_model_exclude_unset=True,
    )
    def request_refund(
        ticket_id: str,
        payload: RefundRequest,
        actor: Principal = Depends(principal),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> RefundAccepted:
        try:
            approval = app.state.store.request_refund(
                actor, ticket_id, payload.amount_cents, idempotency_key or ""
            )
        except AuthorizationError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        accepted = {"id": approval.id, "state": approval.state, "action": approval.action}
        if hasattr(app.state.task_queue, "track_refund"):
            accepted["task_id"] = app.state.task_queue.track_refund(
                actor, ticket_id, approval.id, approval.idempotency_key
            )
        return accepted

    @app.get("/v1/approvals")
    def list_approvals(
        state: Literal["pending", "approved", "rejected"] = "pending",
        actor: Principal = Depends(principal),
    ) -> list[ApprovalView]:
        try:
            approvals = app.state.store.list_approvals(actor, state)
        except AuthorizationError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return [
            ApprovalView(
                id=item.id,
                ticket_id=item.ticket_id,
                action=item.action,
                amount_cents=item.amount_cents,
                state=item.state,
                requested_by=item.requested_by,
                created_at=item.created_at,
            )
            for item in approvals
        ]

    @app.post("/v1/approvals/{approval_id}/decision")
    def decide_approval(
        approval_id: str,
        payload: ApprovalDecision,
        actor: Principal = Depends(principal),
    ) -> ApprovalState:
        try:
            approval = app.state.store.decide_approval(
                actor, approval_id, payload.decision
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

    @app.post("/v1/tasks", status_code=202, response_model_exclude_unset=True)
    def enqueue_triage_task(
        payload: TaskCreate,
        actor: Principal = Depends(principal),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> TaskView:
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

    @app.get("/v1/tasks/{task_id}", response_model_exclude_unset=True)
    def get_task(
        task_id: str, actor: Principal = Depends(principal)
    ) -> TaskView:
        if "task:read" not in actor.scopes:
            raise HTTPException(status_code=403, detail="task:read scope required")
        try:
            task = app.state.task_queue.get(actor, task_id)
        except AuthorizationError as exc:
            raise HTTPException(status_code=404, detail="task not found") from exc
        result = {"id": task.id, "status": task.status.value, "attempts": task.attempts}
        if hasattr(task, "result"):
            result.update(result=task.result, error=failure_code(task.last_error))
        return result

    @app.middleware("http")
    async def request_size_limit(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
            except ValueError:
                return JSONResponse(
                    status_code=400, content={"detail": "invalid content length"}
                )
            if length < 0:
                return JSONResponse(
                    status_code=400, content={"detail": "invalid content length"}
                )
            if length > 1_000_000:
                return JSONResponse(
                    status_code=413, content={"detail": "request too large"}
                )
        bucket = request.client.host if request.client else "unknown"
        authorization = request.headers.get("authorization", "")
        limit = app.state.rate_limit
        if app.state.auth_mode == "oidc" and authorization.startswith("Bearer "):
            # Verified subjects are limited in `principal`. Here one proxy IP
            # carries many users, and this only guards introspection from floods.
            limit *= PREAUTH_LIMIT_MULTIPLIER
        if app.state.rate_limiter is not None:
            if authorization.startswith("Bearer "):
                try:
                    actor = decode_principal(authorization[7:], app.state.token_secret)
                    bucket = actor.tenant_id + ":" + actor.subject
                except InvalidTokenError:
                    pass
            try:
                allowed = await asyncio.to_thread(
                    app.state.rate_limiter.allow, bucket, limit
                )
            except Exception:
                return JSONResponse(
                    status_code=503,
                    content={"detail": "rate-limit service unavailable"},
                )
            if not allowed:
                return JSONResponse(
                    status_code=429, content={"detail": "rate limit exceeded"}
                )
        elif not allow_locally(bucket, limit):
            return JSONResponse(
                status_code=429, content={"detail": "rate limit exceeded"}
            )
        response = await call_next(request)
        app.state.metrics.record_request(request.method, response.status_code)
        return response

    @app.middleware("http")
    async def trace_request(request: Request, call_next):
        with trace.get_tracer("p05.api").start_as_current_span(
            "api.request",
            context=propagate.extract(dict(request.headers)),
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            span.set_attribute("http.request.method", request.method)
            span.set_attribute("llm.mode", "fake")
            response = await call_next(request)
            response.headers["X-Trace-ID"] = format(
                span.get_span_context().trace_id, "032x"
            )
            return response

    # Outermost on purpose: a preflight must be answered before authentication or rate limits run.
    origins = parse_cors_origins(cors_origins if cors_origins is not None else os.getenv("CORS_ALLOWED_ORIGINS"))
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=ALLOWED_METHODS,
            allow_headers=ALLOWED_HEADERS,
            expose_headers=EXPOSED_HEADERS,
            allow_credentials=False,
            max_age=600,
        )
    return app


app = create_app()
