from __future__ import annotations

import unittest

from tools.dry_run_measured_interaction import run_fixture


class MeasuredFixtureTests(unittest.TestCase):
    def test_authentic_boundary_full_loop_runs_without_provider(self) -> None:
        result = run_fixture()
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual(2, len(result["cells"]))
        self.assertTrue(result["offline_provider_only"])
        self.assertFalse(result["gpu_authorized"])


if __name__ == "__main__":
    unittest.main()
