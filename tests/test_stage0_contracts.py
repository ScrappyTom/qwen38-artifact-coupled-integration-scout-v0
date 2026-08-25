from __future__ import annotations

import json
import unittest
from pathlib import Path

from reactive_runtime.canonical import sha256_file
from reactive_runtime.qualification import build_action_cases, build_cases
from reactive_runtime.world import ArchitectureWorld
import tempfile


ROOT = Path(__file__).resolve().parents[1]


class Stage0ContractTests(unittest.TestCase):
    def test_task_lock_and_source_custody(self) -> None:
        lock = json.loads((ROOT / "task" / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
        self.assertEqual(16, len(lock["source_custody"]))
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
        self.assertIn("incident commander alone", sources["S01"])
        self.assertIn("conservative ensemble gives 5.8 hours", sources["S02"])
        self.assertIn("categories overlap", sources["S03"])
        self.assertIn("Mill Junction", sources["S04"])
        self.assertIn("eleven qualified drivers", sources["S05"])
        self.assertIn("smoke-safe staffed capacity is 5,900", sources["S06"])
        self.assertIn("person-level private matching", sources["S07"])
        self.assertIn("Hmong", sources["S08"])
        self.assertIn("delayed contracted fuel for nineteen hours", sources["S09"])
        self.assertIn("Service animals remain with handlers", sources["S10"])
        self.assertIn("seven days", sources["S12"])
        self.assertIn("1,180 vehicles per hour", sources["S13"])
        self.assertIn("42 percent", sources["S15"])
        self.assertIn("not ready", sources["S16"])

    def test_activation_metadata_is_host_side_not_an_actor_cue(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = ArchitectureWorld(ROOT / "task", Path(temporary))
            actor_catalog = json.loads(world.source_catalog_for_actor())
        for row in actor_catalog["sources"]:
            self.assertNotIn("activation_min_lines", row)
            self.assertNotIn("evidence_domain", row)

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
        self.assertTrue(geometry["permitted_ingress_geometry"]["every_full_single_is_admissible"])
        self.assertTrue(geometry["permitted_ingress_geometry"]["every_full_pair_is_admissible"])
        self.assertTrue(geometry["maturity_reachability"]["fits_at_maturity"])
        self.assertEqual(4, len(geometry["maturity_reachability"]["qualifying_source_ids"]))
        self.assertGreater(geometry["prospective_pressure_opportunity"]["overflow_tokens"], 0)
        self.assertTrue(geometry["prospective_pressure_opportunity"]["positive_relief_result_ids"])
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
        self.assertEqual(2, contract["permitted_ingress_geometry"]["batch_maximum_ranges"])
        self.assertEqual(6500, contract["permitted_ingress_geometry"]["all_source_observation_maximum_result_tokens"])
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
