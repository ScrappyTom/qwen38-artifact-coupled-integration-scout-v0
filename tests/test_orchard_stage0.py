from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reactive_runtime.canonical import canonical_json_text
from reactive_runtime.configuration import phase_lifecycle_actor_actions
from reactive_runtime.orchard_world import OrchardWorld
from reactive_runtime.phase_lifecycle import p1_verification_messages
from reactive_runtime.records import ResultLedger
from reactive_runtime.world import ActionRejected
from tools.materialize_orchard_world import SOURCE_IDS, SPECS, document
from tools.orchard_stage0 import TASK


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "ORCHARD_PHASE_LIFECYCLE_STAGE0_PREFLIGHT.json"


class OrchardStage0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))

    def test_fresh_task_lock_and_sources(self) -> None:
        lock = json.loads((TASK / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
        self.assertEqual("orchard-biologics-restart-decision-v0", lock["task_id"])
        self.assertEqual(13, len(lock["source_custody"]))
        self.assertEqual(SOURCE_IDS, tuple(row["source_id"] for row in lock["source_custody"]))
        for spec in SPECS:
            self.assertEqual(document(spec), (TASK / "sources" / spec.filename).read_text(encoding="utf-8"))

    def test_preflight_is_offline_and_passed(self) -> None:
        self.assertTrue(self.preflight["passed"])
        self.assertEqual([], self.preflight["failures"])
        self.assertEqual(0, self.preflight["provider_calls"])
        self.assertFalse(self.preflight["gpu_authorized"])

    def test_prospective_pressure_precedes_final_source(self) -> None:
        pressure = self.preflight["prospective_pressure_opportunity"]
        self.assertEqual(6, pressure["step"])
        self.assertEqual("RESULT-006", pressure["pending_result_id"])
        self.assertEqual(["RESULT-001"], pressure["selected_result_ids"])
        self.assertGreater(pressure["ordinary_prompt_tokens"], 20_992)
        self.assertLessEqual(pressure["relieved_prompt_tokens"], 20_992)
        self.assertNotIn("REVIEW", self.preflight["prospective_path"][-1]["source_ids"])

    def test_whole_system_lifecycles_reach_current_recheck_and_submission(self) -> None:
        fixtures = self.preflight["provider_free_lifecycles"]
        self.assertEqual(2, len(fixtures))
        self.assertEqual(fixtures[0]["final_candidate_sha256"], fixtures[1]["final_candidate_sha256"])
        self.assertTrue(all(row["construction_milestone"]["passed"] for row in fixtures))
        self.assertTrue(all(row["prior_check_stale_after_patch"] for row in fixtures))
        self.assertTrue(all(row["recheck_passed"] and row["submitted"] for row in fixtures))
        f0, p1 = fixtures
        self.assertGreater(f0["prompt_tokens"]["after_recheck"], f0["prompt_tokens"]["after_patch"])
        self.assertLess(p1["prompt_tokens"]["after_recheck"], p1["prompt_tokens"]["after_patch"])

    def test_relationship_red_team_is_not_keyword_only(self) -> None:
        rows = self.preflight["relationship_red_team"]
        self.assertEqual(4, len(rows))
        self.assertTrue(all(row["caught"] for row in rows))

    def test_phase_transition_is_mechanical_and_not_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = OrchardWorld(TASK, Path(temporary))
            with self.assertRaises(ActionRejected):
                world.execute({"action": "begin_verification"}, result_id="EARLY")
        self.assertIn("begin_verification", phase_lifecycle_actor_actions("F0_FIXED_SCAFFOLD_APPEND_ONLY_VERIFICATION", phase="construction"))
        self.assertNotIn("begin_verification", phase_lifecycle_actor_actions("P1_PHASE_CONDITIONAL_CURRENT_VERIFICATION", phase="verification"))

    def test_p1_projection_drops_semantic_bytes_but_keeps_exact_handles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = OrchardWorld(TASK, Path(temporary))
            ledger = ResultLedger()
            messages = p1_verification_messages(
                task_system="system", task_text="task", action_text="actions",
                source_catalog=world.source_catalog_for_actor(), world=world, ledger=ledger,
                pending_result_id=None, latest_effect_result_id=None,
                full_history_handle="history://exact", scaffold_handle="register://exact",
            )
        rendered = canonical_json_text(messages)
        self.assertIn("register://exact", rendered)
        self.assertIn("history://exact", rendered)
        self.assertNotIn("NON-AUTHORITATIVE, INCOMPLETE SEMANTIC RESIDUE", rendered)

    def test_pressure_screen_is_treatment_free_and_inert(self) -> None:
        contract = json.loads((ROOT / "ORCHARD_PRESSURE_SCREEN_CONTRACT.json").read_text(encoding="utf-8"))
        request = json.loads((ROOT / "ORCHARD_PRESSURE_SCREEN_AUTHORIZATION_REQUEST.json").read_text(encoding="utf-8"))
        self.assertFalse(contract["semantic_maintenance_present"])
        self.assertFalse(contract["treatment_present"])
        self.assertEqual(10, contract["minimum_qualifying_sources"])
        self.assertEqual(30, contract["maximum_actor_calls"])
        self.assertFalse(contract["gpu_authorized"])
        self.assertFalse(request["authorized"])


if __name__ == "__main__":
    unittest.main()
