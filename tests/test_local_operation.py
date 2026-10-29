from decimal import Decimal

import pytest

from scripts.campaign_ledger import CampaignBlocked,CampaignLedger
from scripts.local_operation import FixtureSession,OperationBlocked,execute,reserve


def test_live_requires_explicit_mode_before_services(monkeypatch):
    monkeypatch.setenv("LLM_MODE","fake")
    with pytest.raises(OperationBlocked,match="explicit_mode"):
        execute("live")


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
