from __future__ import annotations

import json
import unittest
from pathlib import Path

from reactive_runtime.boundary import verify_pressure_handoff


ROOT = Path(__file__).resolve().parents[1]


class BoundaryTests(unittest.TestCase):
    def test_placeholder_cannot_be_hydrated_as_authentic_evidence(self) -> None:
        handoff = json.loads(
            (ROOT / "NORTHSTAR_PRESSURE_BOUNDARY_HANDOFF.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("pending_live_screen", handoff["status"])
        self.assertFalse(handoff["pressure_qualified"])
        with self.assertRaises(RuntimeError):
            verify_pressure_handoff(ROOT)


if __name__ == "__main__":
    unittest.main()
