from __future__ import annotations

import json
import unittest
from pathlib import Path

from reactive_runtime.canonical import sha256_file
from reactive_runtime.qualification import build_action_cases, build_cases


ROOT = Path(__file__).resolve().parents[1]


class Stage0ContractTests(unittest.TestCase):
    def test_task_lock_and_source_custody(self) -> None:
        lock = json.loads((ROOT / "task" / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
        self.assertEqual(14, len(lock["source_custody"]))
        for row in lock["files"]:
            self.assertEqual(row["sha256"], sha256_file(ROOT / "task" / row["path"]))

    def test_frozen_world_facts_are_recoverable_from_independent_sources(self) -> None:
        catalog = json.loads(
            (ROOT / "task" / "SOURCE_CATALOG.json").read_text(encoding="utf-8")
        )
        sources = {
            row["source_id"]: (ROOT / "task" / row["path"]).read_text(encoding="utf-8")
            for row in catalog["sources"]
        }
        self.assertIn("producer_id:event_id", sources["S03"])
        self.assertIn("31 hours", sources["S06"])
        self.assertIn("48-hour", sources["S06"])
        self.assertIn("forward-fix", sources["S04"])
        self.assertIn("fail-closed", sources["S07"])
        self.assertIn("11 hours and 8 minutes", sources["S08"])
        self.assertIn("twelve hours", sources["S08"])
        self.assertIn("every tenant-hour", sources["S10"])
        self.assertIn("above 60%", sources["S12"])
        self.assertIn("not ready", sources["S14"])

    def test_qualification_contract_matches_independent_cases(self) -> None:
        contract = json.loads((ROOT / "MAINTENANCE_QUALIFICATION_CONTRACT.json").read_text(encoding="utf-8"))
        cases = build_cases(ROOT)
        action_cases = build_action_cases(ROOT)
        self.assertEqual(contract["case_order"], [case.case_id for case in (*cases, *action_cases)])
        self.assertEqual(4, contract["maximum_model_calls"])
        self.assertEqual(("S02",), cases[0].allowed_source_ids)
        self.assertEqual(("S02", "S03"), cases[1].allowed_source_ids)

    def test_geometry_refuses_world_size_as_activation_proof(self) -> None:
        geometry = json.loads((ROOT / "STAGE0_GEOMETRY.json").read_text(encoding="utf-8"))
        self.assertGreater(geometry["source_corpus_tokens"], 25088)
        self.assertFalse(geometry["activation_qualified"])
        self.assertIn("screening trajectory", geometry["activation_blocker"])
        self.assertEqual(8, geometry["trajectory_budget"]["postconstruction_calls"])
        self.assertEqual(4, geometry["trajectory_budget"]["clean_postconstruction_path_calls"])

    def test_provider_free_loop_covers_both_feedback_systems(self) -> None:
        fixture = json.loads((ROOT / "STAGE0_INTERACTION_FIXTURE.json").read_text(encoding="utf-8"))
        self.assertTrue(fixture["passed"])
        by_id = {row["configuration_id"]: row for row in fixture["configurations"]}
        self.assertFalse(by_id["D0_DETACHED"]["candidate_changed_by_maintenance"])
        self.assertTrue(by_id["A1_COUPLED"]["candidate_changed_by_maintenance"])
        for row in by_id.values():
            self.assertEqual("stale", row["post_repair_prior_check_currency"])
            self.assertEqual("current", row["recheck_currency"])

    def test_pressure_screen_contract_matches_runner(self) -> None:
        from tools import run_pressure_screen as runner

        contract = json.loads((ROOT / "PRESSURE_SCREEN_CONTRACT.json").read_text(encoding="utf-8"))
        self.assertEqual(runner.RUN_ID, contract["run_id"])
        self.assertEqual(runner.MAX_CALLS, contract["maximum_actor_calls"])
        self.assertEqual(runner.MAX_SERIALIZED, contract["maximum_serialized_tokens"])
        self.assertEqual(runner.PROMPT_LIMIT, contract["prompt_limit"])
        self.assertIn("strictly positive first-fit relief", contract["qualifying_endpoint"])
        self.assertNotIn("verify_qualification_handoff", Path(runner.__file__).read_text(encoding="utf-8"))

    def test_model_seed_lock_matches_screen_and_measured_runners(self) -> None:
        from tools import run_measured_interaction as measured
        from tools import run_pressure_screen as screen

        profile = json.loads(
            (ROOT / "MODEL_PROFILE_LOCK.json").read_text(encoding="utf-8")
        )
        self.assertEqual(screen.SEED, profile["screen_seed"])
        self.assertEqual(measured.ACTOR_SEED, profile["measured_actor_seed"])
        self.assertEqual(measured.MAINTENANCE_SEED, profile["measured_maintenance_seed"])


if __name__ == "__main__":
    unittest.main()
