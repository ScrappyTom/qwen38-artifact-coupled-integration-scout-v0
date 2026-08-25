from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.audit_bluehaven_pressure_screen import audit


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "2026-08-25-bluehaven-pressure-screen-v0"


class BluehavenPressureScreenAuditTests(unittest.TestCase):
    def test_exact_live_boundary_passes_independent_audit(self) -> None:
        result = audit(ROOT, write_outputs=False)
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual([], result["failures"])
        self.assertEqual(6, result["actor_calls"])
        self.assertEqual(6, result["provider_attempts"])
        self.assertEqual(71_166, result["serialized_tokens"])
        self.assertEqual("RESULT-006", result["pending_result_id"])
        self.assertEqual(23_820, result["ordinary_prospective_prompt_tokens"])
        self.assertEqual(2_828, result["overflow_tokens"])
        self.assertEqual(["RESULT-001"], result["positive_relief_result_ids"])
        self.assertEqual(20_917, result["positive_relief_after_tokens"])
        self.assertTrue(result["interaction_trigger_qualified"])
        self.assertFalse(result["measured_fork_authorized"])

    def test_pressure_history_is_six_valid_two_source_batches(self) -> None:
        trace = json.loads((RUN_ROOT / "CALL_TRACE.json").read_text(encoding="utf-8"))
        self.assertEqual(6, len(trace))
        expected = [
            ("S01", "S02"),
            ("S03", "S04"),
            ("S05", "S06"),
            ("S07", "S08"),
            ("S09", "S10"),
            ("S11", "S12"),
        ]
        for row, source_ids in zip(trace, expected, strict=True):
            self.assertIsNone(row["rejection_code"])
            self.assertEqual("read_batch", row["parsed_action"]["action"])
            requests = row["parsed_action"]["requests"]
            self.assertEqual(source_ids, tuple(request["source_id"] for request in requests))
            self.assertTrue(all(request["start_line"] == 1 for request in requests))
            self.assertTrue(all(request["end_line"] == 70 for request in requests))
            self.assertEqual(row["candidate_sha256_before"], row["candidate_sha256_after"])

    def test_handoff_binds_exact_audited_fork_and_authorizes_nothing(self) -> None:
        handoff = json.loads(
            (ROOT / "BLUEHAVEN_PRESSURE_BOUNDARY_HANDOFF.json").read_text(encoding="utf-8")
        )
        audit_receipt = json.loads(
            (ROOT / "BLUEHAVEN_PRESSURE_SCREEN_AUDIT.json").read_text(encoding="utf-8")
        )
        self.assertEqual("passed_authentic_pressure_boundary", handoff["status"])
        self.assertEqual(audit_receipt["run_id"], handoff["run_id"])
        self.assertEqual(audit_receipt["pending_result_id"], handoff["pending_result_id"])
        self.assertEqual(
            audit_receipt["positive_relief_result_ids"],
            handoff["positive_relief_result_ids"],
        )
        self.assertFalse(handoff["pending_result_delivered"])
        self.assertFalse(handoff["candidate_changed"])
        self.assertFalse(handoff["candidate_submitted"])
        self.assertFalse(handoff["measured_fork_authorized"])

    def test_activation_is_source_coverage_not_result_count(self) -> None:
        audit_receipt = json.loads(
            (ROOT / "BLUEHAVEN_PRESSURE_SCREEN_AUDIT.json").read_text(encoding="utf-8")
        )
        activation = audit_receipt["activation_snapshot"]
        self.assertEqual(10, len(activation["qualifying_sources"]))
        self.assertEqual(10, len(activation["qualifying_domains"]))
        self.assertEqual(140, activation["pending_novel_lines"])
        self.assertEqual(
            {f"S{ordinal:02d}" for ordinal in range(1, 11)},
            set(activation["coverage_lines"]),
        )

    def test_screen_trace_contains_no_treatment(self) -> None:
        result = json.loads((RUN_ROOT / "SCREEN_RESULT.json").read_text(encoding="utf-8"))
        trace = json.loads((RUN_ROOT / "CALL_TRACE.json").read_text(encoding="utf-8"))
        self.assertFalse(result["candidate_submitted"])
        self.assertTrue(all(row["result_kind"] == "source_observation" for row in trace))
        self.assertFalse((RUN_ROOT / "maintenance").exists())
        self.assertFalse((RUN_ROOT / "treatment").exists())


if __name__ == "__main__":
    unittest.main()
