"""Transactional product submission outbox feeding the installed P04 queue/worker."""

from dataclasses import dataclass
from uuid import uuid4

import boto3
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from opentelemetry import propagate, trace
from supportops_async.queue.contracts import BrokerMessage
from supportops_async.queue.memory import SqsBroker
from supportops_async.store.postgres import PostgresTaskStore

from supportops_platform.contracts import Principal, TaskStatus
from supportops_platform.repositories import AuthorizationError

TRACER = trace.get_tracer("p05.durable")


@dataclass
class DurableTask:
    id: str
    status: TaskStatus
    attempts: int
    result: dict | None
    last_error: str | None


class DurableQueue:
    def __init__(self, dsn, endpoint, queue_name="p05-tasks"):
        self.dsn = dsn
        self.backend = PostgresTaskStore(dsn)
        client = boto3.client("sqs", endpoint_url=endpoint, region_name="us-east-1",
                              aws_access_key_id="test", aws_secret_access_key="test")
        main = client.create_queue(QueueName=queue_name)["QueueUrl"]
        dead = client.create_queue(QueueName=queue_name+"-dlq")["QueueUrl"]
        self.broker = SqsBroker(client, main, dead)

    def enqueue(self, actor, task_type, payload, idempotency_key):
        if "triage:run" not in actor.scopes:
            raise AuthorizationError("triage:run scope required for durable triage")
        if task_type != "triage" or not idempotency_key or len(idempotency_key)>128:
            raise ValueError("valid triage task and idempotency key required")
        with TRACER.start_as_current_span("queue.enqueue"):
            carrier = {}
            propagate.inject(carrier)
            identity = {"subject":actor.subject,"tenant_id":actor.tenant_id,
                        "roles":sorted(actor.roles),"scopes":sorted(actor.scopes)}
            with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
                row = conn.execute("INSERT INTO platform_jobs(id,tenant_id,idempotency_key,ticket_id,principal,trace_context) "
                                   "VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(tenant_id,idempotency_key) DO NOTHING RETURNING *",
                                   (str(uuid4()),actor.tenant_id,idempotency_key,payload["ticket_id"],Jsonb(identity),Jsonb(carrier))).fetchone()
                if row is None:
                    row=conn.execute("SELECT * FROM platform_jobs WHERE tenant_id=%s AND idempotency_key=%s",
                                     (actor.tenant_id,idempotency_key)).fetchone()
                    if row["ticket_id"] != payload["ticket_id"]:
                        raise ValueError("idempotency key reused with different task")
            return self.get(actor,row["id"])

    def job(self, identifier):
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            row=conn.execute("SELECT * FROM platform_jobs WHERE id=%s",(identifier,)).fetchone()
            if row is None: raise ValueError("unknown job")
            return row

    def get(self, actor, identifier):
        try: row=self.job(identifier)
        except ValueError as exc: raise AuthorizationError("task not found") from exc
        if row["tenant_id"] != actor.tenant_id: raise AuthorizationError("task not found")
        task=self.backend.get(row["backend_task_id"]) if row["backend_task_id"] else None
        status=row["status"]
        if task and task.status.value=="running" and status=="queued": status="running"
        error=row["error"]
        if task and task.status.value == "failed" and status not in {"succeeded","needs_approval"}:
            status="failed"
            error=task.error
        return DurableTask(row["id"],TaskStatus(status),task.attempts if task else 0,row["result"],error)

    def dispatch_pending(self):
        count=0
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            rows=conn.execute("SELECT * FROM platform_jobs WHERE NOT dispatched ORDER BY created_at "
                              "FOR UPDATE SKIP LOCKED LIMIT 20").fetchall()
            for row in rows:
                with TRACER.start_as_current_span("queue.publish",context=propagate.extract(row["trace_context"])):
                    carrier={}
                    propagate.inject(carrier)
                    task,_=self.backend.create({"job_id":row["id"],"generation":row["generation"],"steps":["triage"]},
                                               f"p05:{row['id']}:{row['generation']}")
                    self.broker.publish(BrokerMessage(task.task_id))
                    conn.execute("UPDATE platform_jobs SET dispatched=true,backend_task_id=%s,trace_context=%s WHERE id=%s",
                                 (task.task_id,Jsonb(carrier),row["id"]))
                    count+=1
        return count

    def resume(self, approval_id):
        with psycopg.connect(self.dsn) as conn:
            conn.execute("UPDATE platform_jobs SET status='queued',generation=generation+1,dispatched=false "
                         "WHERE approval_id=%s AND status='needs_approval'",(approval_id,))

    def reconcile_approvals(self):
        with psycopg.connect(self.dsn) as conn:
            conn.execute("UPDATE platform_jobs j SET status='queued',generation=generation+1,dispatched=false "
                         "FROM platform_objects a WHERE j.status='needs_approval' AND a.kind='approval' "
                         "AND a.tenant_id=j.tenant_id AND a.id=j.approval_id AND a.data->>'state' IN ('approved','rejected')")

    def finish(self, identifier, status, result, approval_id=None, *, generation):
        with psycopg.connect(self.dsn) as conn:
            changed=conn.execute("UPDATE platform_jobs SET status=%s,result=%s,approval_id=%s,error=NULL WHERE id=%s AND generation=%s RETURNING tenant_id,ticket_id",
                                 (status,Jsonb(result),approval_id,identifier,generation)).fetchone()
            if changed is None: return False
            ticket_status='needs_approval' if status=='needs_approval' else 'done'
            conn.execute("UPDATE platform_objects SET data=jsonb_set(data,'{status}',%s::jsonb) WHERE tenant_id=%s AND kind='ticket' AND id=%s",
                         (Jsonb(ticket_status),changed[0],changed[1]))
            return True

    @staticmethod
    def actor(row):
        data=row["principal"]
        return Principal(data["subject"],data["tenant_id"],frozenset(data["roles"]),frozenset(data["scopes"]))
