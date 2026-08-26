from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.audit_aster_pressure_screen import audit


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "2026-08-25-aster-provenance-relational-pressure-screen-v0"


class AsterPressureScreenAuditTests(unittest.TestCase):
    def test_exact_live_boundary_passes_independent_audit(self) -> None:
        result = audit(ROOT, write_outputs=False)
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual([], result["failures"])
        self.assertEqual(6, result["actor_calls"])
        self.assertEqual(6, result["provider_attempts"])
        self.assertEqual(66_362, result["serialized_tokens"])
        self.assertEqual("RESULT-006", result["pending_result_id"])
        self.assertEqual(21_787, result["ordinary_prospective_prompt_tokens"])
        self.assertEqual(795, result["overflow_tokens"])
        self.assertEqual(["RESULT-001"], result["positive_relief_result_ids"])
        self.assertEqual(["RESULT-001"], result["externalized_source_result_ids"])
        self.assertEqual(18_951, result["positive_relief_after_tokens"])
        self.assertEqual(2_041, result["remaining_prompt_headroom_tokens"])
        self.assertTrue(result["interaction_trigger_qualified"])
        self.assertFalse(result["expression_qualification_authorized"])
        self.assertFalse(result["measured_fork_authorized"])

    def test_pressure_history_is_six_valid_two_source_batches(self) -> None:
        trace = json.loads((RUN_ROOT / "CALL_TRACE.json").read_text(encoding="utf-8"))
        expected = [
            ("ANCHOR", "BRIDGE"),
            ("CIRRUS", "DUSK"),
            ("EMBER", "FORGE"),
            ("GROVE", "HARBOR"),
            ("IRIS", "JUNIPER"),
            ("KELP", "LATTICE"),
        ]
        self.assertEqual(len(expected), len(trace))
        for row, source_ids in zip(trace, expected, strict=True):
            self.assertIsNone(row["rejection_code"])
            self.assertEqual("read_batch", row["parsed_action"]["action"])
            requests = row["parsed_action"]["requests"]
            self.assertEqual(source_ids, tuple(item["source_id"] for item in requests))
            self.assertTrue(all(item["start_line"] == 1 for item in requests))
            self.assertTrue(all(item["end_line"] == 64 for item in requests))
            self.assertEqual(
                row["candidate_sha256_before"], row["candidate_sha256_after"]
            )

    def test_handoff_binds_exact_audited_fork_and_authorizes_nothing(self) -> None:
        handoff = json.loads(
            (ROOT / "ASTER_PRESSURE_BOUNDARY_HANDOFF.json").read_text(encoding="utf-8")
        )
        receipt = json.loads(
            (ROOT / "ASTER_PRESSURE_SCREEN_AUDIT.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            "passed_authentic_interaction_pressure_boundary", handoff["status"]
        )
        self.assertEqual(receipt["run_id"], handoff["run_id"])
        self.assertEqual(receipt["pending_result_id"], handoff["pending_result_id"])
        self.assertEqual(
            receipt["positive_relief_result_ids"], handoff["positive_relief_result_ids"]
        )
        self.assertEqual(
            receipt["externalized_source_result_ids"],
            handoff["externalized_source_result_ids"],
        )
        self.assertFalse(handoff["pending_result_delivered"])
        self.assertFalse(handoff["candidate_changed"])
        self.assertFalse(handoff["candidate_submitted"])
        self.assertIsNone(handoff["current_check_binding"])
        self.assertFalse(handoff["expression_qualification_authorized"])
        self.assertFalse(handoff["measured_fork_authorized"])

    def test_screen_trace_contains_no_treatment(self) -> None:
        result = json.loads(
            (RUN_ROOT / "SCREEN_RESULT.json").read_text(encoding="utf-8")
        )
        trace = json.loads((RUN_ROOT / "CALL_TRACE.json").read_text(encoding="utf-8"))
        self.assertFalse(result["candidate_submitted"])
        self.assertTrue(
            all(row["result_kind"] == "source_observation" for row in trace)
        )
        self.assertFalse((RUN_ROOT / "maintenance").exists())
        self.assertFalse((RUN_ROOT / "treatment").exists())


if __name__ == "__main__":
    unittest.main()
