from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools import run_maintenance_qualification as runner


ROOT = Path(__file__).resolve().parents[1]


class MaintenanceQualificationContractTests(unittest.TestCase):
    def test_optional_live_expression_contract_is_not_authorized(self) -> None:
        contract = json.loads(
            (ROOT / "MAINTENANCE_QUALIFICATION_CONTRACT.json").read_text(
                encoding="utf-8"
            )
        )
        request = json.loads(
            (ROOT / "AUTHORIZATION_REQUEST.json").read_text(encoding="utf-8")
        )
        self.assertEqual(runner.RUN_ID, contract["run_id"])
        self.assertEqual(runner.SCOPE, request["scope"])
        self.assertEqual(4, contract["maximum_model_calls"])
        self.assertFalse(request["authorized"])


if __name__ == "__main__":
    unittest.main()
