from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools import run_measured_interaction as measured


ROOT = Path(__file__).resolve().parents[1]


class MeasuredContractTests(unittest.TestCase):
    def test_frozen_contract_matches_runner_limits(self) -> None:
        contract = json.loads(
            (ROOT / "MEASURED_INTERACTION_CONTRACT.json").read_text(encoding="utf-8")
        )
        self.assertEqual(measured.RUN_ID, contract["run_id"])
        self.assertEqual(list(measured.CONFIGURATION_ORDER), contract["configuration_order"])
        self.assertEqual(
            measured.MAX_ACTOR_CALLS_PER_CELL,
            contract["maximum_actor_calls_per_configuration"],
        )
        self.assertEqual(
            measured.MAX_MAINTENANCE_CALLS_PER_CELL,
            contract["maximum_maintenance_calls_per_configuration"],
        )
        self.assertEqual(measured.MAX_PROVIDER_CALLS, contract["maximum_provider_calls"])
        self.assertEqual(1, contract["attempts_per_call"])
        self.assertEqual(0, contract["retries"])

    def test_authorization_request_does_not_authorize(self) -> None:
        request = json.loads(
            (ROOT / "MEASURED_AUTHORIZATION_REQUEST.json").read_text(encoding="utf-8")
        )
        self.assertFalse(request["authorized"])
        self.assertEqual(measured.SCOPE, request["scope"])
        self.assertEqual(measured.MAX_PROVIDER_CALLS, request["maximum_provider_calls"])


if __name__ == "__main__":
    unittest.main()
