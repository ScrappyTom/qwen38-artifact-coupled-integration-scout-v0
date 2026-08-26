from __future__ import annotations

import json
import unittest
from pathlib import Path

from reactive_runtime.aster_boundary import verify_aster_pressure_handoff
from reactive_runtime.aster_qualification import build_aster_relational_case
from reactive_runtime.canonical import canonical_json_text, sha256_bytes, sha256_file
from tools import run_aster_relational_expression_qualification as runner
from tools.offline_tokenizer import OfflineTokenizer


ROOT = Path(__file__).resolve().parents[1]


class AsterRelationalExpressionFreezeTests(unittest.TestCase):
    def test_pressure_handoff_is_exact_and_authorizes_no_successor(self) -> None:
        handoff = verify_aster_pressure_handoff(ROOT)
        self.assertEqual(
            "2026-08-25-aster-provenance-relational-pressure-screen-v0",
            handoff["run_id"],
        )
        self.assertEqual(["RESULT-001"], handoff["externalized_source_result_ids"])
        self.assertEqual("RESULT-006", handoff["pending_result_id"])
        self.assertFalse(handoff["expression_qualification_authorized"])
        self.assertFalse(handoff["measured_fork_authorized"])

    def test_case_uses_only_first_actual_source_externalization(self) -> None:
        case = build_aster_relational_case(ROOT)
        self.assertEqual("Q1_FIRST_ACTUAL_SOURCE_EXTERNALIZATION", case.case_id)
        self.assertEqual(531702, case.seed)
        self.assertEqual(("RESULT-001",), case.input_result_ids)
        self.assertEqual(("ANCHOR", "BRIDGE"), case.input_source_ids)
        self.assertEqual(1, len(case.records))
        self.assertTrue(case.records[0].previously_visible)
        joined = "\n".join(message["content"] for message in case.messages)
        self.assertIn("--- NEWLY EXTERNALIZED RESULT-001 ---", joined)
        self.assertIn('"source_id":"ANCHOR"', joined)
        self.assertIn('"source_id":"BRIDGE"', joined)
        self.assertNotIn("RESULT-002", joined)
        self.assertNotIn("RESULT-006", joined)
        self.assertIn("source-reported relationship", joined)
        self.assertIn("does not assert their authoritative current state", joined)

    def test_preflight_reproduces_exact_case_and_fits(self) -> None:
        case = build_aster_relational_case(ROOT)
        preflight_path = ROOT / "ASTER_RELATIONAL_EXPRESSION_PREFLIGHT.json"
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
        self.assertEqual(4428, OfflineTokenizer().count_messages(case.messages))
        self.assertEqual(4428, preflight["prompt_tokens"])
        self.assertEqual(1800, preflight["provider_max_completion_tokens"])
        self.assertEqual(18860, preflight["headroom_after_completion"])
        self.assertTrue(preflight["fits"])
        self.assertEqual(
            sha256_bytes(canonical_json_text(case.messages).encode("utf-8")),
            preflight["message_sha256"],
        )
        self.assertEqual(
            sha256_file(ROOT / "ASTER_PRESSURE_BOUNDARY_HANDOFF.json"),
            preflight["pressure_handoff_sha256"],
        )
        self.assertEqual(0, preflight["model_calls"])
        self.assertFalse(preflight["gpu_authorized"])
        self.assertFalse(preflight["measured_continuation_authorized"])

    def test_contract_request_and_runner_freeze_one_call_only(self) -> None:
        contract = json.loads(
            (
                ROOT / "ASTER_RELATIONAL_EXPRESSION_QUALIFICATION_CONTRACT.json"
            ).read_text(encoding="utf-8")
        )
        request = json.loads(
            (ROOT / "ASTER_RELATIONAL_EXPRESSION_AUTHORIZATION_REQUEST.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(runner.RUN_ID, contract["run_id"])
        self.assertEqual(runner.SCOPE, contract["scope"])
        self.assertEqual(runner.MAX_CALLS, contract["maximum_model_calls"])
        self.assertEqual(runner.RUN_ID, request["requested_run_id"])
        self.assertEqual(runner.SCOPE, request["requested_scope"])
        self.assertEqual(runner.MAX_CALLS, request["requested_maximum_model_calls"])
        self.assertEqual(1, runner.MAX_CALLS)
        self.assertFalse(contract["gpu_authorized"])
        self.assertFalse(contract["measured_continuation_authorized"])
        self.assertFalse(request["authorized"])
        self.assertFalse(request["measured_continuation_included"])
        self.assertFalse((ROOT / "qualification_runs" / runner.RUN_ID).exists())

    def test_safety_contract_is_source_bound_and_non_authorizing(self) -> None:
        safety = json.loads(
            (ROOT / "ASTER_RELATIONAL_EXPRESSION_SAFETY_CONTRACT.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(["RESULT-001"], safety["input_result_ids"])
        self.assertEqual(["ANCHOR", "BRIDGE"], safety["input_source_ids"])
        self.assertEqual(8, len(safety["noncontradiction_criteria"]))
        self.assertEqual(
            {"ANCHOR", "BRIDGE"},
            {row["source_id"] for row in safety["noncontradiction_criteria"]},
        )
        self.assertIn("closure authorization", safety["automatic_failures"])
        self.assertIn("not repaired", safety["omission_rule"])


if __name__ == "__main__":
    unittest.main()
