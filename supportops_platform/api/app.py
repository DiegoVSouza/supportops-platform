"""HTTP API with explicit local fake credentials and tenant-bound persistence."""

import os
from collections import deque
from threading import Lock
from time import monotonic

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from supportops_platform import __version__
from supportops_platform.contracts import Principal, Ticket
from supportops_platform.repositories import AuthorizationError, InMemoryStore


class TicketCreate(BaseModel):
    customer_id: str = Field(min_length=1, max_length=100)
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10_000)


class RefundRequest(BaseModel):
    amount_cents: int = Field(gt=0, le=5000)


class ApprovalDecision(BaseModel):
    decision: str


def _fake_principals() -> dict[str, Principal]:
    if os.getenv("LLM_MODE", "fake") != "fake":
        raise RuntimeError("only LLM_MODE=fake is implemented in this release candidate")
    return {
        "tenant-a-agent": Principal(
            subject="agent-a", tenant_id="tenant-a", roles=frozenset({"agent"}),
            scopes=frozenset({"ticket:read", "ticket:write", "refund:request"}),
        ),
        "tenant-a-approver": Principal(
            subject="approver-a", tenant_id="tenant-a", roles=frozenset({"approver"}),
            scopes=frozenset({"ticket:read", "approval:decide"}),
        ),
        "tenant-a-reader": Principal(
            subject="reader-a", tenant_id="tenant-a", roles=frozenset({"viewer"}),
            scopes=frozenset({"ticket:read"}),
        ),
        "tenant-b-agent": Principal(
            subject="agent-b", tenant_id="tenant-b", roles=frozenset({"agent"}),
            scopes=frozenset({"ticket:read", "ticket:write"}),
        ),
    }


def create_app(store: InMemoryStore | None = None, requests_per_minute: int = 60) -> FastAPI:
    if requests_per_minute < 1:
        raise ValueError("requests_per_minute must be positive")
    app = FastAPI(title="SupportOps Platform", version=__version__)
    app.state.store = store or InMemoryStore()
    app.state.tokens = _fake_principals()
    app.state.rate_limit = requests_per_minute
    app.state.request_times = {}
    app.state.request_times_lock = Lock()

    def principal(authorization: str | None = Header(default=None)) -> Principal:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="bearer token required")
        token = authorization.removeprefix("Bearer ")
        actor = app.state.tokens.get(token)
        if actor is None:
            raise HTTPException(status_code=401, detail="invalid token")
        return actor

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__, "llm_mode": os.getenv("LLM_MODE", "fake")}

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
        return {"id": approval.id, "state": approval.state}

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
        with app.state.request_times_lock:
            events = app.state.request_times.setdefault(bucket, deque())
            while events and events[0] <= now - 60:
                events.popleft()
            if len(events) >= app.state.rate_limit:
                return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"})
            events.append(now)
        return await call_next(request)

    return app


app = create_app()
