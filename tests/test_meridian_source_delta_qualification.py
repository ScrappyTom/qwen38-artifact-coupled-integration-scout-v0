from __future__ import annotations

import json
import unittest
from pathlib import Path

from reactive_runtime.meridian_boundary import verify_meridian_pressure_handoff
from reactive_runtime.meridian_qualification import build_meridian_delta_case
from tools.offline_tokenizer import OfflineTokenizer
from tools import run_meridian_source_delta_qualification as runner


ROOT = Path(__file__).resolve().parents[1]


class MeridianSourceDeltaQualificationTests(unittest.TestCase):
    def test_exact_pressure_handoff_is_bound_and_authorizes_nothing(self) -> None:
        handoff = verify_meridian_pressure_handoff(ROOT)
        self.assertEqual(["RESULT-001"], handoff["positive_relief_result_ids"])
        self.assertEqual("RESULT-006", handoff["pending_result_id"])
        self.assertFalse(handoff["expression_qualification_authorized"])
        self.assertFalse(handoff["measured_fork_authorized"])

    def test_case_is_the_first_actual_externalization_only(self) -> None:
        case = build_meridian_delta_case(ROOT)
        self.assertEqual("Q1_FIRST_ACTUAL_EXTERNALIZATION", case.case_id)
        self.assertEqual(427032, case.seed)
        self.assertEqual(("RESULT-001",), case.input_result_ids)
        self.assertEqual({"AXIOM", "BRAMBLE"}, set(case.allowed_source_versions))
        joined = "\n".join(message["content"] for message in case.messages)
        self.assertIn("## EXACT RESULT RESULT-001", joined)
        self.assertNotIn("## EXACT RESULT RESULT-002", joined)
        self.assertNotIn("## EXACT RESULT RESULT-006", joined)
        self.assertIn("AUTH-000", joined)
        self.assertIn("QUAL-000", joined)

    def test_preflight_matches_exact_case_and_has_large_headroom(self) -> None:
        case = build_meridian_delta_case(ROOT)
        preflight = json.loads(
            (ROOT / "MERIDIAN_SOURCE_DELTA_QUALIFICATION_PREFLIGHT.json").read_text(
                encoding="utf-8"
            )
        )
        contract = json.loads(
            (ROOT / "MERIDIAN_SOURCE_DELTA_QUALIFICATION_CONTRACT.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(4234, OfflineTokenizer().count_messages(case.messages))
        self.assertEqual(4234, preflight["prompt_tokens"])
        self.assertEqual(19054, preflight["headroom_after_completion"])
        self.assertTrue(preflight["fits"])
        self.assertEqual(1, contract["maximum_model_calls"])
        self.assertEqual(["RESULT-001"], contract["case_input_result_ids"])
        self.assertEqual(["AXIOM", "BRAMBLE"], contract["case_source_ids"])
        self.assertFalse(contract["measured_continuation_authorized"])
        self.assertFalse(contract["gpu_authorized"])

    def test_runner_and_authorization_request_are_frozen_and_inert(self) -> None:
        request = json.loads(
            (ROOT / "MERIDIAN_SOURCE_DELTA_AUTHORIZATION_REQUEST.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(runner.RUN_ID, request["run_id"])
        self.assertEqual(runner.SCOPE, request["scope"])
        self.assertEqual(runner.MAX_CALLS, request["maximum_model_calls"])
        self.assertFalse(request["authorized"])
        self.assertFalse(
            (ROOT / "qualification_runs" / runner.RUN_ID).exists()
        )
        source = Path(runner.__file__).read_text(encoding="utf-8")
        self.assertIn("validate_source_delta", source)
        self.assertIn('"pending_offline"', source)
        self.assertIn('"measured_continuation_authorized": False', source)


if __name__ == "__main__":
    unittest.main()
