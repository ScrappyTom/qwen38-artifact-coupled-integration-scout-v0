from __future__ import annotations

import json
import unittest
from pathlib import Path

from reactive_runtime.configuration import PHASE_LIFECYCLE_CONFIGURATIONS
from reactive_runtime.configuration import phase_lifecycle_actor_actions
from reactive_runtime.orchard_boundary import verify_orchard_pressure_handoff
from tools import run_orchard_phase_lifecycle as runner
from tools.preflight_orchard_phase_lifecycle import preflight


ROOT = Path(__file__).resolve().parents[1]


class OrchardPhaseLifecycleFreezeTests(unittest.TestCase):
    def test_exact_handoff_and_postrun_preflight_refuses_duplicate(self) -> None:
        handoff = verify_orchard_pressure_handoff(ROOT)
        result = preflight(write_output=False)
        self.assertFalse(result["passed"])
        self.assertEqual(["measured_run_root_already_exists"], result["failures"])
        self.assertEqual("RESULT-006", handoff["pending_result_id"])
        self.assertEqual(["RESULT-001"], handoff["positive_relief_result_ids"])
        self.assertFalse(handoff["measured_fork_authorized"])

    def test_compound_configuration_and_budgets_are_frozen(self) -> None:
        contract = json.loads(
            (ROOT / "ORCHARD_PHASE_LIFECYCLE_MEASURED_CONTRACT.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(PHASE_LIFECYCLE_CONFIGURATIONS, runner.CONFIGURATION_ORDER)
        self.assertEqual(list(PHASE_LIFECYCLE_CONFIGURATIONS), contract["configuration_order"])
        self.assertEqual(72, contract["budgets"]["maximum_actor_calls_total"])
        self.assertEqual(24, contract["budgets"]["maximum_maintenance_calls_total"])
        self.assertEqual(96, contract["budgets"]["maximum_provider_calls_total"])
        self.assertIn("same_fallible_anchored_maintenance_on_source_externalization", contract["common_before_transition"])
        self.assertIn("replace_model_facing_verification_projection_after_every_action", contract["P1_after_transition"])

    def test_historical_request_is_inert_and_completed_run_has_exact_receipt(self) -> None:
        request = json.loads(
            (ROOT / "ORCHARD_PHASE_LIFECYCLE_AUTHORIZATION_REQUEST.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(request["authorized"])
        run_root = ROOT / "runs" / runner.RUN_ID
        self.assertTrue(run_root.exists())
        receipt = json.loads(
            (run_root / "AUTHORIZATION_RECEIPT.json").read_text(encoding="utf-8")
        )
        self.assertTrue(receipt["authorized"])
        self.assertEqual(runner.RUN_ID, receipt["authorized_run_id"])
        self.assertEqual(
            "094bbce57407568d1ef0ecd94414ae1a957e3b45",
            receipt["authorized_freeze_commit"],
        )
        self.assertEqual(1, request["attempts_per_call"])
        self.assertEqual(0, request["retries"])

    def test_runner_keeps_maintenance_common_and_changes_only_after_transition(self) -> None:
        source = (ROOT / "tools" / "run_orchard_phase_lifecycle.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('if not records or phase != "construction"', source)
        self.assertNotIn("if not records or not treatment", source)
        self.assertIn('if world.phase == "verification" and phase == "construction"', source)
        self.assertIn("if p1:\n                    recompose_p1()", source)
        self.assertIn('elif p1 and phase == "verification"', source)

    def test_construction_cannot_bypass_the_phase_transition(self) -> None:
        construction = phase_lifecycle_actor_actions(
            "F0_FIXED_SCAFFOLD_APPEND_ONLY_VERIFICATION", phase="construction"
        )
        verification = phase_lifecycle_actor_actions(
            "F0_FIXED_SCAFFOLD_APPEND_ONLY_VERIFICATION", phase="verification"
        )
        self.assertIn("begin_verification", construction)
        self.assertNotIn("run_check", construction)
        self.assertNotIn("submit", construction)
        self.assertNotIn("begin_verification", verification)
        self.assertIn("run_check", verification)
        self.assertIn("submit", verification)


if __name__ == "__main__":
    unittest.main()
