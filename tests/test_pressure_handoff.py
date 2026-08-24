from __future__ import annotations

import unittest

from tools.run_pressure_screen import verify_qualification_handoff


class PressureHandoffTests(unittest.TestCase):
    def test_committed_expression_handoff_is_exactly_reconciled(self) -> None:
        handoff = verify_qualification_handoff()
        self.assertTrue(handoff["passed"])
        self.assertEqual(4, handoff["model_calls"])
        self.assertFalse(handoff["measured_actor_authorized"])


if __name__ == "__main__":
    unittest.main()
