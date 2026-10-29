import importlib
import sys
import types
from pathlib import Path

import pytest


def test_legacy_entries_stop_before_provider_or_services(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    monkeypatch.setitem(sys.modules, "groq", types.SimpleNamespace(Groq=object))
    groq = importlib.import_module("run_live_groq_eval")
    service = importlib.import_module("check_live_services")

    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected external access")

    for module in (groq, service):
        monkeypatch.setattr(module, "load_credentials", forbidden)
    monkeypatch.setattr(service.httpx, "Client", forbidden)
    monkeypatch.setattr(groq, "run_live_triage", forbidden)
    assert groq.main() == 2
    assert service.main() == 2


def test_runtime_sdk_construction_is_denied_before_provider_access():
    from supportops_platform.agents.live_groq import _new_groq

    with pytest.raises(RuntimeError, match="accounted_guard_required"):
        _new_groq(api_key="synthetic-test-only")
