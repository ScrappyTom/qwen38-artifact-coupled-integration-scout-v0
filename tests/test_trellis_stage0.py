from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TrellisStage0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = json.loads((ROOT / "TRELLIS_STAGE0_RESULT.json").read_text(encoding="utf-8"))
        cls.lock = json.loads((ROOT / "task_trellis" / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
        cls.contract = json.loads((ROOT / "TRELLIS_PRESSURE_SCREEN_CONTRACT.json").read_text(encoding="utf-8"))

    def test_fresh_task_and_source_custody(self) -> None:
        self.assertEqual(self.lock["task_id"], "trellis-heat-continuity-decision-v0")
        self.assertEqual(len(self.lock["source_custody"]), 12)
        self.assertEqual(len({row["evidence_domain"] for row in self.lock["source_custody"]}), 12)
        for row in self.lock["files"]:
            self.assertTrue((ROOT / "task_trellis" / row["path"]).is_file())

    def test_provider_free_stage0_passes_complete_lifecycle(self) -> None:
        self.assertTrue(self.result["passed"])
        self.assertEqual(self.result["provider_model_calls"], 0)
        lifecycle = self.result["lifecycle"]
        self.assertTrue(lifecycle["milestone_passed"])
        self.assertFalse(lifecycle["first_check_passed"])
        self.assertTrue(lifecycle["repair_changed_candidate"])
        self.assertTrue(lifecycle["recheck_passed"])
        self.assertTrue(lifecycle["submitted"])

    def test_scaffold_is_partial_requirement_coupled_and_nonfatal(self) -> None:
        scaffold = self.result["scaffold"]
        self.assertEqual(scaffold["admitted_claim_ids"], ["COUNCIL_T01"])
        self.assertEqual(scaffold["rejected_codes"]["CLIMATE_BAD"], "target_requirement_unknown")
        self.assertEqual(scaffold["requirement_index"]["T01"], ["COUNCIL_T01"])
        self.assertTrue(scaffold["register_changed"])

    def test_pressure_geometry_is_realized_not_world_size_only(self) -> None:
        pressure = self.result["pressure_geometry"]["pressure"]
        self.assertGreater(pressure["ordinary_prompt_tokens"], 20_992)
        self.assertGreaterEqual(len(pressure["delivered_sources"]), 8)
        self.assertTrue(pressure["relief_feasible"])
        self.assertLessEqual(pressure["relief_prompt_tokens"], 20_992)

    def test_live_screen_is_common_and_inert(self) -> None:
        self.assertFalse(self.contract["semantic_maintenance_present"])
        self.assertFalse(self.contract["treatment_present"])
        self.assertFalse(self.contract["gpu_authorized"])
        from tools import run_trellis_pressure_screen as runner

        self.assertEqual(runner.RUN_ID, self.contract["run_id"])
        self.assertEqual(runner.SCOPE, self.contract["scope"])
        self.assertEqual(runner.SEED, self.contract["seed"])
        self.assertEqual(runner.MAX_CALLS, self.contract["maximum_actor_calls"])
        request = json.loads((ROOT / "TRELLIS_PRESSURE_SCREEN_AUTHORIZATION_REQUEST.json").read_text(encoding="utf-8"))
        self.assertFalse(request["authorized"])


if __name__ == "__main__":
    unittest.main()
