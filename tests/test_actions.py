from __future__ import annotations

import json
import unittest

from reactive_runtime.actions import DECISION_HEADINGS, action_json_schema, parse_action
from reactive_runtime.configuration import (
    causal_verification_actor_actions,
    ordinary_actions,
)


class ActionTests(unittest.TestCase):
    def test_all_common_actions_have_schema(self) -> None:
        schema = action_json_schema(
            ordinary_actions(),
            source_ids=("S01", "S02"),
            reopen_result_ids=("RESULT-001",),
        )
        self.assertEqual(
            len(ordinary_actions()), len(schema["json_schema"]["schema"]["oneOf"])
        )

    def test_reopen_is_not_advertised_without_an_external_result(self) -> None:
        schema = action_json_schema(
            ordinary_actions(), source_ids=("S01",), reopen_result_ids=()
        )
        actions = [
            row["properties"]["action"]["const"]
            for row in schema["json_schema"]["schema"]["oneOf"]
        ]
        self.assertNotIn("reopen_exact", actions)

    def test_incremental_section_action_is_exact(self) -> None:
        value = {
            "action": "upsert_decision_section",
            "heading": DECISION_HEADINGS[0],
            "body": "Grounded body [S01].",
        }
        self.assertEqual(value, parse_action(json.dumps(value), ordinary_actions()))
        value["heading"] = "Invented"
        with self.assertRaises(ValueError):
            parse_action(json.dumps(value), ordinary_actions())

    def test_batch_overlap_is_rejected(self) -> None:
        value = {
            "action": "read_batch",
            "requests": [
                {"source_id": "S01", "start_line": 1, "end_line": 20},
                {"source_id": "S01", "start_line": 10, "end_line": 30},
            ],
        }
        with self.assertRaises(ValueError):
            parse_action(json.dumps(value), ordinary_actions())

    def test_bound_section_repair_is_closed_and_hash_bound(self) -> None:
        allowed = causal_verification_actor_actions(
            "V1_BOUNDED_CAUSAL_CONTINUITY", phase="verification"
        )
        value = {
            "action": "replace_artifact_section",
            "candidate_sha256": "1" * 64,
            "artifact_sha256": "2" * 64,
            "section_heading": DECISION_HEADINGS[0],
            "expected_section_sha256": "3" * 64,
            "replacement_section": f"## {DECISION_HEADINGS[0]}\n\nReplacement.\n",
        }
        self.assertEqual(value, parse_action(json.dumps(value), allowed))
        schema = action_json_schema(allowed, source_ids=("S01",), reopen_result_ids=())
        branch = next(
            row
            for row in schema["json_schema"]["schema"]["oneOf"]
            if row["properties"]["action"]["const"] == "replace_artifact_section"
        )
        self.assertEqual(
            "^[0-9a-f]{64}$", branch["properties"]["candidate_sha256"]["pattern"]
        )
        value["candidate_sha256"] = "not-a-hash"
        with self.assertRaises(ValueError):
            parse_action(json.dumps(value), allowed)


if __name__ == "__main__":
    unittest.main()
