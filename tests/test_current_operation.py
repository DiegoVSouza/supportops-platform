from decimal import Decimal
import pytest
from scripts.current_operation import reserve,OperationBlocked
from scripts.local_operation import reserve as original_reserve
from scripts.campaign_ledger import CampaignLedger


def test_new_live_scope_requires_exact_known_original(tmp_path):
    with pytest.raises(OperationBlocked,match="prior_success_required"):
        reserve(tmp_path/"missing.sqlite",require_original=True)
    path=tmp_path/"ledger.sqlite"
    original=original_reserve(path)
    original.complete(case_id="fixture-local-01",trial=1,input_tokens=1582,output_tokens=257,actual_cost_usd=Decimal("0.00019575"),outcome="ok",error_class=None)
    before=original.reserved_trials()
    current=reserve(path,require_original=True)
    assert current.totals()["requests"]==8
    assert original.reserved_trials()[:2]==before
    with pytest.raises(OperationBlocked,match="no_replay"):
        reserve(path,require_original=True)


def test_unknown_original_cannot_be_bypassed(tmp_path):
    path=tmp_path/"ledger.sqlite"
    original=original_reserve(path)
    original.complete(case_id="fixture-local-01",trial=1,input_tokens=None,output_tokens=None,actual_cost_usd=None,outcome="incomplete",error_class="unknown")
    with pytest.raises(OperationBlocked,match="prior_work_requires_review"):
        reserve(path,require_original=True)
    assert original.totals()["requests"]==4
