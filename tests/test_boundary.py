from __future__ import annotations

import json
import unittest
from pathlib import Path

from reactive_runtime.boundary import verify_pressure_handoff


ROOT = Path(__file__).resolve().parents[1]


class BoundaryTests(unittest.TestCase):
    def test_live_handoff_is_exactly_qualified(self) -> None:
        handoff = json.loads(
            (ROOT / "CEDAR_PRESSURE_BOUNDARY_HANDOFF.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("passed_authentic_pressure_boundary", handoff["status"])
        self.assertTrue(handoff["pressure_qualified"])
        self.assertTrue(handoff["interaction_trigger_qualified"])
        self.assertEqual(5, handoff["actor_calls"])
        self.assertEqual(8, len(handoff["activation_snapshot"]["qualifying_sources"]))
        self.assertEqual(6, len(handoff["activation_snapshot"]["qualifying_domains"]))
        self.assertEqual(2384, handoff["overflow_tokens"])
        self.assertEqual(19881, handoff["positive_relief_after_tokens"])
        audited = verify_pressure_handoff(ROOT)
        self.assertEqual("RESULT-005", audited["pending_result_id"])


if __name__ == "__main__":
    unittest.main()
