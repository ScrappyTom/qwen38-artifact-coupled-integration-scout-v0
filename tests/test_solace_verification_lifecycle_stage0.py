from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reactive_runtime.actions import parse_action
from reactive_runtime.world import ActionRejected
from tools.solace_verification_lifecycle_stage0 import (
    ALLOWED_ACTIONS,
    CONFIGURATION_ORDER,
    DONOR_REGISTER,
    create_world,
    verification_messages,
)


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "SOLACE_VERIFICATION_LIFECYCLE_PREFLIGHT.json"


class SolaceVerificationLifecycleStage0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))

    def test_preflight_passes_without_provider_calls(self) -> None:
        self.assertTrue(self.preflight["passed"])
        self.assertEqual([], self.preflight["failures"])
        self.assertEqual(0, self.preflight["provider_calls"])
        self.assertFalse(self.preflight["gpu_authorized"])

    def test_exact_donor_and_frozen_register(self) -> None:
        self.assertEqual(
            "82d14bff607d8e323899d09b72739ee4bf14bc067013c6675365b580093ecf5a",
            self.preflight["donor"]["candidate_sha256"],
        )
        self.assertEqual(20, self.preflight["donor"]["register_claims"])
        register = json.loads(DONOR_REGISTER.read_text(encoding="utf-8"))
        self.assertEqual(self.preflight["donor"]["register_sha256"], register["sha256"])

    def test_evaluator_v1_matches_reconciled_donor_adjudication(self) -> None:
        expected = {
            "decision_heading_order",
            "Q02_hydraulics",
            "Q03_sampling",
            "Q04_pumping",
            "Q09_observation",
        }
        for fixture in self.preflight["provider_free_lifecycles"]:
            observed = {row.split(":", 1)[0] for row in fixture["initial_blocking_requirements"]}
            self.assertEqual(expected, observed)
            self.assertNotIn("Q10_environment", observed)

    def test_bounded_patch_transport_and_currentness(self) -> None:
        self.assertEqual(11, self.preflight["patch_transport"]["edit_count"])
        self.assertTrue(self.preflight["patch_transport"]["fits_response_budget"])
        for fixture in self.preflight["provider_free_lifecycles"]:
            self.assertTrue(fixture["prior_check_stale_after_patch"])
            self.assertTrue(fixture["recheck_passed"])
            self.assertEqual([], fixture["recheck_blocking_requirements"])
            self.assertTrue(fixture["submitted"])

    def test_patch_is_exact_anchor_bound_and_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = create_world(Path(temporary))
            before = world.candidate_sha256
            bad = {"action": "patch_decision", "edits": [{"old": "absent anchor", "new": "x"}]}
            parsed = parse_action(json.dumps(bad), ALLOWED_ACTIONS, decision_headings=world.decision_headings)
            with self.assertRaises(ActionRejected):
                world.execute(parsed, result_id="BAD-PATCH")
            self.assertEqual(before, world.candidate_sha256)

    def test_only_a1_receives_register(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            a0_world = create_world(Path(temporary) / "a0")
            a1_world = create_world(Path(temporary) / "a1")
            a0 = verification_messages(CONFIGURATION_ORDER[0], a0_world)
            a1 = verification_messages(CONFIGURATION_ORDER[1], a1_world)
        self.assertEqual(a0, a1[:-1])
        self.assertTrue(a1[-1]["content"].startswith("# Anchored provenance-local source register"))

    def test_budget_is_not_outcome_dependent(self) -> None:
        budget = self.preflight["trajectory_budget"]
        self.assertEqual(12, budget["maximum_actor_calls_per_cell"])
        self.assertEqual(24, budget["maximum_provider_calls"])
        self.assertEqual(1, budget["attempts_per_call"])
        self.assertEqual(0, budget["retries"])

    def test_live_contract_requires_separate_authorization(self) -> None:
        contract = json.loads((ROOT / "SOLACE_VERIFICATION_LIFECYCLE_CONTRACT.json").read_text(encoding="utf-8"))
        request = json.loads((ROOT / "SOLACE_VERIFICATION_LIFECYCLE_AUTHORIZATION_REQUEST.json").read_text(encoding="utf-8"))
        self.assertFalse(contract["gpu_authorized"])
        self.assertFalse(request["gpu_authorized"])
        self.assertEqual(list(CONFIGURATION_ORDER), contract["configuration_order"])


if __name__ == "__main__":
    unittest.main()
