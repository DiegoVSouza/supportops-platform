from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import campaign_execution as ex
from scripts.campaign_corpus import MODEL_FAMILIES, build_case
from scripts.run_live_campaign import read_cases, read_json

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT.parents[1]
CONFIG = read_json(ROOT / "evals/live-campaign.json")
CASES = read_cases(ROOT / CONFIG["cases_path"], read_json(ROOT / CONFIG["dataset_manifest"]))
MODEL = [c for c in CASES if c["split"] == "development" and c["family"] in MODEL_FAMILIES]
BUILT = {build_case(c).ticket.id: build_case(c) for c in MODEL}


def run(out: Path, session: ex.OracleFixtureSession, max_trials: int) -> dict:
    return ex.execute_campaign(
        cases=CASES, session=session, out_dir=out, usage_reader=session.usage_for,
        max_trials=max_trials, min_gap_seconds=0, sleep=lambda _s: None,
    )


class NoCitationSession(ex.OracleFixtureSession):
    """Answers the responder step without a citation, which breaks the accounted contract."""

    def complete(self, envelope):
        result = super().complete(envelope)
        content = json.loads(result["content"])
        if "response" in content:
            content["response"] = "The value is stated in the policy."
            result["content"] = json.dumps(content)
        return result


class BrokenSession(ex.OracleFixtureSession):
    def complete(self, envelope):
        raise RuntimeError("PRIVATE-PROVIDER-DETAIL")


class ExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="p05-campaign-")
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)

    def test_every_model_case_runs_end_to_end_with_the_oracle_fixture(self) -> None:
        session = ex.OracleFixtureSession(BUILT)
        self.assertEqual(run(self.out, session, 99), {"ran": 16, "remaining": 0})
        ex.run_offline_controls(CASES, self.out)
        report = ex.build_report(CASES, self.out, provenance="fixture")
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["provenance"], "fixture")
        self.assertEqual((report["live_model"]["trials"], report["live_model"]["passed"]), (16, 16))
        self.assertEqual(report["offline_code_controls"]["cases"], 16)
        self.assertEqual(report["offline_code_controls"]["passed"], 16)
        self.assertEqual(report["offline_code_controls"]["provider_calls"], 0)
        self.assertEqual(report["not_evaluated"]["cases"], 4)
        self.assertEqual(report["live_model"]["wilson95"][1], 1.0)

    def test_pilot_runs_first_and_resume_never_repeats_a_trial(self) -> None:
        session = ex.OracleFixtureSession(BUILT)
        self.assertEqual(run(self.out, session, 6), {"ran": 6, "remaining": 10})
        rows = ex.read_jsonl(self.out / "trials.jsonl")
        self.assertEqual([row["case_id"] for row in rows], list(ex.PILOT_IDS))
        self.assertTrue(all(row["pilot"] for row in rows))
        self.assertEqual(run(self.out, session, 99), {"ran": 10, "remaining": 0})
        self.assertEqual(run(self.out, session, 99), {"ran": 0, "remaining": 0})
        ids = [row["case_id"] for row in ex.read_jsonl(self.out / "trials.jsonl")]
        self.assertEqual(len(ids), 16)
        self.assertEqual(len(set(ids)), 16)

    def test_a_contract_violation_is_a_graded_failure_and_the_campaign_continues(self) -> None:
        session = NoCitationSession(BUILT)
        self.assertEqual(run(self.out, session, 3)["ran"], 3)
        rows = ex.read_jsonl(self.out / "trials.jsonl")
        self.assertTrue(all(not row["pass"] and row["failure_category"] == "citation_contract" for row in rows))
        self.assertFalse((self.out / "stop.json").exists())

    def test_an_infrastructure_failure_stops_the_campaign_and_closes_it(self) -> None:
        with self.assertRaisesRegex(ex.ExecutionBlocked, "uncertain_or_invalid_attempt"):
            run(self.out, BrokenSession(BUILT), 2)
        stop = json.loads((self.out / "stop.json").read_text())
        self.assertEqual(stop["reason"], "uncertain_or_invalid_attempt")
        self.assertFalse(stop["replay_allowed"])
        self.assertNotIn("PRIVATE", json.dumps(stop))
        with self.assertRaisesRegex(ex.ExecutionBlocked, "campaign_stopped_requires_review"):
            run(self.out, ex.OracleFixtureSession(BUILT), 2)

    def test_an_interrupted_reservation_requires_review(self) -> None:
        ledger = ex.CampaignLedger(self.out / "ledger.sqlite", campaign_id=ex.CAMPAIGN)
        ledger.reserve(
            case_id=ex.PILOT_IDS[0], trial=1, calls=4, input_tokens=16384, output_tokens=2048,
            estimated_cost_usd=ex.TRIAL_CAPS["estimated_cost_usd"],
            caps={"requests": 64, "input_tokens": 99999999, "output_tokens": 99999999, "estimated_cost_usd": ex.Decimal("1")},
        )
        with self.assertRaisesRegex(ex.ExecutionBlocked, "uncertain_trial_requires_review"):
            run(self.out, ex.OracleFixtureSession(BUILT), 1)

    def test_records_are_content_free(self) -> None:
        run(self.out, ex.OracleFixtureSession(BUILT), 6)
        blob = "".join(path.read_text(errors="ignore") for path in self.out.glob("*.json*"))
        for case in MODEL[:6]:
            built = build_case(case)
            self.assertNotIn(built.ticket.subject, blob)
            self.assertNotIn(built.ticket.body, blob)
        self.assertNotIn("The value is", blob)

    def test_manifest_binds_the_frozen_sources(self) -> None:
        cases_path = ROOT / CONFIG["cases_path"]
        with patch.object(ex, "fingerprint", return_value="a" * 64), patch.object(ex, "git", return_value="b" * 40):
            manifest = ex.freeze(ROOT, LAB, self.out, cases_path, CASES)
            self.assertEqual(manifest["case_order"][:6], list(ex.PILOT_IDS))
            self.assertEqual(len(manifest["case_order"]), 16)
            self.assertEqual(ex.validate_manifest(ROOT, LAB, self.out, cases_path, CASES)["campaign"], ex.CAMPAIGN)
        with patch.object(ex, "fingerprint", return_value="c" * 64), patch.object(ex, "git", return_value="b" * 40):
            with self.assertRaisesRegex(ex.ExecutionBlocked, "manifest_mismatch"):
                ex.validate_manifest(ROOT, LAB, self.out, cases_path, CASES)
        (self.out / "manifest.json").unlink()
        with self.assertRaisesRegex(ex.ExecutionBlocked, "manifest_missing"):
            ex.validate_manifest(ROOT, LAB, self.out, cases_path, CASES)

    def test_pacing_waits_only_for_minute_capacity_and_never_for_a_daily_limit(self) -> None:
        sys.path.insert(0, str(LAB / "scripts/harness"))
        from live_free_account import AccountBlocked

        class Inner:
            provenance = "live"

            def __init__(self, reasons):
                self.reasons = list(reasons)

            def preview(self, envelope):
                if self.reasons:
                    raise AccountBlocked(self.reasons.pop(0))
                return "approved"

        waits: list[float] = []
        paced = ex.PacedSession(Inner(["free_token_minute_checkpoint"] * 2), sleep=waits.append, seconds=15)
        self.assertEqual(paced.preview({}), "approved")
        self.assertEqual(waits, [15, 15])
        with self.assertRaisesRegex(AccountBlocked, "free_token_day_checkpoint"):
            ex.PacedSession(Inner(["free_token_day_checkpoint"]), sleep=waits.append).preview({})
        with self.assertRaisesRegex(AccountBlocked, "free_token_minute_checkpoint"):
            ex.PacedSession(Inner(["free_token_minute_checkpoint"] * 3), sleep=waits.append, waits=2).preview({})

    def test_cli_fixture_run_and_refusals(self) -> None:
        import contextlib
        import io
        import os

        from scripts.run_live_campaign import main

        def call(*argv: str) -> tuple[int, dict]:
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = main(list(argv))
            return code, json.loads(buffer.getvalue().strip().splitlines()[-1])

        code, result = call("--stage", "development", "--execute-fixture", "--max-trials", "16", "--output-dir", str(self.out))
        self.assertEqual((code, result["status"], result["provenance"], result["trials"], result["passed"]), (0, "COMPLETE", "fixture", 16, 16))
        self.assertTrue((self.out / "report.json").exists())
        self.assertEqual(call("--stage", "development", "--execute-fixture", "--output-dir", str(self.out))[1]["reason"], "max_trials_required")
        inside = ROOT / "artifacts/evals/live/should-not-exist"
        self.assertEqual(call("--stage", "development", "--execute-fixture", "--max-trials", "1", "--output-dir", str(inside))[1]["reason"], "fixture_output_outside_repository_required")
        self.assertFalse(inside.exists())
        with patch.dict(os.environ, {"LLM_MODE": "fake"}):
            self.assertEqual(call("--stage", "development", "--execute-free", "--max-trials", "1")[1]["reason"], "explicit_live_mode_required")
        self.assertEqual(call("--stage", "pilot", "--execute-fixture", "--max-trials", "1", "--output-dir", str(self.out))[1]["reason"], "development_stage_only")
        self.assertEqual(call("--stage", "development", "--execute-free", "--execute-fixture", "--max-trials", "1")[1]["reason"], "conflicting_options")

    def test_wilson_interval_matches_the_known_p00_final_value(self) -> None:
        low, high = ex.wilson(54, 60)
        self.assertAlmostEqual(low, 0.799, delta=0.001)
        self.assertAlmostEqual(high, 0.953, delta=0.001)
        self.assertIsNone(ex.wilson(0, 0))


if __name__ == "__main__":
    unittest.main()
