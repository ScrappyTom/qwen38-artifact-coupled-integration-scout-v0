from __future__ import annotations

import unittest

from reactive_runtime.integration import next_artifact, validate_integration
from reactive_runtime.records import ResultRecord


def source_record() -> ResultRecord:
    return ResultRecord(
        result_id="RESULT-001", result_kind="source_observation", object_id="batch:S02+S03", object_version="a" * 64,
        exact_content="exact", acquired_call=1, candidate_sha256_after="b" * 64,
        metadata={"source_ids": ["S02", "S03"], "segments": []},
    )


class IntegrationTests(unittest.TestCase):
    def test_allowlist_and_closure_guard(self) -> None:
        accepted = "# Evidence Integration Ledger\n\nR01 is supported by [S02] and [S03]."
        result = validate_integration(accepted, count_text=lambda value: len(value.split()), allowed_source_ids=("S02", "S03"))
        self.assertTrue(result.valid)
        forbidden = validate_integration(accepted + " Submit now. [S14]", count_text=lambda value: len(value.split()), allowed_source_ids=("S02", "S03"))
        self.assertFalse(forbidden.valid)
        self.assertIn("unobserved_source_reference", forbidden.issues)
        self.assertIn("closure_authorization_forbidden", forbidden.issues)

    def test_replacement_tracks_exact_inputs_without_append_semantics(self) -> None:
        first = next_artifact(prior=None, body="# Evidence Integration Ledger\n\nR01 [S02].", body_tokens=7, result=source_record())
        second_record = source_record()
        second_record.result_id = "RESULT-002"
        second_record.metadata = {"source_ids": ["S04"], "segments": []}
        second = next_artifact(prior=first, body="# Evidence Integration Ledger\n\nR02 [S04].", body_tokens=7, result=second_record)
        self.assertEqual(2, second.version)
        self.assertEqual(("RESULT-001", "RESULT-002"), second.input_result_ids)
        self.assertNotIn("R01", second.body)


if __name__ == "__main__":
    unittest.main()
