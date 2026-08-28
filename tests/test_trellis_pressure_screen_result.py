from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TrellisPressureScreenResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = json.loads((ROOT / "TRELLIS_PRESSURE_SCREEN_AUDIT.json").read_text(encoding="utf-8"))
        cls.result = json.loads((ROOT / "runs" / "2026-08-28-trellis-artifact-centered-pressure-screen-v0" / "SCREEN_RESULT.json").read_text(encoding="utf-8"))

    def test_audit_passes_and_fork_is_not_authorized(self) -> None:
        self.assertTrue(self.audit["passed"])
        self.assertFalse(self.audit["pressure_qualified"])
        self.assertFalse(self.audit["measured_fork_authorized"])
        self.assertTrue(self.audit["runtime_released"])

    def test_exact_nonqualification_geometry(self) -> None:
        self.assertEqual(self.result["terminal_disposition"], "pressure_before_ingress_aligned_activation")
        self.assertEqual(self.audit["ordinary_prospective_prompt_tokens"], 21_401)
        self.assertEqual(self.audit["overflow_tokens"], 409)
        self.assertEqual(self.audit["positive_relief_result_ids"], ["RESULT-001"])
        self.assertEqual(self.audit["positive_relief_after_tokens"], 18_663)

    def test_visible_and_pending_sources_remain_distinct(self) -> None:
        self.assertEqual(len(self.audit["visible_qualifying_sources"]), 6)
        self.assertEqual(self.audit["pending_source_ids"], ["COMMS", "TRANSIT"])
        self.assertFalse(self.audit["pending_result_delivered"])

    def test_all_calls_are_valid_acquisition_and_candidate_is_unchanged(self) -> None:
        trace = json.loads((ROOT / "runs" / self.result["run_id"] / "CALL_TRACE.json").read_text(encoding="utf-8"))
        self.assertEqual(len(trace), 7)
        self.assertTrue(all(row["parsed_action"]["action"] == "read_batch" for row in trace))
        self.assertTrue(all(row["rejection_code"] is None for row in trace))
        self.assertTrue(all(row["candidate_sha256_before"] == row["candidate_sha256_after"] for row in trace))


if __name__ == "__main__":
    unittest.main()
