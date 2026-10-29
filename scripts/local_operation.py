"""Fixed synthetic local HTTP/queue/RAG/MCP operation; fake is the default."""
import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
import threading
import time
import uuid
from contextlib import nullcontext
from decimal import Decimal
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError

from scripts.campaign_ledger import CampaignLedger
from supportops_platform.agents.accounted import AccountedDenied, MODEL, run as run_accounted

PROJECT=Path(__file__).resolve().parents[1]
LAB=PROJECT.parents[1]
OUT=PROJECT/"artifacts/evidence/accounted-local-services-029"
MANIFEST="artifacts/evals/live/local-operation-v1/candidate-029-v3.json"
CASE="fixture-local-01"


class OperationBlocked(RuntimeError):
    pass


def poll_trace(url,*,opener=urlopen,sleep=time.sleep):
    """Bounded read-only polling for asynchronous export; never resubmit work."""
    for attempt in range(5):
        try:
            with opener(url,timeout=5) as response:
                data=json.load(response)
        except HTTPError as error:
            if error.code!=404:
                raise
            data={"data":[]}
        if data.get("data"):
            return data
        if attempt<4:
            sleep((1,2,4,8)[attempt])
    raise OperationBlocked("trace_not_observed")


def git(project,*args):
    result=subprocess.run(["git",*args],cwd=project,capture_output=True,timeout=15)
    if result.returncode:
        raise OperationBlocked("source_provenance")
    return result.stdout.decode().strip()


def source_paths(project):
    return sorted(p for p in git(project,"ls-files").splitlines()
                  if p.startswith(("supportops_platform/","scripts/","tests/","agent/","evals/","migrations/"))
                  or p in {"pyproject.toml","uv.lock","harness.yaml"})


def fingerprint(project=PROJECT,lab=LAB):
    paths=source_paths(project)
    git(project,"diff","--quiet","HEAD","--",*paths)
    shared=["scripts/harness/live_free_account.py","scripts/harness/live_provider_transport.py","shared/policies/groq-free-campaign.json"]
    git(lab,"diff","--quiet","HEAD","--",*shared)
    values=[("p05/"+p,hashlib.sha256((project/p).read_bytes()).hexdigest()) for p in paths]
    values += [(p,hashlib.sha256((lab/p).read_bytes()).hexdigest()) for p in shared]
    return hashlib.sha256(json.dumps(values,separators=(",",":")).encode()).hexdigest()


def validate(project=PROJECT,lab=LAB):
    try:
        manifest=json.loads((project/MANIFEST).read_text())
        owner=json.loads((project/"evals/live-execution.json").read_text())
    except (OSError,ValueError):
        raise OperationBlocked("manifest_missing") from None
    if (manifest.get("case")!=CASE or manifest.get("campaign")!="local-operation-v1"
            or manifest.get("fingerprint")!=fingerprint(project,lab) or owner.get("execution_enabled") is not True):
        raise OperationBlocked("manifest_mismatch")
    candidate=manifest.get("candidate")
    if not isinstance(candidate,str) or len(candidate)!=40:
        raise OperationBlocked("candidate_missing")
    git(project,"merge-base","--is-ancestor",candidate,"HEAD")
    git(project,"diff","--quiet",candidate,"--",*source_paths(project))


def reserve(path):
    ledger=CampaignLedger(path,campaign_id="local-operation-v1")
    if ledger.reserved_trials():
        raise OperationBlocked("prior_operation_no_replay")
    ledger.reserve(case_id=CASE,trial=1,calls=4,input_tokens=16384,output_tokens=2048,
                   estimated_cost_usd=Decimal("0.0018432"),caps={"requests":8,"input_tokens":32768,"output_tokens":4096,
                   "estimated_cost_usd":Decimal("0.0036864")})
    return ledger


class LazySession:
    provenance="live"

    def __init__(self,factory):
        self.factory,self.session=factory,None

    def preview(self,envelope):
        if self.session is None:
            self.session=self.factory()
        return self.session.preview(envelope)

    def complete(self,envelope):
        return self.session.complete(envelope)


class FixtureSession:
    provenance="fixture"

    def __init__(self):
        self.calls=0

    def preview(self,envelope):
        pass

    def complete(self,envelope):
        self.calls+=1
        payload=json.loads(envelope["payload"]["messages"][1]["content"])
        citation=payload["untrusted_citations"][0]
        outputs={"classifier":{"category":"shipping","summary":"Synthetic tracking question","escalate":""},
                 "kb_researcher":{"context":citation["text"]},
                 "billing_agent":{"context":"No billing action or lookup is needed.","escalate":""},
                 "responder":{"response":"The synthetic tracking link is in the order dashboard ["+citation["id"]+"].","approved":True}}
        return {"status":"ok","model":MODEL,"attempt_id":f"{self.calls:032x}","usage":{"input_tokens":100,"output_tokens":20},
                "content":json.dumps(outputs[payload["worker"]])}


def start_server(app,port):
    import uvicorn
    server=uvicorn.Server(uvicorn.Config(app,host="127.0.0.1",port=port,log_level="critical",access_log=False))
    thread=threading.Thread(target=server.run,daemon=True)
    thread.start()
    deadline=time.monotonic()+20
    while not server.started:
        if not thread.is_alive() or time.monotonic()>deadline:
            raise OperationBlocked("local_service_startup")
        time.sleep(.1)
    return server,thread


def execute(mode,fixture_attempt=1):
    if (mode not in {"fake","live"} or os.getenv("LLM_MODE","fake")!=mode
            or type(fixture_attempt) is not int or fixture_attempt not in (1,2,3)
            or (mode=="live" and fixture_attempt!=1)):
        raise OperationBlocked("explicit_mode_required")
    validate()
    if any(key.startswith("MCP_OIDC_") and value for key,value in os.environ.items()):
        raise OperationBlocked("external_identity_configuration_not_allowed")
    # The API module constructs its default app during import; first telemetry setup wins.
    os.environ.update(OTEL_SERVICE_NAME="p05-accounted-local",
                      OTEL_EXPORTER_OTLP_ENDPOINT="http://127.0.0.1:38317")
    import httpx
    import psycopg
    from opentelemetry import trace
    from supportops_obs import flush_telemetry
    from supportops_platform.api.app import create_app
    from supportops_platform.auth.jwt import issue_demo_token
    from supportops_platform.async_tasks.durable import DurableQueue
    from supportops_platform.persistence import PostgresStore
    from supportops_platform.rag.postgres import PostgresRetriever
    from supportops_platform.rag.retrieval import KnowledgeDocument
    from supportops_platform.service_runtime import ServiceWorker
    from supportops_platform.mcp.runtime import create_mcp_app
    from supportops_platform.integrations.observability import configure_telemetry
    sys.path.insert(0,str(LAB/"scripts/harness"))
    from live_free_account import machine_lease
    from live_provider_transport import ProviderSession
    policy=json.loads((LAB/"shared/policies/groq-free-campaign.json").read_text())
    if policy["projects"]["p05"]["requests"]!=1712:
        raise OperationBlocked("allocation_not_migrated")
    label=mode if fixture_attempt==1 else mode+"-"+str(fixture_attempt)
    database="supportops_accounted_029_"+mode+"_"+str(fixture_attempt)
    admin="postgresql://supportops:local-test-only@127.0.0.1:38432/supportops"
    with psycopg.connect(admin,autocommit=True) as conn:
        if conn.execute("SELECT 1 FROM pg_database WHERE datname=%s",(database,)).fetchone():
            raise OperationBlocked("synthetic_database_already_exists")
        conn.execute(psycopg.sql.SQL("CREATE DATABASE {}").format(psycopg.sql.Identifier(database)))
    dsn=admin.rsplit("/",1)[0]+"/"+database
    secret=secrets.token_urlsafe(48)
    os.environ.update(MCP_SIGNING_SECRET=secrets.token_urlsafe(48),MCP_ISSUER="http://127.0.0.1:38081/issuer",
                      MCP_URL="http://127.0.0.1:38081/mcp",OTEL_SERVICE_NAME="p05-accounted-local",
                      OTEL_EXPORTER_OTLP_ENDPOINT="http://127.0.0.1:38317",API_AUTH_MODE="local")
    configure_telemetry()
    store=PostgresStore(dsn)
    store.migrate()
    retriever=PostgresRetriever(dsn)
    retriever.ingest(KnowledgeDocument("accounted-tracking-029","tenant-a","Synthetic tracking policy",
                                      "The synthetic tracking link is available in the synthetic order dashboard. No refund or real account action is performed."))
    queue=DurableQueue(dsn,"redis://127.0.0.1:38379/0","p05-accounted-029-"+mode)
    base=PROJECT/"artifacts/evals/live" if mode=="live" else OUT/("fake-runtime-"+str(fixture_attempt))
    base.mkdir(parents=True,exist_ok=True)
    session=LazySession(lambda:ProviderSession(LAB,"p05",policy)) if mode=="live" else FixtureSession()
    trace_id=uuid.uuid4().hex
    context={"mode":mode,"trace_id":trace_id,"status":"preparing","provider_calls":0}
    calls=[]
    def handler(ticket,selected_retriever,*,actor,job_id=None,authorize=None):
        if job_id!=context.get("job_id") or ticket.id!=context.get("ticket_id"):
            raise AccountedDenied("fixed_job_required")
        if actor.tenant_id!="tenant-a" or not {"triage:run","billing:read","crm:read"} <= actor.scopes:
            raise AccountedDenied("authorization_denied")
        calls.append(1)
        return run_accounted(base/"operations.sqlite",CASE,actor,ticket,selected_retriever,session,
                             authorize=authorize,allow_live=mode=="live",return_execution=True)
    servers=[]
    try:
        servers.append(start_server(create_mcp_app(),38081))
        servers.append(start_server(create_app(store=store,token_secret=secret,retriever=retriever,task_queue=queue),38080))
        scopes=["ticket:read","ticket:write","task:read","task:write","triage:run","billing:read","crm:read"]
        bearer=issue_demo_token("synthetic-accounted-agent","tenant-a",["agent"],scopes,secret=secret)
        headers={"Authorization":"Bearer "+bearer,"traceparent":f"00-{trace_id}-0123456789abcdef-01"}
        lock=machine_lease(LAB/".runtime/llm-live-readiness/campaign.lock") if mode=="live" else nullcontext()
        with lock:
            ledger=reserve(base/"ledger.sqlite")
            with httpx.Client(base_url="http://127.0.0.1:38080",timeout=15) as api:
                ticket=api.post("/v1/tickets",headers=headers,json={"customer_id":"customer-a","subject":"Synthetic tracking",
                                "body":"Where is the synthetic tracking link?"})
                ticket.raise_for_status()
                context["ticket_id"]=ticket.json()["id"]
                task=api.post("/v1/tasks",headers={**headers,"Idempotency-Key":CASE},json={"ticket_id":context["ticket_id"]})
                task.raise_for_status()
                context["job_id"]=task.json()["id"]
                context["status"]="submitted"
                (OUT/(label+"-context.json")).write_text(json.dumps(context,indent=2)+"\n",newline="\n")
                queue.dispatch_pending()
                worker=ServiceWorker(store,retriever,queue,triage_handler=handler)
                if not worker.worker.run_once():
                    raise OperationBlocked("queue_delivery_missing")
                state=api.get("/v1/tasks/"+context["job_id"],headers=headers)
                state.raise_for_status()
                if state.json()["status"]!="succeeded":
                    raise OperationBlocked("worker_result_incomplete")
                replay=api.post("/v1/tasks",headers={**headers,"Idempotency-Key":CASE},json={"ticket_id":context["ticket_id"]})
                replay.raise_for_status()
                if replay.json()["id"]!=context["job_id"] or len(calls)!=1:
                    raise OperationBlocked("duplicate_operation")
            import sqlite3
            from contextlib import closing
            with closing(sqlite3.connect((base/"operations.sqlite").resolve().as_uri()+"?mode=ro",uri=True)) as db:
                rows=db.execute("SELECT receipt,input_tokens,output_tokens FROM attempts WHERE status='ok'").fetchall()
            if len(rows)!=4:
                raise OperationBlocked("receipt_count")
            inp,out=sum(r[1] for r in rows),sum(r[2] for r in rows)
            cost=(Decimal(inp)*Decimal("0.075")+Decimal(out)*Decimal("0.30"))/1000000
            ledger.complete(case_id=CASE,trial=1,input_tokens=inp,output_tokens=out,actual_cost_usd=cost,outcome="ok",error_class=None)
            flushed=flush_telemetry(timeout_millis=10000)
            result={**context,"status":"ok","provenance":mode,"provider_calls":4 if mode=="live" else 0,
                    "accounted_calls":4,"input_tokens":inp,"output_tokens":out,"receipts":[r[0] for r in rows],
                    "telemetry_flushed":flushed,"duplicate_job_reused":True,"mcp_read_only":True,"actual_billed_usd":None}
            (OUT/(label+"-result.json")).write_text(json.dumps(result,indent=2)+"\n",newline="\n")
            return result
    except Exception as error:
        allowed={"fixed_job_required","authorization_denied","authorization_expired_or_revoked","authorization_unavailable",
                 "fixture_contract","retrieval_refused","worker_order","workflow_stopped","input_bound","prior_work_requires_review",
                 "already_reserved","fixture_cap","invalid_accounted_receipt","worker_contract","citation_contract",
                 "duplicate_receipt","uncertain_or_invalid_attempt","incomplete_workflow","local_service_startup",
                 "queue_delivery_missing","worker_result_incomplete","duplicate_operation","receipt_count"}
        reason=str(error) if isinstance(error,(OperationBlocked,AccountedDenied)) and str(error) in allowed else "operation_uncertain"
        report={**context,"status":"INCOMPLETE","reason":reason,"replay_allowed":False}
        if mode=="live":
            import sqlite3
            from contextlib import closing
            provider_path=base/"provider-usage.sqlite"
            try:
                observed=[]
                if provider_path.exists():
                    with closing(sqlite3.connect(provider_path.resolve().as_uri()+"?mode=ro",uri=True)) as db:
                        observed=db.execute("SELECT attempt_id,event,status,actual_input,actual_output FROM usage_events WHERE campaign='local-operation-v1' AND case_id=? ORDER BY sequence",(CASE,)).fetchall()
                report["provider_calls"]=sum(row[1]=="reserved" for row in observed)
                report["provider_receipts"]=[{"receipt":r[0],"status":r[2],"input_tokens":r[3],"output_tokens":r[4]} for r in observed if r[1]=="completed"]
            except sqlite3.Error:
                report["provider_calls"]=None
                report["provider_accounting"]="unknown"
        (OUT/(label+"-stop.json")).write_text(json.dumps(report,indent=2)+"\n",newline="\n")
        raise OperationBlocked(reason) from None
    finally:
        for server,thread in reversed(servers):
            server.should_exit=True
            thread.join(timeout=15)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=("fake","live"),default="fake")
    parser.add_argument("--fixture-attempt",type=int,choices=(1,2,3),default=1)
    args=parser.parse_args()
    try:
        result=execute(args.mode,args.fixture_attempt)
        print(json.dumps(result))
        raise SystemExit(0 if result["telemetry_flushed"] else 2)
    except OperationBlocked as error:
        print(json.dumps({"status":"INCOMPLETE","reason":str(error)}))
        raise SystemExit(2)
    except Exception:
        print(json.dumps({"status":"INCOMPLETE","reason":"operation_uncertain"}))
        raise SystemExit(2)
