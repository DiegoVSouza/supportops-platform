from datetime import timedelta

from fastapi.testclient import TestClient

from supportops_platform.agents.accounted import run
from supportops_platform.api.app import create_app
from supportops_platform.auth.jwt import issue_demo_token
from test_accounted_identity import Retriever, Session

SECRET="synthetic-local-test-signing-material-32chars"


def token(tenant="fixture-a",scopes=None,lifetime=timedelta(minutes=5)):
    return {"Authorization":"Bearer "+issue_demo_token("synthetic-agent",tenant,["agent"],
            scopes if scopes is not None else ["ticket:write","triage:run"],secret=SECRET,lifetime=lifetime)}


def test_authenticated_http_routes_to_accounted_core_without_fake_live_claim(tmp_path):
    session=Session()
    def handler(ticket,retriever,*,actor):
        return run(tmp_path/"ops.sqlite","fixture-http",actor,ticket,retriever,session,
                   authorize=lambda checked: checked==actor,return_execution=True)
    api=TestClient(create_app(token_secret=SECRET,retriever=Retriever(),triage_handler=handler))
    created=api.post("/v1/tickets",headers=token(),json={"customer_id":"synthetic","subject":"Tracking","body":"Tracking status?"})
    assert created.status_code==201
    response=api.post("/v1/tickets/"+created.json()["id"]+"/triage",headers=token())
    assert response.status_code==200
    assert len(session.calls)==4
    assert response.json()["llm_mode"]=="fake"
    assert "provider" not in response.json()


def test_http_scope_tenant_and_expiry_stop_before_accounted_handler():
    calls=[]
    def handler(*args,**kwargs):
        calls.append(1)
        raise AssertionError("must not dispatch")
    api=TestClient(create_app(token_secret=SECRET,triage_handler=handler))
    ticket=api.post("/v1/tickets",headers=token(),json={"customer_id":"synthetic","subject":"Tracking","body":"status"}).json()["id"]
    url="/v1/tickets/"+ticket+"/triage"
    assert api.post(url,headers=token(tenant="fixture-b")).status_code==404
    assert api.post(url,headers=token(scopes=["ticket:write"])).status_code==403
    assert api.post(url,headers=token(lifetime=timedelta(seconds=-1))).status_code==401
    assert calls==[]
