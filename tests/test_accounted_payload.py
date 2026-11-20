"""The accounted worker request asks the provider for the exact contract and tells the responder how to abstain."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts import campaign_execution as ex
from scripts.campaign_corpus import MODEL_FAMILIES, build_case
from scripts.run_live_campaign import read_cases, read_json
from supportops_platform.agents.accounted import FIELDS

ROOT = Path(__file__).resolve().parents[1]
CONFIG = read_json(ROOT / "evals/live-campaign.json")
CASES = read_cases(ROOT / CONFIG["cases_path"], read_json(ROOT / CONFIG["dataset_manifest"]))
DEV = [c for c in CASES if c["split"] == "development" and c["family"] in MODEL_FAMILIES]
BUILT = {build_case(c).ticket.id: build_case(c) for c in DEV}


class Recording(ex.OracleFixtureSession):
    def __init__(self, built):
        super().__init__(built)
        self.payloads = []

    def complete(self, envelope):
        self.payloads.append(envelope["payload"])
        return super().complete(envelope)


class PayloadTests(unittest.TestCase):
    def test_every_worker_request_uses_a_strict_schema_of_its_exact_keys(self) -> None:
        import tempfile

        session = Recording(BUILT)
        with tempfile.TemporaryDirectory() as tmp:
            ex.execute_campaign(cases=CASES, session=session, out_dir=Path(tmp), usage_reader=session.usage_for,
                                max_trials=1, min_gap_seconds=0, sleep=lambda _s: None)
        self.assertEqual(len(session.payloads), 4)
        for payload, agent in zip(session.payloads, FIELDS):
            fmt = payload["response_format"]
            self.assertEqual(fmt["type"], "json_schema")
            schema = fmt["json_schema"]
            self.assertTrue(schema["strict"])
            self.assertEqual(schema["name"], agent)
            body = schema["schema"]
            self.assertEqual(set(body["properties"]), FIELDS[agent])
            self.assertEqual(set(body["required"]), FIELDS[agent])
            self.assertIs(body["additionalProperties"], False)
            for key, spec in body["properties"].items():
                self.assertEqual(spec["type"], "boolean" if key == "approved" else "string")
        self.assertEqual(session.payloads[0]["response_format"]["json_schema"]["schema"]["properties"]["category"]["enum"],
                         ["shipping", "billing", "technical", "account_access", "other"])

    def test_the_system_prompt_tells_the_responder_how_to_abstain(self) -> None:
        import tempfile

        session = Recording(BUILT)
        with tempfile.TemporaryDirectory() as tmp:
            ex.execute_campaign(cases=CASES, session=session, out_dir=Path(tmp), usage_reader=session.usage_for,
                                max_trials=1, min_gap_seconds=0, sleep=lambda _s: None)
        system = session.payloads[3]["messages"][0]["content"]
        self.assertIn("cannot confirm", system)
        self.assertIn("approved", system)


if __name__ == "__main__":
    unittest.main()
