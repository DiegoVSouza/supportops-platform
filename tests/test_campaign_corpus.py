from __future__ import annotations

import unittest
from pathlib import Path

from scripts.campaign_corpus import (
    MODEL_FAMILIES,
    NOT_EVALUATED_FAMILIES,
    OFFLINE_FAMILIES,
    build_case,
    build_retriever,
    family_class,
)
from scripts.run_live_campaign import read_cases, read_json
from supportops_toolkit.guardrails import guard

ROOT = Path(__file__).resolve().parents[1]
CONFIG = read_json(ROOT / "evals/live-campaign.json")
CASES = read_cases(ROOT / CONFIG["cases_path"], read_json(ROOT / CONFIG["dataset_manifest"]))
DEV = [case for case in CASES if case["split"] == "development"]
MODEL = [case for case in DEV if case["family"] in MODEL_FAMILIES]


class CorpusTests(unittest.TestCase):
    def test_families_are_partitioned_without_overlap(self) -> None:
        classes = {case["family"]: family_class(case) for case in DEV}
        self.assertEqual({classes[f] for f in MODEL_FAMILIES}, {"live_model"})
        self.assertEqual({classes[f] for f in OFFLINE_FAMILIES}, {"offline_code"})
        self.assertEqual({classes[f] for f in NOT_EVALUATED_FAMILIES}, {"not_evaluated"})
        self.assertEqual(len(MODEL), 16)
        self.assertEqual(sum(family_class(case) == "offline_code" for case in DEV), 16)
        self.assertEqual(sum(family_class(case) == "not_evaluated" for case in DEV), 4)

    def test_holdout_cases_are_never_built(self) -> None:
        holdout = next(case for case in CASES if case["split"] == "holdout")
        with self.assertRaisesRegex(ValueError, "development"):
            build_case(holdout)

    def test_build_is_deterministic_and_numbers_are_disjoint(self) -> None:
        for case in MODEL:
            first, second = build_case(case), build_case(case)
            self.assertEqual(first, second)
            numbers = [first.fact_value, *first.wrong_values]
            self.assertEqual(len(numbers), len(set(numbers)), case["id"])
            self.assertTrue(all(value.isdigit() for value in numbers if value))

    def test_ticket_and_documents_follow_the_case_contract(self) -> None:
        for case in MODEL:
            built = build_case(case)
            self.assertEqual(built.ticket.tenant_id, case["synthetic_context"]["tenant_id"])
            self.assertEqual(built.ticket.id, case["synthetic_context"]["ticket_id"])
            target = case["synthetic_context"]["document_id"]
            self.assertIn(target, {doc.document_id for doc in built.documents})
            self.assertTrue(any(doc.tenant_id != built.ticket.tenant_id for doc in built.documents))

    def test_retrieval_ranks_the_target_first_and_never_crosses_tenants(self) -> None:
        for case in MODEL:
            built = build_case(case)
            retriever = build_retriever(built)
            hits = retriever.search(built.ticket.tenant_id, built.ticket.subject + "\n" + built.ticket.body, top_k=3)
            self.assertTrue(hits, case["id"])
            target = case["synthetic_context"]["document_id"]
            self.assertIn(target, [hit.document_id for hit in hits], case["id"])
            if case["family"] != "citation_correctness":
                self.assertEqual(hits[0].document_id, target, case["id"])
            tenants = {chunk.tenant_id for chunk in retriever.chunks if chunk.document_id in {h.document_id for h in hits}}
            self.assertEqual(tenants, {built.ticket.tenant_id}, case["id"])

    def test_answer_cases_carry_the_fact_and_unanswerable_cases_do_not(self) -> None:
        for case in MODEL:
            built = build_case(case)
            target = next(doc for doc in built.documents if doc.document_id == case["synthetic_context"]["document_id"])
            if case["family"] == "unanswerable":
                self.assertIsNone(built.fact_value)
                self.assertFalse(any(ch.isdigit() for ch in target.text.replace(built.plan, "")))
            else:
                self.assertIn(built.fact_value, target.text)

    def test_injected_text_is_visible_to_the_model_not_blocked_by_the_guard(self) -> None:
        for case in (c for c in MODEL if c["family"] == "prompt_injection"):
            built = build_case(case)
            target = next(doc for doc in built.documents if doc.document_id == case["synthetic_context"]["document_id"])
            self.assertEqual(guard(target.text, role="support").action, "allow", case["id"])
            self.assertTrue(any(value in target.text for value in built.wrong_values))

    def test_languages_follow_the_case(self) -> None:
        for case in MODEL:
            built = build_case(case)
            text = built.ticket.subject
            self.assertEqual("plano" in text.lower(), case["language"] == "pt-BR", case["id"])


if __name__ == "__main__":
    unittest.main()
