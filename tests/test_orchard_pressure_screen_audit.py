from __future__ import annotations

import json
import unittest
from pathlib import Path

from reactive_runtime.orchard_boundary import verify_orchard_pressure_handoff
from tools.audit_orchard_pressure_screen import audit


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "2026-08-27-orchard-phase-lifecycle-pressure-screen-v0"


class OrchardPressureScreenAuditTests(unittest.TestCase):
    def test_exact_live_boundary_passes_independent_audit(self) -> None:
        result = audit(ROOT, write_outputs=False)
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual(6, result["actor_calls"])
        self.assertEqual(62_106, result["serialized_tokens"])
        self.assertEqual("RESULT-006", result["pending_result_id"])
        self.assertEqual(21_152, result["ordinary_prospective_prompt_tokens"])
        self.assertEqual(160, result["overflow_tokens"])
        self.assertEqual(["RESULT-001"], result["positive_relief_result_ids"])
        self.assertEqual(18_509, result["positive_relief_after_tokens"])
        self.assertEqual(2_483, result["remaining_prompt_headroom_tokens"])
        self.assertFalse(result["expression_qualification_authorized"])
        self.assertFalse(result["measured_fork_authorized"])

    def test_history_is_six_valid_actor_selected_batches(self) -> None:
        trace = json.loads((RUN_ROOT / "CALL_TRACE.json").read_text(encoding="utf-8"))
        expected = [
            ("CHARTER", "CULTURE"),
            ("STERILE", "CHILL"),
            ("CURRENT", "ASSAY"),
            ("GUARD", "SUPPLY"),
            ("SAFETY", "SIGNAL"),
            ("COMMUNE", "CHANGE"),
        ]
        self.assertEqual(len(expected), len(trace))
        for row, source_ids in zip(trace, expected, strict=True):
            self.assertIsNone(row["rejection_code"])
            self.assertEqual("read_batch", row["parsed_action"]["action"])
            requests = row["parsed_action"]["requests"]
            self.assertEqual(source_ids, tuple(item["source_id"] for item in requests))
            self.assertEqual(row["candidate_sha256_before"], row["candidate_sha256_after"])

    def test_handoff_is_exact_and_authorizes_nothing(self) -> None:
        handoff = verify_orchard_pressure_handoff(ROOT)
        self.assertFalse(handoff["pending_result_delivered"])
        self.assertFalse(handoff["candidate_changed"])
        self.assertFalse(handoff["candidate_submitted"])
        self.assertFalse(handoff["expression_qualification_authorized"])
        self.assertFalse(handoff["measured_fork_authorized"])

    def test_screen_contains_no_treatment(self) -> None:
        result = json.loads((RUN_ROOT / "SCREEN_RESULT.json").read_text(encoding="utf-8"))
        trace = json.loads((RUN_ROOT / "CALL_TRACE.json").read_text(encoding="utf-8"))
        self.assertFalse(result["candidate_submitted"])
        self.assertTrue(all(row["result_kind"] == "source_observation" for row in trace))
        self.assertFalse((RUN_ROOT / "maintenance").exists())
        self.assertFalse((RUN_ROOT / "treatment").exists())


if __name__ == "__main__":
    unittest.main()
