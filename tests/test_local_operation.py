from decimal import Decimal
from urllib.error import HTTPError
import io

import pathlib
import pytest

from scripts.campaign_ledger import CampaignBlocked,CampaignLedger
from scripts.local_operation import FixtureSession,OperationBlocked,execute,reserve,poll_trace


def test_live_requires_explicit_mode_before_services(monkeypatch):
    monkeypatch.setenv("LLM_MODE","fake")
    with pytest.raises(OperationBlocked,match="explicit_mode"):
        execute("live")
    monkeypatch.setenv("LLM_MODE","live")
    with pytest.raises(OperationBlocked,match="explicit_mode"):
        execute("live",fixture_attempt=2)


def test_full_reservation_precedes_work_and_cannot_be_reopened(tmp_path):
    path=tmp_path/"ledger.sqlite"
    ledger=reserve(path)
    assert ledger.totals()["requests"]==4
    assert ledger.totals()["input_tokens"]==16384
    with pytest.raises(OperationBlocked,match="no_replay"):
        reserve(path)


@pytest.mark.parametrize("calls",[True,0,5,1.5])
def test_ledger_call_count_contract_is_bounded(tmp_path,calls):
    ledger=CampaignLedger(tmp_path/"ledger.sqlite",campaign_id="fixture")
    with pytest.raises(CampaignBlocked):
        ledger.reserve(case_id="fixture-one",trial=1,calls=calls,input_tokens=4096,output_tokens=512,
                       estimated_cost_usd=Decimal("0.0004608"),caps={"requests":8,"input_tokens":32768,
                       "output_tokens":4096,"estimated_cost_usd":Decimal("0.0036864")})


def test_controller_fixture_session_uses_exact_json_worker_protocol(tmp_path):
    from test_accounted_identity import fixtures
    from supportops_platform.agents.accounted import run
    actor,ticket,retriever,_=fixtures()
    session=FixtureSession()
    result=run(tmp_path/"operations.sqlite","fixture-preflight",actor,ticket,retriever,session,authorize=lambda a:True)
    assert result["status"]=="ok" and result["provenance"]=="fixture"
    assert session.calls==4


def test_async_trace_404_is_polled_without_resubmission():
    calls=[]
    sleeps=[]
    def opener(url,timeout):
        calls.append(url)
        if len(calls)==1:
            raise HTTPError(url,404,"pending",None,None)
        return io.BytesIO(b'{"data":[{"spans":[]}]}')
    assert poll_trace("http://127.0.0.1/trace",opener=opener,sleep=sleeps.append)["data"]
    assert len(calls)==2 and sleeps==[1]


def test_trace_polling_stops_at_five_reads_and_does_not_retry_denial():
    calls=[]
    sleeps=[]
    def missing(url,timeout):
        calls.append(1)
        raise HTTPError(url,404,"pending",None,None)
    with pytest.raises(OperationBlocked,match="trace_not_observed"):
        poll_trace("http://127.0.0.1/trace",opener=missing,sleep=sleeps.append)
    assert len(calls)==5 and sleeps==[1,2,4,8]
    def denied(url,timeout):
        raise HTTPError(url,403,"denied",None,None)
    with pytest.raises(HTTPError):
        poll_trace("http://127.0.0.1/trace",opener=denied,sleep=lambda _:pytest.fail("must not retry denial"))


@pytest.mark.skipif(
    not (pathlib.Path(__file__).resolve().parents[3] / "scripts/harness/live_free_account.py").is_file(),
    reason="lab integration test: the controller imports live_free_account from the ai-engineer-lab scripts/harness directory, which is absent outside the lab",
)
def test_controller_configures_export_before_import_time_default_app():
    import subprocess
    import sys
    code = """
import os
os.environ['LLM_MODE']='fake'
os.environ['OTEL_EXPORTER_OTLP_ENDPOINT']=''
for key in list(os.environ):
    if key.startswith('MCP_OIDC_'):
        os.environ.pop(key)
from scripts import local_operation as controller
controller.validate=lambda:None
import psycopg
def stop(*args,**kwargs):
    raise RuntimeError('before_database')
psycopg.connect=stop
try:
    controller.execute('fake')
except RuntimeError as error:
    assert str(error)=='before_database'
from supportops_obs import instrumentation as obs
processors=obs._provider._active_span_processor._span_processors
assert len(processors)==1, 'first import silently disabled export'
assert processors[0].span_exporter._endpoint=='127.0.0.1:38317'
obs.shutdown_telemetry()
"""
    result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
