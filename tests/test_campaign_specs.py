"""Campaign specs: the diagnostic and holdout campaigns reuse the sealed executor without loosening its rules."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts import campaign_execution as ex
from scripts.campaign_corpus import MODEL_FAMILIES, build_case
from scripts.run_live_campaign import read_cases, read_json

ROOT = Path(__file__).resolve().parents[1]
CONFIG = read_json(ROOT / "evals/live-campaign.json")
CASES = read_cases(ROOT / CONFIG["cases_path"], read_json(ROOT / CONFIG["dataset_manifest"]))


class SpecTests(unittest.TestCase):
    def tearDown(self) -> None:
        ex.use_campaign("p05-dev-v1")

    def test_the_default_campaign_is_the_sealed_development_one(self) -> None:
        self.assertEqual((ex.CAMPAIGN, ex.ACTIVE.split, ex.ACTIVE.max_requests), ("p05-dev-v1", "development", 64))
        self.assertEqual(len(ex.ordered_model_cases(CASES)), 16)

    def test_an_unknown_campaign_is_refused(self) -> None:
        with self.assertRaisesRegex(ex.ExecutionBlocked, "unknown_campaign"):
            ex.use_campaign("p05-anything-v9")

    def test_the_diagnostic_runs_two_known_development_cases_with_eight_calls(self) -> None:
        ex.use_campaign("p05-diag-v1")
        order = [c["id"] for c in ex.ordered_model_cases(CASES)]
        self.assertEqual(order, ["citation_correctness-02", "prompt_injection-01"])
        self.assertEqual((ex.CAMPAIGN, ex.ACTIVE.max_requests, ex.ACTIVE.split), ("p05-diag-v1", 8, "development"))

    def test_the_candidate_smoke_runs_the_four_worker_contract_failures_with_sixteen_calls(self) -> None:
        ex.use_campaign("p05-diag-v2")
        order = [c["id"] for c in ex.ordered_model_cases(CASES)]
        self.assertEqual(sorted(order), ["citation_correctness-02", "citation_correctness-04", "prompt_injection-01", "retrieval_relevance-02"])
        self.assertEqual((ex.ACTIVE.max_requests, ex.ACTIVE.split), (16, "development"))

    def test_the_holdout_runs_only_the_thirty_nine_model_family_holdout_cases(self) -> None:
        ex.use_campaign("p05-holdout-v1")
        ordered = ex.ordered_model_cases(CASES)
        self.assertEqual(len(ordered), 39)
        self.assertTrue(all(c["split"] == "holdout" and c["family"] in MODEL_FAMILIES for c in ordered))
        self.assertEqual(ex.ACTIVE.max_requests, 156)
        self.assertEqual([c["id"] for c in ordered[:4]], list(ex.ACTIVE.pilot_ids))

    def test_a_case_builds_only_for_the_split_the_campaign_owns(self) -> None:
        holdout = next(c for c in CASES if c["split"] == "holdout" and c["family"] in MODEL_FAMILIES)
        with self.assertRaisesRegex(ValueError, "only development cases"):
            build_case(holdout)
        self.assertEqual(build_case(holdout, split="holdout").ticket.id, build_case(holdout, split="holdout").ticket.id)
        dev = next(c for c in CASES if c["split"] == "development" and c["family"] in MODEL_FAMILIES)
        with self.assertRaisesRegex(ValueError, "only holdout cases"):
            build_case(dev, split="holdout")

    def test_a_fixture_run_of_each_campaign_completes_with_its_own_case_count(self) -> None:
        import tempfile

        for name, expected in (("p05-diag-v1", 2), ("p05-holdout-v1", 39)):
            ex.use_campaign(name)
            built = {b.ticket.id: b for b in (build_case(c, split=ex.ACTIVE.split) for c in ex.ordered_model_cases(CASES))}
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp)
                ex.execute_campaign(cases=CASES, session=ex.OracleFixtureSession(built), out_dir=out,
                                    usage_reader=ex.OracleFixtureSession(built).usage_for, max_trials=99,
                                    min_gap_seconds=0, sleep=lambda _s: None)
                report = ex.build_report(CASES, out, provenance="fixture")
            self.assertEqual(report["status"], "COMPLETE")
            self.assertEqual((report["live_model"]["cases_planned"], report["live_model"]["trials"]), (expected, expected))

    def test_each_campaign_binds_its_own_authorization_file(self) -> None:
        for name in ("p05-dev-v1", "p05-diag-v1", "p05-diag-v2", "p05-holdout-v1"):
            ex.use_campaign(name)
            self.assertIn(ex.ACTIVE.authorization, ex.root_files())
            self.assertEqual(sum("AUTHORIZATION.json" in p for p in ex.root_files()), 1)


if __name__ == "__main__":
    unittest.main()
