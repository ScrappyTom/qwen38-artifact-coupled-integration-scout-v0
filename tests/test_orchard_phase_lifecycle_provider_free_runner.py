from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reactive_runtime.canonical import canonical_json_text
from reactive_runtime.tokenizer import render_qwen_messages
from tools import run_orchard_phase_lifecycle as runner
from tools.offline_tokenizer import OfflineTokenizer
from tools.orchard_stage0 import fixture_decision, fixture_delta, fixture_ledger, repair_action


class FakeLiveTokenizer:
    def __init__(self) -> None:
        self.offline = OfflineTokenizer()

    def tokenize(self, content: str) -> list[int]:
        return list(range(self.offline.count_text(content)))

    def count_messages(self, messages: list[dict[str, str]]) -> tuple[int, str]:
        rendered = render_qwen_messages(messages)
        return self.offline.count_text(rendered), rendered


class OrchardPhaseLifecycleProviderFreeRunnerTests(unittest.TestCase):
    def test_both_live_control_paths_reach_recheck_and_submission(self) -> None:
        actor_outputs = [
            canonical_json_text(
                {"action": "replace_evidence_ledger", "content": fixture_ledger()}
            ),
            canonical_json_text(
                {"action": "replace_decision", "content": fixture_decision(defective=True)}
            ),
            canonical_json_text({"action": "begin_verification"}),
            canonical_json_text({"action": "run_check"}),
            canonical_json_text(repair_action()),
            canonical_json_text({"action": "run_check"}),
            canonical_json_text({"action": "submit"}),
        ]
        tokenizer = FakeLiveTokenizer()

        def fake_verify() -> dict[str, object]:
            return {"passed": True, "failures": []}

        def fake_start(_root: Path):
            return object(), None, None, {}

        def fake_stop(_process, _stdout, _stderr, _root: Path):
            return {"released": True}

        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            maintenance_output = fixture_delta(
                runner.OrchardWorld(runner.TASK, temporary_root / "maintenance-world"),
                "RESULT-001",
                ("CHARTER", "CULTURE"),
            )
            run_root = temporary_root / "run"
            run_root.mkdir()
            results = []
            for configuration_id in runner.CONFIGURATION_ORDER:
                queue = list(actor_outputs)

                def fake_complete(payload, custody_root: Path, *, timeout: int):
                    if "maintenance" in custody_root.parts:
                        content = maintenance_output
                    else:
                        content = queue.pop(0)
                    prompt = tokenizer.count_messages(payload["messages"])[0]
                    completion = tokenizer.offline.count_text(content)
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

                with (
                    patch.object(runner, "verify_runtime_assets", fake_verify),
                    patch.object(runner, "start_server", fake_start),
                    patch.object(runner, "stop_server", fake_stop),
                    patch.object(runner, "LiveTokenizer", lambda: tokenizer),
                    patch.object(runner, "complete_custodied", fake_complete),
                ):
                    results.append(runner.run_cell(configuration_id, run_root))

        self.assertEqual(2, len(results))
        self.assertTrue(all(result["candidate_submitted"] for result in results))
        self.assertTrue(all(result["phase"] == "verification" for result in results))
        self.assertTrue(
            all(result["current_check_binding"]["currency"] == "current" for result in results)
        )
        self.assertTrue(all(result["external_evaluation"]["projection"]["passed"] for result in results))
        self.assertTrue(results[0]["register_retained_in_verification"])
        self.assertFalse(results[1]["register_retained_in_verification"])


if __name__ == "__main__":
    unittest.main()
