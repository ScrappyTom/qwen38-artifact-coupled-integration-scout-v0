from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools import run_pressure_screen as runner


ROOT = Path(__file__).resolve().parents[1]


class PressureHandoffTests(unittest.TestCase):
    def test_screen_is_frozen_but_not_predeclared_as_authentic(self) -> None:
        contract = json.loads(
            (ROOT / "PRESSURE_SCREEN_CONTRACT.json").read_text(encoding="utf-8")
        )
        self.assertEqual("frozen_offline_gpu_withheld", contract["status"])
        self.assertEqual(runner.RUN_ID, contract["run_id"])
        self.assertIn("four qualifying source IDs", contract["qualifying_endpoint"])
        self.assertEqual(
            "union of exact source lines delivered across prior actor decision boundaries",
            contract["activation_semantics"]["unit"],
        )
        self.assertIn(
            "result object count", contract["activation_semantics"]["explicit_non_units"]
        )

    def test_authorization_placeholder_does_not_authorize(self) -> None:
        request = json.loads(
            (ROOT / "PRESSURE_SCREEN_AUTHORIZATION_REQUEST.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(request["authorized"])
        self.assertEqual(runner.SCOPE, request["scope"])
        self.assertEqual(runner.MAX_CALLS, request["maximum_model_calls"])


if __name__ == "__main__":
    unittest.main()
