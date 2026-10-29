"""Read-only verification of one existing fake/live operation and its trace."""
import json
import sqlite3
import sys
import time
from contextlib import closing
from pathlib import Path
from urllib.request import urlopen

mode=sys.argv[1]
assert mode in {"fake","live"}
root=Path(__file__).resolve().parents[3]
out=Path(__file__).resolve().parent
result=json.loads((out/(mode+"-result.json")).read_text())
assert result["status"]=="ok" and result["telemetry_flushed"] and result["accounted_calls"]==4
assert result["provider_calls"]==(4 if mode=="live" else 0)
assert result["duplicate_job_reused"] and result["mcp_read_only"]
if mode=="live":
    with closing(sqlite3.connect((root/"artifacts/evals/live/provider-usage.sqlite").resolve().as_uri()+"?mode=ro",uri=True)) as db:
        rows=db.execute("SELECT attempt_id,actual_input,actual_output FROM usage_events WHERE event='completed' AND status='ok'").fetchall()
    assert len(rows)==4 and {r[0] for r in rows}==set(result["receipts"])
    assert sum(r[1] for r in rows)==result["input_tokens"] and sum(r[2] for r in rows)==result["output_tokens"]
data=None
for attempt in range(5):
    with urlopen("http://127.0.0.1:38486/api/traces/"+result["trace_id"],timeout=5) as response:
        data=json.load(response)
    if data.get("data"):
        break
    time.sleep(.5)
spans=data["data"][0]["spans"]
names={s["operationName"] for s in spans}
assert {"api.request","queue.enqueue","queue.publish","worker.run","agent.triage","llm.inference","mcp.request","tool.lookup_invoice","database.knowledge.hybrid_search"} <= names
assert all(s["traceID"]==result["trace_id"] for s in spans)
inference=[s for s in spans if s["operationName"]=="llm.inference"]
assert len(inference)==4
assert sum(next(t["value"] for t in s["tags"] if t["key"]=="supportops.llm.input_tokens") for s in inference)==result["input_tokens"]
for span in spans:
    assert not span.get("logs")
    for tag in span["tags"]:
        assert "content" not in tag["key"] and "description" not in tag["key"]
        assert "synthetic-accounted-agent" not in str(tag["value"])
        assert not any(r in str(tag["value"]) for r in result["receipts"])
report={"status":"PASS","mode":mode,"provider_calls":result["provider_calls"],"accounted_calls":4,
        "input_tokens":result["input_tokens"],"output_tokens":result["output_tokens"],
        "http_queue_rag_mcp_correlated":True,"content_exported":False,"receipt_matches":True,
        "trace_id":result["trace_id"],"actual_billed_usd":None}
(out/(mode+"-verification.json")).write_text(json.dumps(report,indent=2)+"\n",newline="\n")
print(json.dumps(report))
