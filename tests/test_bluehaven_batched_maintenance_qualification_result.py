from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.audit_bluehaven_batched_maintenance_qualification import audit


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = (
    ROOT
    / "qualification_runs"
    / "2026-08-25-bluehaven-batched-maintenance-expression-qualification-v0"
)


class BluehavenBatchedMaintenanceQualificationResultTests(unittest.TestCase):
    def test_independent_audit_passes_while_qualification_fails(self) -> None:
        result = audit(ROOT, write_output=False)
        self.assertTrue(result["passed"], result["failures"])
        self.assertFalse(result["qualification_passed"])
        self.assertEqual(2, result["model_calls"])
        self.assertEqual(2, result["provider_attempts"])
        self.assertEqual(22_674, result["prompt_tokens"])
        self.assertEqual(2_332, result["completion_tokens"])
        self.assertEqual(25_006, result["serialized_tokens"])
        self.assertTrue(result["runtime_released"])
        self.assertFalse(result["measured_continuation_authorized"])

    def test_literal_case_dispositions_are_frozen(self) -> None:
        result = json.loads(
            (RUN_ROOT / "QUALIFICATION_RESULT.json").read_text(encoding="utf-8")
        )
        self.assertFalse(result["passed"])
        first, second = result["cases"]
        self.assertFalse(first["accepted"])
        self.assertEqual("unobserved_source_reference", first["validation"]["code"])
        self.assertEqual(
            ["S07", "S08", "S09", "S10", "S11", "S12"],
            first["validation"]["disallowed_source_ids"],
        )
        self.assertTrue(second["accepted"])
        self.assertEqual("accepted", second["validation"]["code"])
        self.assertEqual([], second["validation"]["disallowed_source_ids"])

    def test_cold_start_contains_substantive_unseen_source_claims(self) -> None:
        output = (
            RUN_ROOT
            / "calls"
            / "01-Q1_INITIAL_THREE_RESULT_BATCH"
            / "assistant_content.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("[S07] Hospitals/dialysis", output)
        self.assertIn("[S10] Multilingual redundant warning", output)
        self.assertIn("[S11] Executable sequence", output)
        self.assertIn("[S12] Independent review blockers", output)

    def test_run_is_released_and_no_continuation_exists(self) -> None:
        finalization = json.loads(
            (RUN_ROOT / "FINALIZATION.json").read_text(encoding="utf-8")
        )
        self.assertIsNone(finalization["failure"])
        self.assertTrue(finalization["release"]["released"])
        self.assertFalse((ROOT / "BLUEHAVEN_MEASURED_AUTHORIZATION_REQUEST.json").exists())
        self.assertFalse((RUN_ROOT / "measured").exists())


if __name__ == "__main__":
    unittest.main()
