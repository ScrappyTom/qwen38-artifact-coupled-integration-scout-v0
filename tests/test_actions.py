from __future__ import annotations

import json
import unittest

from reactive_runtime.actions import DECISION_HEADINGS, action_json_schema, parse_action
from reactive_runtime.configuration import ordinary_actions


class ActionTests(unittest.TestCase):
    def test_all_common_actions_have_schema(self) -> None:
        schema = action_json_schema(
            ordinary_actions(), source_ids=("S01", "S02"), reopen_result_ids=("RESULT-001",)
        )
        self.assertEqual(len(ordinary_actions()), len(schema["json_schema"]["schema"]["oneOf"]))

    def test_reopen_is_not_advertised_without_an_external_result(self) -> None:
        schema = action_json_schema(ordinary_actions(), source_ids=("S01",), reopen_result_ids=())
        actions = [row["properties"]["action"]["const"] for row in schema["json_schema"]["schema"]["oneOf"]]
        self.assertNotIn("reopen_exact", actions)

    def test_incremental_section_action_is_exact(self) -> None:
        value = {"action": "upsert_decision_section", "heading": DECISION_HEADINGS[0], "body": "Grounded body [S01]."}
        self.assertEqual(value, parse_action(json.dumps(value), ordinary_actions()))
        value["heading"] = "Invented"
        with self.assertRaises(ValueError):
            parse_action(json.dumps(value), ordinary_actions())

    def test_batch_overlap_is_rejected(self) -> None:
        value = {"action": "read_batch", "requests": [{"source_id": "S01", "start_line": 1, "end_line": 20}, {"source_id": "S01", "start_line": 10, "end_line": 30}]}
        with self.assertRaises(ValueError):
            parse_action(json.dumps(value), ordinary_actions())


if __name__ == "__main__":
    unittest.main()
