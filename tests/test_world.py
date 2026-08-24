from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reactive_runtime.actions import DECISION_HEADINGS
from reactive_runtime.integration import IntegrationArtifact
from reactive_runtime.world import ArchitectureWorld


ROOT = Path(__file__).resolve().parents[1]


class WorldTests(unittest.TestCase):
    def test_detached_and_coupled_maintenance_have_different_exact_effects(self) -> None:
        artifact = IntegrationArtifact(1, "# Evidence Integration Ledger\n\nR01 [S02].\n", 8, ("RESULT-001",), ("S02",))
        with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
            detached = ArchitectureWorld(ROOT / "task", Path(left))
            coupled = ArchitectureWorld(ROOT / "task", Path(right))
            detached_before = detached.candidate_sha256
            coupled_before = coupled.candidate_sha256
            d_effect = detached.apply_integration("D0_DETACHED", artifact)
            a_effect = coupled.apply_integration("A1_COUPLED", artifact)
            self.assertEqual(detached_before, detached.candidate_sha256)
            self.assertEqual("semantic_state_effect", d_effect.result_kind)
            self.assertNotEqual(coupled_before, coupled.candidate_sha256)
            self.assertEqual("candidate_effect", a_effect.result_kind)
            self.assertEqual(artifact.body, (coupled.candidate_root / "EVIDENCE_INTEGRATION_LEDGER.md").read_text(encoding="utf-8"))

    def test_check_currency_tracks_incremental_section_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = ArchitectureWorld(ROOT / "task", Path(temporary))
            checked = world.execute({"action": "run_check"}, result_id="RESULT-CHECK")
            self.assertEqual(world.candidate_sha256, checked.evaluated_candidate_sha256)
            world.execute({"action": "upsert_decision_section", "heading": DECISION_HEADINGS[0], "body": "Scoped evidence [S02]."}, result_id="RESULT-EFFECT")
            self.assertEqual("stale", world.current_check_binding()["currency"])
            current = world.execute({"action": "run_check"}, result_id="RESULT-RECHECK")
            self.assertEqual(world.candidate_sha256, current.evaluated_candidate_sha256)
            self.assertEqual("current", world.current_check_binding()["currency"])

    def test_incremental_sections_render_in_task_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = ArchitectureWorld(ROOT / "task", Path(temporary))
            world.execute({"action": "upsert_decision_section", "heading": DECISION_HEADINGS[3], "body": "Fourth."}, result_id="R1")
            world.execute({"action": "upsert_decision_section", "heading": DECISION_HEADINGS[0], "body": "First."}, result_id="R2")
            text = (world.candidate_root / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md").read_text(encoding="utf-8")
            self.assertLess(text.index(DECISION_HEADINGS[0]), text.index(DECISION_HEADINGS[3]))


if __name__ == "__main__":
    unittest.main()
