from types import SimpleNamespace
import json
from supportops_platform.agents import live_groq
from supportops_platform.contracts import Citation

def test_live_client_uses_only_supplied_tenant_citations_and_tracks_usage(monkeypatch):
    seen={}
    class FakeGroq:
        def __init__(self,**kwargs): pass
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    seen.update(kwargs)
                    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"category":"shipping","summary":"Tracking guidance","escalate":""}'))],usage=SimpleNamespace(prompt_tokens=20,completion_tokens=10))
    monkeypatch.setattr(live_groq,"_new_groq",lambda **kwargs: FakeGroq(**kwargs))
    citation=Citation("shipping","Shipping","shipping:0","Use the carrier tracking link.",0.9)
    client=live_groq.GroqRAGClient(["dummy-test-key"],(citation,))
    result=client.complete("classifier",{"ticket":{"tenant_id":"tenant-a"}})
    assert result["category"]=="shipping"
    assert client.calls==1 and client.input_tokens==20 and client.output_tokens==10
    serialized=json.dumps(seen["messages"])
    assert "tenant-a" in serialized
    assert "private-b" not in serialized

def test_live_client_refuses_unknown_agent_before_network():
    client=live_groq.GroqRAGClient(["dummy-test-key"],())
    try:
        client.complete("unknown",{})
    except ValueError as exc:
        assert "unknown support agent" in str(exc)
    else:
        raise AssertionError("unknown agent was accepted")
