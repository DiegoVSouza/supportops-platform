"""demo-live-v1: ledger boundary, concurrency, key failover and the absence of a silent fallback.

Everything runs with a fake transport. No provider is contacted and no key is read.
"""

import json
import os
import threading

import pytest

from supportops_platform.agents import demo_live
from supportops_platform.agents.accounted import MODEL, AccountedDenied
from supportops_platform.agents.demo_live import (
    BudgetExhausted,
    KeyRing,
    MemoryLedger,
    PostgresLedger,
    ProviderBusy,
    ProviderError,
    ProviderReply,
    micro_usd,
    run_demo_triage,
)
from supportops_platform.contracts import Citation, Ticket

OUTPUTS = {
    "classifier": {"category": "billing", "summary": "refund question", "escalate": ""},
    "kb_researcher": {"context": "policy text"},
    "billing_agent": {"context": "within policy", "escalate": ""},
    "responder": {"response": "See the policy [doc-1#c-1].", "approved": True},
}
CITATION = Citation("doc-1", "Policy", "c-1", "Refunds above the limit need a second approver.", 1.0)


class Retriever:
    def search(self, tenant_id, query, top_k=3):
        return [CITATION]


def ticket():
    return Ticket(tenant_id="tenant-a", customer_id="cust-1", subject="Refund", body="I want a refund")


def reply(agent, *, input_tokens=900, output_tokens=60, model=MODEL):
    return ProviderReply(json.dumps(OUTPUTS[agent]), model, input_tokens, output_tokens,
                         {"x-ratelimit-remaining-tokens": "5000"})


class FakePost:
    """Answers by worker name. ``script`` maps a key to a list of exceptions to raise first."""

    def __init__(self, failing=None, **reply_options):
        self.calls, self.failing, self.reply_options = [], dict(failing or {}), reply_options
        self.lock = threading.Lock()

    def __call__(self, key, payload):
        worker = json.loads(payload["messages"][1]["content"])["worker"]
        with self.lock:
            self.calls.append((key, worker))
        error = self.failing.get(key)
        if error is not None:
            raise error
        return reply(worker, **self.reply_options)


def ring(post, keys=("k1", "k2", "k3", "k4")):
    return KeyRing(list(keys), post=post)


def test_four_steps_report_usage_and_settle_below_the_reservation():
    post = FakePost()
    ledger = MemoryLedger(10_000_000)
    run = run_demo_triage(ticket(), Retriever(), ledger=ledger, ring=ring(post))
    assert [s["agent"] for s in run.llm_steps] == ["classifier", "kb_researcher", "billing_agent", "responder"]
    for step in run.llm_steps:
        assert step["model"] == MODEL
        assert step["input_tokens"] == 900 and step["output_tokens"] == 60
        assert step["estimated_cost_usd"] == micro_usd(900, 60) / 1_000_000
        assert 1 <= step["key_slot"] <= 4 and step["latency_ms"] >= 0
    assert run.live_metrics["calls"] == 4
    # The ledger holds the actual cost, not the worst case.
    assert ledger.spent_micro() == 4 * micro_usd(900, 60)
    assert "k1" not in json.dumps(run.llm_steps)


def test_ledger_boundary_is_exact_and_fails_closed():
    ledger = MemoryLedger(1000)
    first = ledger.reserve("a", 1000)  # exactly the ceiling is allowed
    with pytest.raises(BudgetExhausted):
        ledger.reserve("a", 1)  # one micro-dollar over is not
    ledger.release(first)
    ledger.reserve("a", 1)
    assert ledger.spent_micro() == 1


def test_concurrent_reservations_never_cross_the_ceiling():
    ledger = MemoryLedger(10)
    granted, denied = [], []

    def worker():
        try:
            granted.append(ledger.reserve("a", 1))
        except BudgetExhausted:
            denied.append(1)

    threads = [threading.Thread(target=worker) for _ in range(64)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(granted) == 10 and len(denied) == 54
    assert ledger.spent_micro() == 10


def test_exhausted_budget_never_contacts_the_provider_and_never_fakes_an_answer():
    post = FakePost()
    ledger = MemoryLedger(100)  # below the worst case of any single call
    with pytest.raises(BudgetExhausted):
        run_demo_triage(ticket(), Retriever(), ledger=ledger, ring=ring(post))
    assert post.calls == []
    assert ledger.spent_micro() == 0


def test_budget_runs_out_mid_run_and_stops_the_workflow():
    post = FakePost()
    ledger = MemoryLedger(300)  # room to reserve one call; after it settles there is not room for the next
    with pytest.raises(AccountedDenied):
        run_demo_triage(ticket(), Retriever(), ledger=ledger, ring=ring(post))
    assert len(post.calls) < 4  # stopped, not completed with invented output


def test_429_moves_to_the_next_credential_and_bills_nothing_for_it():
    post = FakePost(failing={"k1": ProviderError(429, billed=False)})
    ledger = MemoryLedger(10_000_000)
    run = run_demo_triage(ticket(), Retriever(), ledger=ledger, ring=KeyRing(["k1", "k2"], post=post))
    assert all(step["key_slot"] == 2 for step in run.llm_steps)  # every call ended on the healthy key
    assert any(step["attempts"] == 2 for step in run.llm_steps)  # and at least one had to fail over
    assert ledger.spent_micro() == 4 * micro_usd(900, 60)


def test_all_keys_rate_limited_is_reported_plainly_and_releases_the_reservation():
    failing = {k: ProviderError(429, billed=False) for k in ("k1", "k2", "k3", "k4")}
    post = FakePost(failing=failing)
    ledger = MemoryLedger(10_000_000)
    with pytest.raises(ProviderBusy):
        run_demo_triage(ticket(), Retriever(), ledger=ledger, ring=ring(post))
    assert ledger.spent_micro() == 0


def test_a_call_that_may_have_reached_the_provider_keeps_its_reservation():
    post = FakePost(failing={k: ProviderError(None, billed=True) for k in ("k1", "k2", "k3", "k4")})
    ledger = MemoryLedger(10_000_000)
    with pytest.raises(AccountedDenied):
        run_demo_triage(ticket(), Retriever(), ledger=ledger, ring=ring(post))
    assert ledger.spent_micro() > 0  # uncertain means spent, as far as the ceiling is concerned


def test_wrong_model_in_the_receipt_is_refused_and_charged_at_the_worst_case():
    post = FakePost(model="some/other-model")
    ledger = MemoryLedger(10_000_000)
    with pytest.raises(AccountedDenied, match="invalid_accounted_receipt"):
        run_demo_triage(ticket(), Retriever(), ledger=ledger, ring=ring(post))
    assert ledger.spent_micro() > micro_usd(900, 60)


def test_citation_contract_is_enforced():
    class NoCitation(FakePost):
        def __call__(self, key, payload):
            worker = json.loads(payload["messages"][1]["content"])["worker"]
            if worker == "responder":
                return ProviderReply(json.dumps({"response": "No source here.", "approved": True}), MODEL, 10, 10, {})
            return super().__call__(key, payload)

    with pytest.raises(AccountedDenied, match="citation_contract"):
        run_demo_triage(ticket(), Retriever(), ledger=MemoryLedger(10_000_000), ring=ring(NoCitation()))


def test_key_ring_rotates_the_first_credential_between_runs():
    post = FakePost()
    keys = KeyRing(["k1", "k2", "k3", "k4"], post=post)
    for _ in range(4):
        keys.call({"messages": [{}, {"content": json.dumps({"worker": "classifier"})}]})
    assert [call[0] for call in post.calls] == ["k1", "k2", "k3", "k4"]


def test_key_ring_requires_a_credential_and_caps_at_four():
    with pytest.raises(ValueError):
        KeyRing(["", ""])
    assert KeyRing(["a", "b", "c", "d", "e"]).slots == 4


def test_live_mode_without_the_ledger_still_refuses_refunds(monkeypatch):
    from supportops_platform.agents.triage import run_configured_triage

    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.delenv("DEMO_LIVE_DSN", raising=False)
    with pytest.raises(ValueError, match="live refund/approval workflow is not enabled"):
        run_configured_triage(ticket(), Retriever())


def test_live_mode_with_the_ledger_routes_to_the_accounted_path(monkeypatch):
    from supportops_platform.agents.triage import run_configured_triage

    post = FakePost()
    ledger = MemoryLedger(10_000_000)
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("DEMO_LIVE_DSN", "postgresql://unused")
    monkeypatch.setattr(demo_live, "configured_demo", lambda: (ledger, ring(post)))
    run = run_configured_triage(ticket(), Retriever())
    assert len(run.llm_steps) == 4 and len(post.calls) == 4
    with pytest.raises(ValueError, match="resumes without a model call"):
        run_configured_triage(ticket(), Retriever(), approved=True)


def test_ceiling_above_ten_dollars_is_rejected(monkeypatch):
    monkeypatch.setattr(demo_live, "_cached", {})
    monkeypatch.setenv("DEMO_LIVE_DSN", "postgresql://unused")
    monkeypatch.setenv("DEMO_CEILING_USD", "10.01")
    with pytest.raises(ValueError, match="at most 10"):
        demo_live.configured_demo()


PG_DSN = os.environ.get("P05_TEST_PG_DSN")
needs_pg = pytest.mark.skipif(
    not PG_DSN,
    reason="needs a PostgreSQL server: set P05_TEST_PG_DSN (run against a throwaway postgres:16 container, see artifacts/evidence/demo-live-v1)",
)


@needs_pg
def test_postgres_ledger_boundary_and_concurrent_reservations():
    campaign = "test-" + os.urandom(4).hex()
    ledger = PostgresLedger(PG_DSN, 10, campaign=campaign)
    outcomes = []

    def worker():
        try:
            outcomes.append(ledger.reserve("a", 1))
        except BudgetExhausted:
            outcomes.append(None)

    threads = [threading.Thread(target=worker) for _ in range(40)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    granted = [o for o in outcomes if o]
    assert len(granted) == 10 and ledger.spent_micro() == 10
    ledger.release(granted[0])
    ledger.settle(granted[1], 0, 1, 1, 1)
    assert ledger.spent_micro() == 8
    # A restart with a larger ceiling must not raise the stored one.
    again = PostgresLedger(PG_DSN, 1_000_000, campaign=campaign)
    assert again.spent_micro() == 8
    with pytest.raises(BudgetExhausted):
        [again.reserve("a", 1) for _ in range(3)]


@needs_pg
def test_postgres_unreachable_fails_closed():
    from supportops_platform.agents.demo_live import BudgetUnavailable

    with pytest.raises(BudgetUnavailable):
        PostgresLedger("postgresql://nobody:nothing@127.0.0.1:1/none?connect_timeout=1", 10)
