from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.audit_aster_relational_expression_qualification import audit


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = (
    ROOT
    / "qualification_runs"
    / "2026-08-26-aster-relational-expression-qualification-v0"
)


class AsterRelationalExpressionQualificationResultTests(unittest.TestCase):
    def test_audit_passes_while_qualification_fails(self) -> None:
        result = audit(ROOT)
        frozen = json.loads(
            (
                ROOT / "ASTER_RELATIONAL_EXPRESSION_QUALIFICATION_AUDIT.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(frozen, result)
        self.assertTrue(result["passed"], result["failures"])
        self.assertFalse(result["transport_passed"])
        self.assertTrue(result["raw_output_material_safety_passed"])
        self.assertFalse(result["admission_based_relevance_gate_passed"])
        self.assertFalse(result["qualification_passed"])
        self.assertEqual(4, result["raw_claim_count"])
        self.assertEqual(0, result["mechanically_admitted_claim_count"])
        self.assertEqual(1, result["model_calls"])
        self.assertEqual(1, result["provider_attempts"])
        self.assertEqual(4_428, result["prompt_tokens"])
        self.assertEqual(708, result["completion_tokens"])
        self.assertEqual(5_136, result["serialized_tokens"])
        self.assertTrue(result["runtime_released"])
        self.assertFalse(result["measured_continuation_authorized"])

    def test_literal_transport_failure_is_frozen(self) -> None:
        result = json.loads(
            (RUN_ROOT / "QUALIFICATION_RESULT.json").read_text(encoding="utf-8")
        )
        self.assertEqual("stop", result["finish_reason"])
        self.assertFalse(result["transport_passed"])
        self.assertEqual(
            "evidence_quote_not_unique_exact_line", result["validation"]["code"]
        )
        self.assertEqual([], result["validation"]["claims"])
        self.assertEqual([], result["validation"]["source_ids"])
        self.assertEqual([], result["validation"]["provenance"])

    def test_all_quotes_are_unique_sentence_substrings_not_complete_lines(self) -> None:
        adjudication = json.loads(
            (
                ROOT
                / "ASTER_RELATIONAL_EXPRESSION_MATERIAL_SAFETY_ADJUDICATION.json"
            ).read_text(encoding="utf-8")
        )
        failures = adjudication["transport_disposition"]["quote_failures"]
        self.assertEqual(4, len(failures))
        self.assertEqual(
            {"ANCHOR-001", "ANCHOR-002", "BRIDGE-001", "BRIDGE-002"},
            {row["claim_id"] for row in failures},
        )
        self.assertTrue(
            all("not the complete line" in row["disposition"] for row in failures)
        )

    def test_semantic_safety_and_transport_are_separate(self) -> None:
        adjudication = json.loads(
            (
                ROOT
                / "ASTER_RELATIONAL_EXPRESSION_MATERIAL_SAFETY_ADJUDICATION.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(adjudication["material_safety_passed"])
        self.assertFalse(adjudication["transport_disposition"]["passed"])
        self.assertFalse(adjudication["admission_based_relevance_gate_passed"])
        self.assertFalse(adjudication["qualification_passed"])
        self.assertFalse(adjudication["measured_continuation_authorized"])
        finalization = json.loads(
            (RUN_ROOT / "FINALIZATION.json").read_text(encoding="utf-8")
        )
        self.assertIsNone(finalization["failure"])
        self.assertTrue(finalization["release"]["released"])


if __name__ == "__main__":
    unittest.main()
