"""Exclusive fake service acceptance then conditional single synthetic live workflow."""
import json
import os
import secrets
import socket
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[3]
out=Path(__file__).resolve().parent
namespace="p05-accounted-029"
records=[]
env=dict(os.environ,LLM_MODE="fake",JWT_SECRET=secrets.token_urlsafe(48),MCP_SIGNING_SECRET=secrets.token_urlsafe(48),
         P05_SOURCE_ROOT=str(root).replace("\\","/"),P05_COMPOSE_PROJECT=namespace,
         P05_COMPOSE_OVERRIDE=str(out/"override.yml"),P05_SKIP_BUILD="1",API_AUTH_MODE="local",
         P05_API_PORT="38800",P05_MCP_PORT="38801",P05_POSTGRES_PORT="38432",P05_REDIS_PORT="38379",
         P05_PROMETHEUS_PORT="38991",P05_JAEGER_PORT="38486",P05_GRAFANA_PORT="38301",P05_OTEL_PORT="38317",
         P05_DB_PASSWORD="local-test-only",P05_TEST_DSN="postgresql://supportops:local-test-only@127.0.0.1:38432/supportops",
         OTEL_EXPORTER_OTLP_ENDPOINT="",OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="",
         P05_EVIDENCE_DIRECTORY="accounted-local-services-029/full-fake",P05_EVIDENCE_PREFIX="accounted029",
         PYTEST_ADDOPTS="--basetemp artifacts/evidence/accounted-local-services-029/tmp-full1")
for key in list(env):
    if key.startswith("MCP_OIDC_"):
        env.pop(key)


def run(command,*,timeout=60,selected_env=None):
    result=subprocess.run(command,cwd=root,env=selected_env or env,capture_output=True,text=True,timeout=timeout)
    records.append({"command":command,"cwd":str(root),"exit_code":result.returncode,"output":result.stdout+result.stderr})
    (out/"commands.json").write_text(json.dumps(records,indent=2)+"\n",newline="\n")
    return result


def inventory():
    result={}
    for kind,command in {"containers":["docker","ps","-a","--no-trunc","--format","{{.ID}}|{{.Names}}|{{.Image}}"],
                         "networks":["docker","network","ls","--no-trunc","--format","{{.ID}}|{{.Name}}"],
                         "volumes":["docker","volume","ls","--format","{{.Name}}"],
                         "images":["docker","image","ls","--no-trunc","--format","{{.ID}}|{{.Repository}}:{{.Tag}}"]}.items():
        response=run(command)
        assert response.returncode==0
        result[kind]=sorted(response.stdout.splitlines())
    return result


assert run(["docker","info","--format","{{.ServerVersion}}"]).returncode==0
before=inventory()
(out/"inventory-before.json").write_text(json.dumps(before,indent=2)+"\n",newline="\n")
existing=run(["docker","ps","-a","-q","--filter","label=com.docker.compose.project="+namespace])
assert existing.returncode==0 and not existing.stdout.strip()
assert not any(namespace in row for row in before["networks"]+before["volumes"])
for port in (38800,38801,38432,38379,38991,38486,38301,38317,38080,38081):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1",port))
for image in ("supportops-platform:groq-live","pgvector/pgvector:0.8.7-pg16","redis@sha256:becdda6c7f4b3fb42e42fd7f120bbf5c54c4caaaf16f26da24e4563d2c1f0576","otel/opentelemetry-collector-contrib:0.161.0","jaegertracing/jaeger:2.18.0","prom/prometheus:v3.14.0","grafana/grafana:12.4.11"):
    assert run(["docker","image","inspect",image,"--format","{{.Id}}"]).returncode==0
compose=["docker","compose","-p",namespace,"-f","docker-compose.services.yml","-f",str(out/"override.yml")]
assert run(compose+["config","--quiet"]).returncode==0
unit=run(["uv","run","--locked","python","scripts/check_full.py","--skip-services"],timeout=300)
assert unit.returncode==2 and unit.stdout.strip().endswith("check-full: INCOMPLETE;"),"offline checks failed beyond explicit service omission"
code=2
try:
    assert run(compose+["up","--no-build","-d","--pull","never","--wait","--wait-timeout","180"],timeout=210).returncode==0
    gate=run(["uv","run","--locked","python","scripts/check_services.py","--no-start"],timeout=600)
    code=gate.returncode
    if code==0:
        # Stop only this namespace's fake worker before the separate host queue.
        assert run(compose+["stop","worker"],timeout=60).returncode==0
        fixture=run(["uv","run","--locked","python","-m","scripts.local_operation","--mode","fake"],timeout=180)
        code=fixture.returncode
        if code==0:
            code=run([sys.executable,str(out/"verify-operation.py"),"fake"],timeout=60).returncode
        if code==0:
            live_env=dict(env,LLM_MODE="live")
            live=run(["uv","run","--locked","python","-m","scripts.local_operation","--mode","live"],selected_env=live_env,timeout=240)
            code=live.returncode
            if code==0:
                code=run([sys.executable,str(out/"verify-operation.py"),"live"],timeout=60).returncode
finally:
    cleanup=run(compose+["down","--volumes","--remove-orphans"],timeout=120)
    after=inventory()
    (out/"inventory-after.json").write_text(json.dumps(after,indent=2)+"\n",newline="\n")
    remaining=run(["docker","ps","-a","-q","--filter","label=com.docker.compose.project="+namespace])
    preserved=all(set(before[k])<=set(after[k]) for k in before)
    report={"gate_exit_code":code,"cleanup_exit_code":cleanup.returncode,"prior_resources_preserved":preserved,"phase_containers_remaining":bool(remaining.stdout.strip())}
    (out/"service-result.json").write_text(json.dumps(report,indent=2)+"\n",newline="\n")
    print(json.dumps(report))
    if cleanup.returncode or not preserved or remaining.stdout.strip():
        code=1
sys.exit(code)
