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
        self.assertIn("QUALIFICATION_HANDOFF.json", Path(runner.__file__).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
