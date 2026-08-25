from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.audit_meridian_source_delta_qualification import audit


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = (
    ROOT
    / "qualification_runs"
    / "2026-08-25-meridian-source-delta-expression-qualification-v0"
)


class MeridianSourceDeltaQualificationResultTests(unittest.TestCase):
    def test_audit_passes_while_qualification_fails(self) -> None:
        result = audit(ROOT, write_output=False)
        self.assertTrue(result["passed"], result["failures"])
        self.assertFalse(result["transport_passed"])
        self.assertTrue(result["material_safety_passed"])
        self.assertFalse(result["qualification_passed"])
        self.assertEqual(1, result["model_calls"])
        self.assertEqual(1, result["provider_attempts"])
        self.assertEqual(4_234, result["prompt_tokens"])
        self.assertEqual(1_010, result["completion_tokens"])
        self.assertEqual(5_244, result["serialized_tokens"])
        self.assertTrue(result["runtime_released"])
        self.assertFalse(result["measured_continuation_authorized"])

    def test_literal_transport_failure_is_frozen(self) -> None:
        result = json.loads(
            (RUN_ROOT / "QUALIFICATION_RESULT.json").read_text(encoding="utf-8")
        )
        self.assertEqual("stop", result["finish_reason"])
        self.assertFalse(result["transport_passed"])
        self.assertEqual(
            "unobserved_source_reference", result["validation"]["code"]
        )
        self.assertEqual(
            ["DRIFT", "EMBER", "HEATH", "NORTH"],
            result["validation"]["disallowed_source_ids"],
        )
        self.assertEqual(["AXIOM", "BRAMBLE"], result["validation"]["source_ids"])

    def test_rejected_relationship_identities_are_grounded_in_bramble(self) -> None:
        output = (
            RUN_ROOT
            / "calls"
            / "01-Q1_FIRST_ACTUAL_EXTERNALIZATION"
            / "assistant_content.txt"
        ).read_text(encoding="utf-8")
        bramble = (
            ROOT / "task_meridian" / "sources" / "BRAMBLE_CONTAMINATION.md"
        ).read_text(encoding="utf-8")
        for source_id in ("DRIFT", "EMBER", "HEATH", "NORTH"):
            self.assertIn(source_id, bramble)
            self.assertIn(source_id, output)
        self.assertNotIn("## SOURCE HEATH", output)
        self.assertNotIn("## SOURCE DRIFT", output)
        self.assertNotIn("## SOURCE EMBER", output)
        self.assertNotIn("## SOURCE NORTH", output)

    def test_material_safety_and_runtime_dispositions_are_separate(self) -> None:
        adjudication = json.loads(
            (
                ROOT
                / "MERIDIAN_SOURCE_DELTA_MATERIAL_SAFETY_ADJUDICATION.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(adjudication["material_safety_passed"])
        self.assertFalse(adjudication["transport_disposition"]["passed"])
        self.assertFalse(adjudication["qualification_passed"])
        self.assertFalse(adjudication["measured_continuation_authorized"])
        finalization = json.loads(
            (RUN_ROOT / "FINALIZATION.json").read_text(encoding="utf-8")
        )
        self.assertIsNone(finalization["failure"])
        self.assertTrue(finalization["release"]["released"])


if __name__ == "__main__":
    unittest.main()
