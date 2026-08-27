from __future__ import annotations

import unittest

from tools.audit_orchard_stage0 import verify


class AuditOrchardStage0Tests(unittest.TestCase):
    def test_audit_passes(self) -> None:
        result = verify()
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual(0, result["provider_calls"])
        self.assertFalse(result["gpu_authorized"])
        self.assertEqual(13, result["source_count"])
        self.assertEqual(4, result["relationship_red_team_cases"])


if __name__ == "__main__":
    unittest.main()
