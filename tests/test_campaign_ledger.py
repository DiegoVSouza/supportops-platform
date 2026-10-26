from __future__ import annotations

import json
import multiprocessing
import sqlite3
import tempfile
import unittest
from contextlib import closing
from decimal import Decimal
from pathlib import Path

from scripts.campaign_ledger import CampaignBlocked, CampaignLease, CampaignLedger


class CampaignLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "ledger.sqlite"
        self.caps = {
            "requests": 2,
            "input_tokens": 100,
            "output_tokens": 100,
            "estimated_cost_usd": Decimal("0.10"),
        }
        self.ledger = CampaignLedger(self.path, campaign_id="campaign-a")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def reserve(self, case_id: str = "case-1", trial: int = 1) -> None:
        self.ledger.reserve(
            case_id=case_id,
            trial=trial,
            input_tokens=20,
            output_tokens=10,
            estimated_cost_usd=Decimal("0.02"),
            caps=self.caps,
        )

    def test_unknown_usage_reservation_is_kept_and_trial_cannot_repeat(self) -> None:
        self.reserve()
        totals = self.ledger.totals()
        self.assertEqual(totals["requests"], 1)
        self.assertEqual(totals["input_tokens"], 20)
        self.assertEqual(totals["estimated_cost_usd"], Decimal("0.02"))
        with self.assertRaisesRegex(CampaignBlocked, "already has"):
            self.reserve()

    def test_completion_reconciles_usage_but_history_is_immutable(self) -> None:
        self.reserve()
        self.ledger.complete(
            case_id="case-1",
            trial=1,
            input_tokens=12,
            output_tokens=8,
            actual_cost_usd=Decimal("0.01"),
            outcome="fail",
            error_class="classification",
        )
        self.assertEqual(self.ledger.totals()["input_tokens"], 12)
        with self.assertRaisesRegex(CampaignBlocked, "already has"):
            self.reserve()
        with closing(sqlite3.connect(self.path)) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("DELETE FROM events")

    def test_completed_attempt_without_usage_keeps_full_reservation(self) -> None:
        self.reserve()
        self.ledger.complete(
            case_id="case-1",
            trial=1,
            input_tokens=None,
            output_tokens=None,
            actual_cost_usd=None,
            outcome="error",
            error_class="transport",
        )
        totals = self.ledger.totals()
        self.assertEqual(totals["input_tokens"], 20)
        self.assertEqual(totals["output_tokens"], 10)
        self.assertEqual(totals["estimated_cost_usd"], Decimal("0.02"))

    def test_caps_are_cumulative_across_campaign_ids(self) -> None:
        self.reserve()
        other = CampaignLedger(self.path, campaign_id="campaign-b")
        with self.assertRaisesRegex(CampaignBlocked, "cap"):
            other.reserve(
                case_id="case-2",
                trial=1,
                input_tokens=20,
                output_tokens=10,
                estimated_cost_usd=Decimal("0.02"),
                caps={**self.caps, "requests": 1},
            )

    def test_parallel_reservations_cannot_race_past_cap(self) -> None:
        queue: multiprocessing.Queue[str] = multiprocessing.Queue()
        processes = [
            multiprocessing.Process(
                target=_reservation_result,
                args=(str(self.path), i, queue),
            )
            for i in range(2)
        ]
        for process in processes:
            process.start()
        for process in processes:
            process.join(10)
            self.assertEqual(process.exitcode, 0)
        results = [queue.get(timeout=2) for _ in processes]
        self.assertCountEqual(results, ["reserved", "blocked"])

    def test_lease_excludes_an_independent_process_and_releases(self) -> None:
        lease_path = self.path.with_suffix(".lock")
        with CampaignLease(lease_path, campaign_id="campaign-a"):
            queue: multiprocessing.Queue[str] = multiprocessing.Queue()
            process = multiprocessing.Process(
                target=_lease_result, args=(str(lease_path), queue)
            )
            process.start()
            process.join(10)
            self.assertEqual(process.exitcode, 0)
            self.assertEqual(queue.get(timeout=2), "blocked")
        lease_text = lease_path.read_text(encoding="utf-8")[1:]
        metadata = json.loads(lease_text)
        self.assertEqual(
            set(metadata), {"pid", "host", "campaign_id", "started_at_utc"}
        )
        self.assertNotIn("case", lease_text.lower())
        with CampaignLease(lease_path, campaign_id="campaign-b"):
            pass


def _reservation_result(
    path: str, index: int, queue: multiprocessing.Queue[str]
) -> None:
    ledger = CampaignLedger(Path(path), campaign_id="campaign-a")
    try:
        ledger.reserve(
            case_id=f"parallel-{index}",
            trial=1,
            input_tokens=20,
            output_tokens=10,
            estimated_cost_usd=Decimal("0.02"),
            caps={
                "requests": 1,
                "input_tokens": 100,
                "output_tokens": 100,
                "estimated_cost_usd": Decimal("0.10"),
            },
        )
        queue.put("reserved")
    except CampaignBlocked:
        queue.put("blocked")


def _lease_result(path: str, queue: multiprocessing.Queue[str]) -> None:
    try:
        with CampaignLease(Path(path), campaign_id="other"):
            queue.put("acquired")
    except CampaignBlocked:
        queue.put("blocked")


if __name__ == "__main__":
    unittest.main()
