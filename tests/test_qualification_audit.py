from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_maintenance_qualification",
    ROOT / "tools" / "audit_maintenance_qualification.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class MaintenanceQualificationAuditTests(unittest.TestCase):
    def test_sealed_run_passes_independent_audit(self) -> None:
        result = MODULE.audit(ROOT)
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual(4, result["model_calls"])
        self.assertEqual(4, result["provider_attempts"])
        self.assertEqual(0, result["retries"])
        self.assertFalse(result["measured_actor_authorized"])


if __name__ == "__main__":
    unittest.main()
