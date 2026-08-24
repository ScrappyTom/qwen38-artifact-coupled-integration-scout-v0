from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_pressure_screen",
    ROOT / "tools" / "audit_pressure_screen.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PressureScreenAuditTests(unittest.TestCase):
    def test_sealed_pressure_boundary_passes_independent_audit(self) -> None:
        result = MODULE.audit(ROOT)
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual(8, result["actor_calls"])
        self.assertEqual(967, result["overflow_tokens"])
        self.assertFalse(result["pending_result_delivered"])
        self.assertFalse(result["measured_fork_authorized"])


if __name__ == "__main__":
    unittest.main()
