from __future__ import annotations

import json
import unittest
from pathlib import Path

from reactive_runtime.canonical import sha256_file
from reactive_runtime.seal import verify_tree_seal


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "2026-08-25-cedar-ingress-aligned-pressure-screen-v0"


class CedarV0AbortTests(unittest.TestCase):
    def test_zero_call_apparatus_abort_is_exactly_sealed(self) -> None:
        disposition = json.loads(
            (ROOT / "CEDAR_PRESSURE_SCREEN_V0_ABORTED_DISPOSITION.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("sealed_aborted_before_provider_call", disposition["status"])
        self.assertEqual(0, disposition["provider_calls"])
        self.assertEqual(0, disposition["actor_calls"])
        self.assertFalse(disposition["gpu_server_started_by_run"])
        self.assertFalse(disposition["external_process_terminated"])
        self.assertFalse(disposition["same_run_retry_allowed"])
        self.assertEqual(
            disposition["run_seal_sha256"], sha256_file(RUN_ROOT / "RUN_SEAL.json")
        )
        self.assertEqual((), verify_tree_seal(RUN_ROOT, RUN_ROOT / "RUN_SEAL.json"))

    def test_failure_preceded_any_trajectory_or_provider_artifact(self) -> None:
        self.assertFalse((RUN_ROOT / "actor").exists())
        self.assertFalse((RUN_ROOT / "trajectory").exists())
        self.assertFalse((RUN_ROOT / "SCREEN_RESULT.json").exists())
        self.assertFalse((RUN_ROOT / "model" / "server.pid").exists())


if __name__ == "__main__":
    unittest.main()
