"""Sealed, resumable executor for the P05 `p05-dev-v1` development campaign.

Live attempts go through the root accounted boundary (`scripts/harness/live_provider_transport.py`);
nothing here reads a credential. Trial records are content-free: no ticket text, no response text.
Fake or fixture sessions can exercise every code path but are labelled `fixture` and never count as live.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import subprocess
import sys
import time
from contextlib import closing, nullcontext
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from scripts.campaign_corpus import (
    MODEL_FAMILIES,
    NOT_EVALUATED_FAMILIES,
    OFFLINE_FAMILIES,
    BuiltCase,
    build_case,
    build_retriever,
    family_class,
)
from scripts.campaign_ledger import CampaignBlocked, CampaignLedger
from scripts.campaign_observe import observe_model_trial, observe_offline
from scripts.run_live_campaign import grade_case
from supportops_agents import get_runner
from supportops_agents.contracts import Ticket as AgentTicket
from supportops_platform.agents.accounted import MODEL, AccountedDenied, Client
from supportops_platform.contracts import Principal
from supportops_toolkit.guardrails import guard

CAMPAIGN = "p05-dev-v1"
PILOT_IDS = (
    "retrieval_relevance-01",
    "citation_correctness-02",
    "unanswerable-03",
    "prompt_injection-04",
    "retrieval_relevance-03",
    "prompt_injection-01",
)
TRIAL_CAPS = {"requests": 4, "input_tokens": 16384, "output_tokens": 2048, "estimated_cost_usd": Decimal("0.0018432")}
CAPACITY_WAITS = {
    "free_token_minute_checkpoint",
    "free_request_minute_checkpoint",
    "provider_token_capacity_checkpoint",
    "provider_cooldown_checkpoint",
    "provider_request_capacity_checkpoint",
}
# Contract failures are graded model failures; everything else that stops a trial is infrastructure.
GRADED_DENIALS = {"worker_contract", "citation_contract"}
PRICE_IN, PRICE_OUT = Decimal("0.075"), Decimal("0.30")
SAFE_REASON = re.compile(r"[a-z_]{1,64}")


class ExecutionBlocked(RuntimeError):
    """A fixed, content-free stop reason."""


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def wilson(successes: int, total: int) -> list[float] | None:
    if total <= 0:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [round(max(0.0, centre - margin), 4), round(min(1.0, centre + margin), 4)]


def cost_of(input_tokens: int, output_tokens: int) -> Decimal:
    return (Decimal(input_tokens) * PRICE_IN + Decimal(output_tokens) * PRICE_OUT) / 1000000


# --- provenance ---------------------------------------------------------------------------------

def git(project: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=project, capture_output=True, timeout=30)
    if result.returncode:
        raise ExecutionBlocked("source_provenance")
    return result.stdout.decode().strip()


def source_paths(project: Path) -> list[str]:
    return sorted(
        path
        for path in git(project, "ls-files").splitlines()
        if path.startswith(("supportops_platform/", "scripts/", "tests/", "agent/", "evals/", "migrations/"))
        or path in {"pyproject.toml", "uv.lock", "harness.yaml"}
    )


ROOT_FILES = (
    "scripts/harness/live_free_account.py",
    "scripts/harness/live_provider_transport.py",
    "shared/policies/groq-free-campaign.json",
    ".planning/llm-live-readiness/phases/057-p05-live-campaign/AUTHORIZATION.json",
)


def fingerprint(project: Path, lab: Path) -> str:
    paths = source_paths(project)
    git(project, "diff", "--quiet", "HEAD", "--", *paths)
    git(lab, "diff", "--quiet", "HEAD", "--", *ROOT_FILES)
    values = [("p05/" + p, hashlib.sha256((project / p).read_bytes()).hexdigest()) for p in paths]
    values += [(p, hashlib.sha256((lab / p).read_bytes()).hexdigest()) for p in ROOT_FILES]
    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()


def ordered_model_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    model = [c for c in cases if c["split"] == "development" and c["family"] in MODEL_FAMILIES]
    by_id = {c["id"]: c for c in model}
    if set(PILOT_IDS) - set(by_id):
        raise ExecutionBlocked("pilot_case_missing")
    pilot = [by_id[i] for i in PILOT_IDS]
    return pilot + [c for c in model if c["id"] not in set(PILOT_IDS)]


def freeze(project: Path, lab: Path, out_dir: Path, cases_path: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = {
        "campaign": CAMPAIGN,
        "candidate": git(project, "rev-parse", "HEAD"),
        "fingerprint": fingerprint(project, lab),
        "dataset_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        "case_order": [c["id"] for c in ordered_model_cases(cases)],
        "pilot_case_ids": list(PILOT_IDS),
        "model": MODEL,
        "frozen_at": utc_now(),
        "split": "development",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


def validate_manifest(project: Path, lab: Path, out_dir: Path, cases_path: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ExecutionBlocked("manifest_missing") from None
    if (
        manifest.get("campaign") != CAMPAIGN
        or manifest.get("fingerprint") != fingerprint(project, lab)
        or manifest.get("dataset_sha256") != hashlib.sha256(cases_path.read_bytes()).hexdigest()
        or manifest.get("case_order") != [c["id"] for c in ordered_model_cases(cases)]
    ):
        raise ExecutionBlocked("manifest_mismatch")
    candidate = manifest.get("candidate")
    if not isinstance(candidate, str) or len(candidate) != 40:
        raise ExecutionBlocked("candidate_missing")
    git(project, "merge-base", "--is-ancestor", candidate, "HEAD")
    git(project, "diff", "--quiet", candidate, "--", *source_paths(project))
    return manifest


# --- sessions -----------------------------------------------------------------------------------

class PacedSession:
    """Waits out per-minute capacity checkpoints before the provider is contacted; never retries a call."""

    def __init__(self, inner: Any, *, sleep: Callable[[float], None] = time.sleep, waits: int = 10, seconds: float = 15.0):
        self.inner, self.sleep, self.waits, self.seconds = inner, sleep, waits, seconds
        self.provenance = inner.provenance
        self.diagnostic: dict[str, Any] | None = None

    def preview(self, envelope: dict[str, Any]) -> Any:
        from live_free_account import AccountBlocked  # root module, path set by the caller

        for attempt in range(self.waits + 1):
            try:
                return self.inner.preview(envelope)
            except AccountBlocked as blocked:
                if str(blocked) not in CAPACITY_WAITS or attempt == self.waits:
                    raise
                self.sleep(self.seconds)

    def complete(self, envelope: dict[str, Any]) -> Any:
        result = self.inner.complete(envelope)
        if isinstance(result, dict) and result.get("status") != "ok":
            self.diagnostic = provider_diagnostic(result)
        return result


def provider_diagnostic(result: dict[str, Any]) -> dict[str, Any] | None:
    """Keep only the transport's categorical cause of a refused call: fixed words, a status and a code, never a message."""
    reason, status, code = result.get("reason"), result.get("http_status"), result.get("provider_error_code")
    kept: dict[str, Any] = {}
    if isinstance(reason, str) and SAFE_REASON.fullmatch(reason):
        kept["reason"] = reason
    if type(status) is int and 100 <= status <= 599:
        kept["http_status"] = status
    if isinstance(code, str) and re.fullmatch(r"[a-z0-9_]{1,64}", code):
        kept["provider_error_code"] = code
    return kept or None


class LazySession:
    provenance = "live"

    def __init__(self, factory: Callable[[], Any]):
        self.factory, self.session = factory, None

    def preview(self, envelope: dict[str, Any]) -> Any:
        if self.session is None:
            self.session = self.factory()
        return self.session.preview(envelope)

    def complete(self, envelope: dict[str, Any]) -> Any:
        return self.session.complete(envelope)


class OracleFixtureSession:
    """Plumbing proof only: answers like a perfect model, makes no network call, is labelled `fixture`."""

    provenance = "fixture"

    def __init__(self, built_by_ticket: dict[str, BuiltCase]):
        self.built_by_ticket = built_by_ticket
        self.calls: dict[str, int] = {}

    def preview(self, envelope: dict[str, Any]) -> None:
        return None

    def complete(self, envelope: dict[str, Any]) -> dict[str, Any]:
        payload = json.loads(envelope["payload"]["messages"][1]["content"])
        built = self.built_by_ticket[payload["input"]["ticket"]["id"]]
        case_id = envelope["case_id"]
        self.calls[case_id] = self.calls.get(case_id, 0) + 1
        ids = [c["id"] for c in payload["untrusted_citations"]]
        target = f"{built.target_document_id}#{built.target_chunk_id}"
        cite = target if target in ids else ids[0]
        worker = payload["worker"]
        if worker == "classifier":
            out = {"category": "other", "summary": "Synthetic policy question", "escalate": ""}
        elif worker == "kb_researcher":
            out = {"context": payload["untrusted_citations"][0]["text"]}
        elif worker == "billing_agent":
            out = {"context": "No billing action is needed.", "escalate": ""}
        elif built.fact_value is not None:
            out = {"response": f"The value is {built.fact_value} {built.unit} [{cite}].", "approved": True}
        else:
            out = {"response": f"The policy does not specify this value, so I cannot confirm it [{cite}].", "approved": True}
        return {
            "status": "ok", "model": MODEL, "attempt_id": f"{sum(self.calls.values()):032x}",
            "usage": {"input_tokens": 100, "output_tokens": 20}, "content": json.dumps(out),
        }

    def usage_for(self, case_id: str) -> dict[str, int]:
        calls = self.calls.get(case_id, 0)
        return {"calls": calls, "input_tokens": 100 * calls, "output_tokens": 20 * calls}


def root_usage_reader(project: Path, campaign: str) -> Callable[[str], dict[str, int]]:
    """Exact provider-side usage of one case, read from the append-only root usage ledger."""

    path = project / "artifacts/evals/live/provider-usage.sqlite"

    def read(case_id: str) -> dict[str, int]:
        try:
            with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
                reserved = db.execute(
                    "SELECT COUNT(*) FROM usage_events WHERE campaign=? AND case_id=? AND event='reserved'",
                    (campaign, case_id),
                ).fetchone()[0]
                done = db.execute(
                    "SELECT COALESCE(SUM(actual_input),0),COALESCE(SUM(actual_output),0),COUNT(*),"
                    "COALESCE(SUM(status!='ok'),0) FROM usage_events WHERE campaign=? AND case_id=? AND event='completed'",
                    (campaign, case_id),
                ).fetchone()
        except sqlite3.Error:
            raise ExecutionBlocked("provider_usage_proof_unavailable") from None
        if done[2] != reserved or done[3]:
            raise ExecutionBlocked("uncertain_or_failed_provider_attempt")
        return {"calls": reserved, "input_tokens": int(done[0]), "output_tokens": int(done[1])}

    return read


# --- trials -------------------------------------------------------------------------------------

def run_model_trial(case: dict[str, Any], built: BuiltCase, session: Any, ops_path: Path) -> dict[str, Any]:
    context = case["synthetic_context"]
    actor = Principal(
        subject=context["principal_id"], tenant_id=context["tenant_id"],
        roles=frozenset(context["roles"]), scopes=frozenset(context["scopes"]),
    )
    valid = context["authorization_state"] == "valid"
    client = Client(ops_path, case["id"], actor, built.ticket, (), session, lambda _actor: valid, campaign=CAMPAIGN)
    client.check_identity()
    hits = tuple(build_retriever(built).search(actor.tenant_id, built.ticket.subject + "\n" + built.ticket.body, top_k=3))
    if not hits or any(guard(hit.text, role="support").action == "block" for hit in hits):
        raise ExecutionBlocked("retrieval_refused")
    client.citations = hits
    tenants = {doc.document_id: doc.tenant_id for doc in built.documents}
    supplied = [
        {"document_id": h.document_id, "chunk_id": h.chunk_id, "tenant_id": tenants[h.document_id], "text": h.text}
        for h in hits
    ]
    agent_ticket = AgentTicket(built.ticket.id, built.ticket.subject, built.ticket.body, built.ticket.customer_id)
    outcome: dict[str, Any] = {"supplied": supplied, "response": "", "approved": False, "stop_reason": "", "failure": None}
    try:
        result = get_runner("core").run(agent_ticket, llm=client, max_steps=4)
        decision = result.decision
        outcome.update(
            action="respond" if decision.action == "respond" and decision.approved else "escalate",
            approved=decision.approved, response=decision.response if decision.action == "respond" else "",
            stop_reason=result.stop_reason,
        )
    except AccountedDenied as denied:
        reason = str(denied)
        if reason not in GRADED_DENIALS:
            raise ExecutionBlocked(reason if SAFE_REASON.fullmatch(reason) else "uncertain_attempt") from None
        outcome.update(action="contract_violation", stop_reason="contract_violation", failure=reason)
    return outcome


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        stream.flush()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_offline_controls(cases: list[dict[str, Any]], out_dir: Path) -> list[dict[str, Any]]:
    path = out_dir / "offline-controls.json"
    rows = []
    for case in cases:
        if case["split"] != "development" or case["family"] not in OFFLINE_FAMILIES:
            continue
        observation = observe_offline(case)
        errors = grade_case(case, observation, provenance="live")  # the provenance gate concerns provider trials only
        rows.append({
            "case_id": case["id"], "family": case["family"], "language": case["language"], "pass": not errors,
            "errors": errors, "provider_calls": observation["provider_calls"], "kind": "offline_code_control",
        })
    out_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return rows


def execute_campaign(
    *,
    cases: list[dict[str, Any]],
    session: Any,
    out_dir: Path,
    usage_reader: Callable[[str], dict[str, int]],
    max_trials: int,
    min_gap_seconds: float = 75.0,
    sleep: Callable[[float], None] = time.sleep,
    lock: Any = None,
) -> dict[str, Any]:
    """Run up to `max_trials` unfinished model trials in order; stop on the first infrastructure problem."""
    if max_trials < 1:
        raise ExecutionBlocked("max_trials_required")
    out_dir.mkdir(parents=True, exist_ok=True)
    if (out_dir / "stop.json").exists():
        raise ExecutionBlocked("campaign_stopped_requires_review")
    provenance = session.provenance
    ledger = CampaignLedger(out_dir / "ledger.sqlite", campaign_id=CAMPAIGN)
    events = ledger.reserved_trials()
    completed = {row["case_id"] for row in events if row["event"] == "completed"}
    reserved = {row["case_id"] for row in events if row["event"] == "reserved"}
    if reserved - completed:
        raise ExecutionBlocked("uncertain_trial_requires_review")
    queue = [c for c in ordered_model_cases(cases) if c["id"] not in completed]
    caps = {"requests": 64, "input_tokens": 64 * 16384, "output_tokens": 64 * 2048, "estimated_cost_usd": Decimal("0.1179648")}
    ran = 0
    with lock if lock is not None else nullcontext():
        for case in queue[:max_trials]:
            if ran:
                sleep(min_gap_seconds)
            built = build_case(case)
            try:
                ledger.reserve(
                    case_id=case["id"], trial=1, calls=TRIAL_CAPS["requests"], input_tokens=TRIAL_CAPS["input_tokens"],
                    output_tokens=TRIAL_CAPS["output_tokens"], estimated_cost_usd=TRIAL_CAPS["estimated_cost_usd"], caps=caps,
                )
            except CampaignBlocked:
                raise ExecutionBlocked("campaign_reservation_refused") from None
            ops = out_dir / "operations" / f"{case['id']}.sqlite"
            ops.parent.mkdir(parents=True, exist_ok=True)
            try:
                outcome = run_model_trial(case, built, session, ops)
                usage = usage_reader(case["id"])
            except ExecutionBlocked as stop:
                _stop(ledger, out_dir, case, str(stop), usage_reader, getattr(session, "diagnostic", None))
                raise
            except Exception:
                _stop(ledger, out_dir, case, "uncertain_attempt", usage_reader, getattr(session, "diagnostic", None))
                raise ExecutionBlocked("uncertain_attempt") from None
            outcome["provider_calls"] = usage["calls"]
            observation = observe_model_trial(case, built, outcome)
            # The provenance gate of `grade_case` concerns the observation schema; the real provenance is recorded below.
            errors = grade_case(case, observation, provenance="live")
            cost = cost_of(usage["input_tokens"], usage["output_tokens"])
            ledger.complete(
                case_id=case["id"], trial=1, input_tokens=usage["input_tokens"], output_tokens=usage["output_tokens"],
                actual_cost_usd=cost, outcome="graded", error_class=outcome["failure"],
            )
            append_jsonl(out_dir / "trials.jsonl", {
                "campaign": CAMPAIGN, "case_id": case["id"], "family": case["family"], "language": case["language"],
                "tenant_id": case["synthetic_context"]["tenant_id"], "trial": 1, "pilot": case["id"] in PILOT_IDS,
                "provenance": provenance, "pass": not errors, "errors": errors, "failure_category": outcome["failure"],
                "action_observed": observation["action"], "abstained": observation["abstained"],
                "stop_reason": outcome["stop_reason"], "provider_calls": usage["calls"],
                "input_tokens": usage["input_tokens"], "output_tokens": usage["output_tokens"],
                "estimated_cost_usd": str(cost), "recorded_at": utc_now(),
            })
            ran += 1
    return {"ran": ran, "remaining": max(0, len(queue) - ran)}


def _stop(ledger: CampaignLedger, out_dir: Path, case: dict[str, Any], reason: str, usage_reader: Callable[[str], dict[str, int]],
          diagnostic: dict[str, Any] | None = None) -> None:
    reason = reason if SAFE_REASON.fullmatch(reason) else "uncertain_attempt"
    try:
        usage = usage_reader(case["id"])
        calls = usage["calls"]
    except ExecutionBlocked:
        calls = None
    (out_dir / "stop.json").write_text(
        json.dumps({"campaign": CAMPAIGN, "case_id": case["id"], "reason": reason, "provider_calls": calls,
                    **({"provider_diagnostic": diagnostic} if diagnostic else {}),
                    "replay_allowed": False, "stopped_at": utc_now()}, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    try:
        ledger.complete(case_id=case["id"], trial=1, input_tokens=None, output_tokens=None, actual_cost_usd=None,
                        outcome="stopped", error_class=reason)
    except CampaignBlocked:
        pass


# --- report -------------------------------------------------------------------------------------

def build_report(cases: list[dict[str, Any]], out_dir: Path, *, provenance: str) -> dict[str, Any]:
    trials = read_jsonl(out_dir / "trials.jsonl")
    offline = _read_json(out_dir / "offline-controls.json") if (out_dir / "offline-controls.json").exists() else []
    dev = [c for c in cases if c["split"] == "development"]
    expected_model = len([c for c in dev if c["family"] in MODEL_FAMILIES])
    passed = sum(t["pass"] for t in trials)

    def group(key: str) -> dict[str, Any]:
        groups: dict[str, list[dict[str, Any]]] = {}
        for t in trials:
            groups.setdefault(t[key], []).append(t)
        return {
            name: {"trials": len(rows), "passed": sum(r["pass"] for r in rows), "wilson95": wilson(sum(r["pass"] for r in rows), len(rows))}
            for name, rows in sorted(groups.items())
        }

    failures: dict[str, int] = {}
    for t in trials:
        for error in t["errors"]:
            failures[error] = failures.get(error, 0) + 1
    inp = sum(t["input_tokens"] for t in trials)
    out = sum(t["output_tokens"] for t in trials)
    complete = len(trials) == expected_model
    return {
        "campaign": CAMPAIGN,
        "dataset": "p05-live-v1",
        "split": "development",
        "provenance": provenance,
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "model": MODEL,
        "live_model": {
            "cases_planned": expected_model,
            "trials": len(trials),
            "passed": passed,
            "pass_rate": round(passed / len(trials), 4) if trials else None,
            "wilson95": wilson(passed, len(trials)),
            "by_family": group("family"),
            "by_language": group("language"),
            "failure_checks": dict(sorted(failures.items())),
            "provider_calls": sum(t["provider_calls"] for t in trials),
            "input_tokens": inp,
            "output_tokens": out,
            "estimated_cost_usd": str(cost_of(inp, out)),
            "contract_violations": sum(t["failure_category"] is not None for t in trials),
        },
        "offline_code_controls": {
            "cases": len(offline),
            "passed": sum(r["pass"] for r in offline),
            "provider_calls": sum(r["provider_calls"] for r in offline),
            "counts_as_provider_trials": False,
            "by_family": {
                family: {"cases": sum(r["family"] == family for r in offline), "passed": sum(r["family"] == family and r["pass"] for r in offline)}
                for family in OFFLINE_FAMILIES
            },
        },
        "not_evaluated": {
            "cases": sum(c["family"] in NOT_EVALUATED_FAMILIES for c in dev),
            "families": list(NOT_EVALUATED_FAMILIES),
            "reason": "needs the Redis and PostgreSQL durable queue; no number is claimed",
        },
        "limits": [
            "development split only; the 84 holdout cases were not opened",
            "corpus and grader are assistant-authored under the rubric; human review is PENDING",
            "independent review is WAIVED_BY_OWNER, which is owner approval and not independent verification",
            "one trial per case; the interval is wide and the result is not a generalisation claim",
            "numbers in an answer must occur in the supplied evidence, so a correct but unlisted number counts as unsupported",
        ],
        "human_review": "PENDING",
        "independent_review": "WAIVED_BY_OWNER",
        "raw_provider_content_persisted": False,
    }


def write_report(report: dict[str, Any], out_dir: Path) -> Path:
    path = out_dir / "report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return path


def live_session(lab: Path, project_name: str = "p05") -> Any:
    """Account-guarded session, paced around per-minute checkpoints. Needs LLM_MODE=live."""
    sys.path.insert(0, str(lab / "scripts/harness"))
    from live_provider_transport import ProviderSession

    policy = _read_json(lab / "shared/policies/groq-free-campaign.json")
    if policy["projects"]["p05"]["requests"] != 1712:
        raise ExecutionBlocked("allocation_not_migrated")
    return PacedSession(LazySession(lambda: ProviderSession(lab, project_name, policy)))
