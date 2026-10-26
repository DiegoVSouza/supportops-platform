import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from supportops_platform.agents import live_groq
from supportops_platform.contracts import Citation


def test_live_client_uses_only_supplied_tenant_citations_and_tracks_usage(monkeypatch):
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content='{"context":"Use the carrier tracking link."}'
                )
            )
        ],
        usage=SimpleNamespace(prompt_tokens=20, completion_tokens=10),
    )
    monkeypatch.setattr(live_groq, "_new_groq", Mock(return_value=sdk_client))
    citation = Citation(
        "shipping", "Shipping", "shipping:0", "Use the carrier tracking link.", 0.9
    )
    client = live_groq.GroqRAGClient(["dummy-test-key"], (citation,))
    result = client.complete("kb_researcher", {"ticket": {"tenant_id": "tenant-a"}})
    assert result["context"] == "Use the carrier tracking link."
    assert (
        client.calls == 1 and client.input_tokens == 20 and client.output_tokens == 10
    )
    request = sdk_client.chat.completions.create.call_args.kwargs
    serialized = json.dumps(request["messages"])
    assert "tenant-a" in serialized
    assert "shipping#shipping:0" in serialized
    assert "private-b" not in serialized


def test_live_client_refuses_unknown_agent_before_network():
    client = live_groq.GroqRAGClient(["dummy-test-key"], ())
    with pytest.raises(ValueError, match="unknown support agent"):
        client.complete("unknown", {})
