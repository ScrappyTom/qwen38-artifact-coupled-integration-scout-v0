from __future__ import annotations

import unittest

from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger, ResultRecord


def record(result_id: str, exact: str, ordinal: int, index: int) -> ResultRecord:
    return ResultRecord(
        result_id=result_id,
        result_kind="source_observation",
        object_id=f"source:{result_id}",
        object_version="a" * 64,
        exact_content=exact,
        acquired_call=ordinal,
        candidate_sha256_after="b" * 64,
        first_model_visible_call=ordinal,
        message_index=index,
        resident=True,
        metadata={"source_id": "S01", "source_path": "sources/S01.md", "source_sha256": "c" * 64, "source_size_bytes": len(exact), "start_line": 1, "end_line": 1},
    )


def count(messages: list[dict[str, str]]) -> int:
    return sum(len(row["content"]) for row in messages)


class PositiveReliefTests(unittest.TestCase):
    def test_non_positive_receipt_is_skipped_for_later_positive_candidate(self) -> None:
        messages = [{"role": "system", "content": "x"}, {"role": "user", "content": "z"}, {"role": "user", "content": "Q" * 4000}]
        ledger = ResultLedger()
        first = record("RESULT-001", "z", 1, 1)
        second = record("RESULT-002", "Q" * 4000, 2, 2)
        ledger.add(first)
        ledger.add(second)
        outcome = positive_savings_first_fit_step(messages=messages, ledger=ledger, prompt_limit=100, count_messages=count)
        self.assertEqual(("RESULT-002",), outcome.selected_result_ids)
        self.assertEqual("non_positive_savings", outcome.audits[0].reason)
        self.assertTrue(first.resident)
        self.assertFalse(second.resident)

    def test_no_positive_candidate_preserves_messages_and_residency(self) -> None:
        messages = [{"role": "user", "content": "z"}]
        ledger = ResultLedger()
        item = record("RESULT-001", "z", 1, 0)
        ledger.add(item)
        outcome = positive_savings_first_fit_step(messages=messages, ledger=ledger, prompt_limit=0, count_messages=count)
        self.assertFalse(outcome.feasible)
        self.assertEqual((), outcome.selected_result_ids)
        self.assertEqual("z", messages[0]["content"])
        self.assertTrue(item.resident)

    def test_pending_result_is_protected(self) -> None:
        messages = [{"role": "user", "content": "A" * 3000}, {"role": "user", "content": "B" * 3000}]
        ledger = ResultLedger()
        a = record("RESULT-001", messages[0]["content"], 1, 0)
        b = record("RESULT-002", messages[1]["content"], 2, 1)
        ledger.add(a)
        ledger.add(b)
        outcome = positive_savings_first_fit_step(messages=messages, ledger=ledger, prompt_limit=100, count_messages=count, protected_result_ids=("RESULT-001",))
        self.assertEqual(("RESULT-002",), outcome.selected_result_ids)
        self.assertTrue(a.resident)


if __name__ == "__main__":
    unittest.main()
