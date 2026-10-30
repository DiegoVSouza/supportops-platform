"""PostgreSQL repositories preserve the tested domain policy under a tenant lock."""

from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from supportops_obs.instrumentation import traced_operation

from .contracts import Approval, AuthorizationLeaseExpired, Ticket
from .repositories import InMemoryStore


def document(value):
    data = asdict(value)
    data["created_at"] = value.created_at.isoformat()
    return data


class PostgresStore:
    def __init__(self, dsn):
        self.dsn = dsn

    def migrate(self):
        root = Path(__file__).resolve().parent
        if not (root / "migrations").is_dir(): root = root.parent
        with psycopg.connect(self.dsn) as conn:
            conn.execute("SELECT pg_advisory_xact_lock(991005)")
            for name in ("002_pgvector_knowledge.sql", "003_product_state.sql", "004_authorization_lease.sql"):
                conn.execute((root / "migrations" / name).read_text(encoding="utf-8"))

    def ping(self):
        with psycopg.connect(self.dsn, connect_timeout=2) as conn:
            conn.execute("SELECT 1")

    @contextmanager
    def _domain(self, actor):
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (actor.tenant_id,))
            domain = InMemoryStore()
            for row in conn.execute("SELECT kind,id,data FROM platform_objects WHERE tenant_id=%s", (actor.tenant_id,)):
                data = row["data"]
                if row["kind"] in {"ticket", "approval"}:
                    data["created_at"] = datetime.fromisoformat(data["created_at"])
                if row["kind"] == "ticket": domain.tickets[row["id"]] = Ticket(**data)
                elif row["kind"] == "approval":
                    approval = Approval(**data)
                    domain.approvals[row["id"]] = approval
                    domain.idempotency[(actor.tenant_id, approval.idempotency_key)] = approval.id
                elif row["kind"] == "feedback": domain.feedback.append(data)
            yield domain
            objects = [("ticket", item.id, document(item)) for item in domain.tickets.values()]
            objects += [("approval", item.id, document(item)) for item in domain.approvals.values()]
            objects += [("feedback", item["id"], item) for item in domain.feedback]
            for kind, identifier, data in objects:
                conn.execute("INSERT INTO platform_objects(tenant_id,kind,id,data) VALUES(%s,%s,%s,%s) "
                             "ON CONFLICT(tenant_id,kind,id) DO UPDATE SET data=EXCLUDED.data",
                             (actor.tenant_id, kind, identifier, Jsonb(data)))

    @traced_operation("database", name="ticket.add")
    def add_ticket(self, actor, ticket):
        with self._domain(actor) as domain: return domain.add_ticket(actor, ticket)

    @traced_operation("database", name="ticket.get")
    def get_ticket(self, actor, ticket_id):
        with self._domain(actor) as domain: return domain.get_ticket(actor, ticket_id)

    def list_tickets(self, actor):
        with self._domain(actor) as domain: return domain.list_tickets(actor)

    def list_approvals(self, actor, state):
        with self._domain(actor) as domain: return domain.list_approvals(actor, state)

    def request_refund(self, actor, ticket_id, amount_cents, idempotency_key):
        with self._domain(actor) as domain:
            return domain.request_refund(actor, ticket_id, amount_cents, idempotency_key)

    def decide_approval(self, actor, approval_id, decision):
        with self._domain(actor) as domain: return domain.decide_approval(actor, approval_id, decision)

    def decide_ticket_approval(self, actor, ticket_id, approval_id, decision):
        with self._domain(actor) as domain:
            return domain.decide_ticket_approval(actor, ticket_id, approval_id, decision)

    def add_feedback(self, actor, ticket_id, rating, comment):
        with self._domain(actor) as domain: return domain.add_feedback(actor, ticket_id, rating, comment)

    def set_status(self, actor, ticket_id, status):
        with self._domain(actor) as domain: domain.get_ticket(actor, ticket_id).status = status

    def approval(self, actor, approval_id):
        with self._domain(actor) as domain: return domain.approvals.get(approval_id)

    @traced_operation("database", name="refund.simulated_effect")
    def simulated_refund(self, job_id, amount_cents):
        result = {"simulated": True, "amount_cents": amount_cents, "effect_performed": True}
        with psycopg.connect(self.dsn) as conn:
            existing = conn.execute("SELECT result FROM platform_effects WHERE job_id=%s", (job_id,)).fetchone()
            if existing is not None:
                return existing[0]
            authorized = conn.execute(
                "SELECT 1 FROM platform_jobs WHERE id=%s AND authorization_expires_at > clock_timestamp() FOR UPDATE",
                (job_id,),
            ).fetchone()
            if authorized is None:
                raise AuthorizationLeaseExpired("job authorization lease expired")
            conn.execute("INSERT INTO platform_effects(job_id,result) VALUES(%s,%s) ON CONFLICT DO NOTHING",
                         (job_id, Jsonb(result)))
            return conn.execute("SELECT result FROM platform_effects WHERE job_id=%s", (job_id,)).fetchone()[0]
