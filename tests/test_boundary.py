from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reactive_runtime.boundary import hydrate_pressure_boundary, verify_pressure_handoff
from reactive_runtime.world import ArchitectureWorld


ROOT = Path(__file__).resolve().parents[1]


class BoundaryTests(unittest.TestCase):
    def test_exact_pressure_handoff_verifies(self) -> None:
        handoff = verify_pressure_handoff(ROOT)
        self.assertTrue(handoff["pressure_qualified"])
        self.assertFalse(handoff["measured_fork_authorized"])

    def test_boundary_hydrates_exact_world_and_pending_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = ArchitectureWorld(ROOT / "task", Path(temporary))
            boundary = hydrate_pressure_boundary(repository_root=ROOT, world=world)
        self.assertEqual("RESULT-008", boundary.pending_result_id)
        self.assertEqual(8, boundary.actor_calls_completed)
        self.assertEqual(9, boundary.next_result_ordinal)
        self.assertEqual(21_959, boundary.prospective_prompt_tokens)
        self.assertIsNone(boundary.ledger.get("RESULT-008").first_model_visible_call)


if __name__ == "__main__":
    unittest.main()
