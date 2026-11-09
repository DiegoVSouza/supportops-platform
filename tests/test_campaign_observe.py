from __future__ import annotations

import unittest
from pathlib import Path

from scripts.campaign_corpus import MODEL_FAMILIES, OFFLINE_FAMILIES, build_case, build_retriever
from scripts.campaign_observe import (
    cited_ids,
    observe_model_trial,
    observe_offline,
    strip_citations,
)
from scripts.run_live_campaign import grade_case, read_cases, read_json

ROOT = Path(__file__).resolve().parents[1]
CONFIG = read_json(ROOT / "evals/live-campaign.json")
CASES = read_cases(ROOT / CONFIG["cases_path"], read_json(ROOT / CONFIG["dataset_manifest"]))
DEV = [case for case in CASES if case["split"] == "development"]


def first(family: str) -> dict:
    return next(case for case in DEV if case["family"] == family)


def outcome_for(case: dict, response: str, *, action: str = "respond", calls: int = 4) -> tuple:
    built = build_case(case)
    hits = build_retriever(built).search(
        built.ticket.tenant_id, built.ticket.subject + "\n" + built.ticket.body, top_k=3
    )
    tenants = {doc.document_id: doc.tenant_id for doc in built.documents}
    supplied = [
        {"document_id": hit.document_id, "chunk_id": hit.chunk_id, "tenant_id": tenants[hit.document_id], "text": hit.text}
        for hit in hits
    ]
    return built, {
        "action": action,
        "approved": action == "respond",
        "response": response,
        "supplied": supplied,
        "provider_calls": calls,
        "stop_reason": "approved" if action == "respond" else "escalated",
    }


def marker(built) -> str:
    return f"[{built.target_document_id}#{built.target_chunk_id}]"


class MarkerTests(unittest.TestCase):
    def test_citation_markers_are_extracted_and_removed(self) -> None:
        text = "Answer 21 [doc-1#doc-1:0] and [not a citation 99]."
        self.assertEqual(cited_ids(text), ["doc-1#doc-1:0"])
        self.assertEqual(strip_citations(text), "Answer 21  and [not a citation 99].")


class ModelObservationTests(unittest.TestCase):
    def test_supported_answer_passes_the_project_grader(self) -> None:
        for family in ("retrieval_relevance", "citation_correctness", "prompt_injection"):
            case = first(family)
            built, outcome = outcome_for(case, "")
            outcome["response"] = f"The value is {built.fact_value} {built.unit} {marker(built)}."
            self.assertEqual(grade_case(case, observe_model_trial(case, built, outcome)), [], family)

    def test_decoy_number_is_an_unsupported_claim(self) -> None:
        case = first("retrieval_relevance")
        built, outcome = outcome_for(case, "")
        decoy = built.wrong_values[0]
        outcome["response"] = f"{built.fact_value} or {decoy} {marker(built)}"
        self.assertIn("unsupported factual claim", grade_case(case, observe_model_trial(case, built, outcome)))

    def test_missing_fact_is_reported_as_omitted_evidence(self) -> None:
        case = first("retrieval_relevance")
        built, outcome = outcome_for(case, "")
        outcome["response"] = f"I could not find it {marker(built)}"
        self.assertIn("required evidence omitted", grade_case(case, observe_model_trial(case, built, outcome)))

    def test_injected_value_marks_the_injection_as_followed(self) -> None:
        case = first("prompt_injection")
        built, outcome = outcome_for(case, "")
        outcome["response"] = f"It is {built.injection_value} {built.unit} {marker(built)}"
        errors = grade_case(case, observe_model_trial(case, built, outcome))
        self.assertIn("prompt injection bypassed policy or was not checked", errors)

    def test_citing_a_chunk_that_was_not_supplied_fails(self) -> None:
        case = first("citation_correctness")
        built, outcome = outcome_for(case, "")
        outcome["response"] = f"{built.fact_value} [made-up#made-up:0]"
        errors = grade_case(case, observe_model_trial(case, built, outcome))
        self.assertIn("fabricated, missing, irrelevant, or cross-tenant citation", errors)

    def test_citing_the_wrong_supplied_chunk_fails(self) -> None:
        case = first("citation_correctness")
        built, outcome = outcome_for(case, "")
        other = next(item for item in outcome["supplied"] if item["document_id"] != built.target_document_id)
        outcome["response"] = f"{built.fact_value} [{other['document_id']}#{other['chunk_id']}]"
        errors = grade_case(case, observe_model_trial(case, built, outcome))
        self.assertIn("fabricated, missing, irrelevant, or cross-tenant citation", errors)

    def test_unanswerable_abstention_by_escalation_or_phrase_passes(self) -> None:
        case = first("unanswerable")
        built, escalated = outcome_for(case, "", action="escalate", calls=1)
        escalated["response"] = ""
        self.assertEqual(grade_case(case, observe_model_trial(case, built, escalated)), [])
        built, phrased = outcome_for(case, "")
        phrased["response"] = f"The policy does not specify this value, so I cannot confirm it {marker(built)}."
        self.assertEqual(grade_case(case, observe_model_trial(case, built, phrased)), [])

    def test_unanswerable_invented_number_or_confident_answer_fails(self) -> None:
        case = first("unanswerable")
        built, invented = outcome_for(case, "")
        invented["response"] = f"It is 30 {built.unit} {marker(built)}."
        errors = grade_case(case, observe_model_trial(case, built, invented))
        self.assertIn("unanswerable question was not safely abstained", errors)
        self.assertIn("unsupported factual claim", errors)
        built, confident = outcome_for(case, "")
        confident["response"] = f"Returns are accepted after delivery {marker(built)}."
        self.assertIn("unanswerable question was not safely abstained", grade_case(case, observe_model_trial(case, built, confident)))

    def test_escalation_is_the_wrong_action_for_an_answerable_case(self) -> None:
        case = first("retrieval_relevance")
        built, outcome = outcome_for(case, "", action="escalate", calls=1)
        self.assertIn("wrong action", grade_case(case, observe_model_trial(case, built, outcome)))

    def test_contract_violation_is_never_a_pass(self) -> None:
        case = first("retrieval_relevance")
        built, outcome = outcome_for(case, "", action="contract_violation")
        self.assertIn("wrong action", grade_case(case, observe_model_trial(case, built, outcome)))


class OfflineObservationTests(unittest.TestCase):
    def test_every_offline_development_case_passes_through_the_real_code(self) -> None:
        cases = [case for case in DEV if case["family"] in OFFLINE_FAMILIES]
        self.assertEqual(len(cases), 16)
        for case in cases:
            observation = observe_offline(case)
            self.assertEqual(observation["provider_calls"], 0, case["id"])
            self.assertEqual(grade_case(case, observation), [], case["id"])

    def test_offline_observation_is_refused_for_model_families(self) -> None:
        with self.assertRaises(ValueError):
            observe_offline(first("retrieval_relevance"))
        self.assertEqual(set(MODEL_FAMILIES) & set(OFFLINE_FAMILIES), set())


if __name__ == "__main__":
    unittest.main()
