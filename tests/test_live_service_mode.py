from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from supportops_platform.agents import triage
from supportops_platform.api.app import create_app
from supportops_platform.auth.jwt import issue_demo_token
from supportops_platform.contracts import Ticket
from supportops_platform.rag.retrieval import LocalRetriever


def test_live_mode_never_uses_fake_and_requires_numbered_credentials(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "live")
    for index in range(1, 5):
        monkeypatch.delenv(f"GROQ_API_KEY_{index}", raising=False)
    fake = Mock(side_effect=AssertionError("fake fallback"))
    monkeypatch.setattr(triage, "run_fake_triage", fake)
    ticket = Ticket("tenant-a", "synthetic", "Tracking", "Where is the link?")
    with pytest.raises(ValueError, match="numbered Groq"):
        triage.run_configured_triage(ticket, LocalRetriever([]))
    monkeypatch.setenv("GROQ_API_KEY_1", "test-credential")
    live = Mock(return_value=object())
    monkeypatch.setattr(triage, "run_live_triage", live)
    assert triage.run_configured_triage(ticket, LocalRetriever([])) is live.return_value
    fake.assert_not_called()
    assert live.call_args.args[2] == ["test-credential"]


def test_unknown_mode_fails_before_provider_or_database(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "invalid")
    with pytest.raises(ValueError, match="LLM_MODE"):
        triage.run_configured_triage(
            Ticket("tenant-a", "c", "s", "b"), LocalRetriever([])
        )


def test_live_refund_workflow_is_not_enabled(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("GROQ_API_KEY_1", "test-credential")
    live = Mock(side_effect=AssertionError("refund must not reach provider"))
    monkeypatch.setattr(triage, "run_live_triage", live)
    with pytest.raises(ValueError, match="refund"):
        triage.run_configured_triage(
            Ticket("tenant-a", "c", "Refund", "Issue a refund"), LocalRetriever([])
        )
    live.assert_not_called()


def test_http_live_route_dispatches_to_live_client(monkeypatch):
    from supportops_agents.contracts import TriageDecision, TriageResult

    secret = "test-local-signing-secret-at-least-32-characters"
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("GROQ_API_KEY_1", "test-credential")
    result = triage.AgentTriageRun(
        TriageResult(TriageDecision("respond", "shipping", "Use the link.", True), []),
        (),
    )
    live = Mock(return_value=result)
    monkeypatch.setattr(triage, "run_live_triage", live)
    api = TestClient(create_app(token_secret=secret))
    token = issue_demo_token(
        "synthetic",
        "tenant-a",
        ["agent"],
        ["ticket:write", "triage:run"],
        secret=secret,
    )
    headers = {"Authorization": "Bearer " + token}
    created = api.post(
        "/v1/tickets",
        headers=headers,
        json={
            "customer_id": "synthetic",
            "subject": "Tracking",
            "body": "Where is the link?",
        },
    )
    response = api.post(f"/v1/tickets/{created.json()['id']}/triage", headers=headers)
    assert response.status_code == 200
    assert response.json()["llm_mode"] == "live"
    live.assert_called_once()
