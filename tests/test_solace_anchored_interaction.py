from __future__ import annotations

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from tools.offline_tokenizer import OfflineTokenizer
from tools.preflight_solace_anchored_interaction import build
from tools.preflight_solace_anchored_interaction import delta_text
from tools import run_solace_anchored_interaction as measured


ROOT = Path(__file__).resolve().parents[1]


class SolaceAnchoredInteractionTests(unittest.TestCase):
    def test_provider_free_preflight_passes(self) -> None:
        value = build(ROOT, write_output=False)
        self.assertTrue(value["passed"], value["failures"])
        self.assertEqual([], value["failures"])
        self.assertEqual(["RESULT-001"], value["common_pressure"]["selected_result_ids"])
        self.assertEqual(18_595, value["common_pressure"]["relief_prompt_tokens"])
        self.assertTrue(value["maintenance"]["valid_transition_changed"])
        self.assertEqual(
            "zero_valid",
            value["maintenance"]["zero_valid_admission"]["disposition"],
        )
        self.assertFalse(value["maintenance"]["zero_valid_transition_changed"])

    def test_frozen_budget_arithmetic(self) -> None:
        self.assertEqual(34, measured.MAX_ACTOR_CALLS_PER_CELL)
        self.assertEqual(18, measured.MAX_MAINTENANCE_CALLS_L1)
        self.assertEqual(86, measured.MAX_PROVIDER_CALLS)
        self.assertEqual(
            measured.MAX_PROVIDER_CALLS,
            2 * measured.MAX_ACTOR_CALLS_PER_CELL
            + measured.MAX_MAINTENANCE_CALLS_L1,
        )

    def test_no_standalone_expression_gate_is_in_runner(self) -> None:
        text = (ROOT / "tools" / "run_solace_anchored_interaction.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("expression_qualification", text)
        self.assertIn("admit_anchored_delta", text)
        self.assertIn("register.apply", text)
        self.assertIn("external_evaluation", text)

    def test_provider_free_cells_cross_the_complete_system_path(self) -> None:
        class FakeTokenizer:
            def __init__(self) -> None:
                self.offline = OfflineTokenizer()

            def count_messages(self, messages):
                return self.offline.count_messages(messages), json.dumps(messages)

            def tokenize(self, text):
                return list(range(self.offline.count_text(text)))

        offline = OfflineTokenizer()
        versions = {
            row["source_id"]: row["sha256"]
            for row in json.loads(
                (ROOT / "task_solace" / "SOURCE_CATALOG.json").read_text(
                    encoding="utf-8"
                )
            )["sources"]
        }

        def fake_provider(payload, custody, timeout=0):
            messages = payload["messages"]
            prompt = offline.count_messages(messages)
            if payload["response_format"] == {"type": "text"}:
                content = delta_text("RESULT-001", versions, valid=True)
            else:
                content = '{"action":"submit"}'
            completion = offline.count_text(content)
            return {
                "content": content,
                "finish_reason": "stop",
                "usage": {
                    "prompt_tokens": prompt,
                    "completion_tokens": completion,
                    "total_tokens": prompt + completion,
                    "prompt_tokens_details": {"cached_tokens": 0},
                },
            }

        dummy_process = object()
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary)
            patches = (
                patch.object(measured, "verify_runtime_assets", return_value={"passed": True, "failures": []}),
                patch.object(measured, "start_server", return_value=(dummy_process, None, None, {})),
                patch.object(measured, "stop_server", return_value={"released": True}),
                patch.object(measured, "LiveTokenizer", FakeTokenizer),
                patch.object(measured, "complete_custodied", side_effect=fake_provider),
            )
            with patches[0], patches[1], patches[2], patches[3], patches[4]:
                w0 = measured.run_cell("W0_DIRECT_EXACT_WORK_FRESH", run_root)
                l1 = measured.run_cell(
                    "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE", run_root
                )
        self.assertEqual("submission_proposed", w0["terminal_disposition"])
        self.assertEqual(0, w0["maintenance_calls"])
        self.assertEqual("submission_proposed", l1["terminal_disposition"])
        self.assertEqual(1, l1["maintenance_calls"])
        self.assertEqual(1, l1["register_claims"])


if __name__ == "__main__":
    unittest.main()
