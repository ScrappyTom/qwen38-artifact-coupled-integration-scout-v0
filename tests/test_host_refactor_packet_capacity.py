from __future__ import annotations

import unittest

from host_refactor.capacity import CapacityManager
from host_refactor.kernel import HostKernel
from host_refactor.model import (
    DeliveryState,
    ExactResult,
    ExactStateObject,
    TranscriptEntry,
)
from host_refactor.packet import PacketComposer


def count_chars(messages: list[dict[str, str]]) -> int:
    return sum(len(row["content"]) for row in messages)


def make_result(
    result_id: str,
    *,
    payload: str,
    span: str = "SOURCE-A:1-20",
    version: str = "v1",
) -> ExactResult:
    return ExactResult(
        result_id=result_id,
        result_kind="source_observation",
        object_id=span,
        object_version=version,
        exact_content=f"wrapper {result_id}\n--- exact result body ---\n{payload}",
        payload_content=payload,
        acquired_call=1,
        candidate_sha256_after="candidate-0",
        span_key=span,
    )


def delivered_kernel(result: ExactResult) -> HostKernel:
    kernel = HostKernel().append_transcript(TranscriptEntry("SYSTEM", "system", "s"))
    kernel = kernel.complete_invocation(
        call_index=1,
        included_result_ids=(),
        request_sha256="r1",
        response_sha256="a1",
    )
    kernel = kernel.append_transcript(TranscriptEntry("A1", "assistant", "read"))
    kernel = kernel.acquire(result).schedule(
        result.result_id,
        call_index=2,
        transcript_entry_id="R1",
    )
    return kernel.complete_invocation(
        call_index=2,
        included_result_ids=(result.result_id,),
        request_sha256="r2",
        response_sha256="a2",
    )


class PacketAndCapacityTests(unittest.TestCase):
    def test_current_candidate_slot_and_check_currency_are_mechanical(self) -> None:
        candidate_one = ExactStateObject(
            "current_candidate",
            "candidate:task",
            "v1",
            "candidate one",
            {"candidate_sha256": "c1"},
        )
        kernel = (
            HostKernel()
            .set_state_object(candidate_one)
            .append_transcript(
                TranscriptEntry(
                    "CANDIDATE",
                    "user",
                    candidate_one.exact_content,
                    state_slot_id="current_candidate",
                )
            )
        )
        kernel = kernel.complete_invocation(
            call_index=1,
            included_result_ids=(),
            request_sha256="r1",
            response_sha256="a1",
        )
        check = ExactResult(
            result_id="CHECK-001",
            result_kind="check_observation",
            object_id="check:task",
            object_version="check-v1",
            exact_content="check passed",
            payload_content="check passed",
            acquired_call=1,
            candidate_sha256_after="c1",
            relief_eligible=False,
            evaluated_candidate_sha256="c1",
        )
        kernel = kernel.acquire(check).schedule(
            "CHECK-001", call_index=2, transcript_entry_id="CHECK"
        )
        kernel = kernel.complete_invocation(
            call_index=2,
            included_result_ids=("CHECK-001",),
            request_sha256="r2",
            response_sha256="a2",
        )
        current = "\n".join(
            row["content"] for row in PacketComposer().compose(kernel).messages
        )
        self.assertIn('"currency":"current"', current)
        candidate_two = ExactStateObject(
            "current_candidate",
            "candidate:task",
            "v2",
            "candidate two",
            {"candidate_sha256": "c2"},
        )
        kernel = kernel.set_state_object(candidate_two)
        stale = "\n".join(
            row["content"] for row in PacketComposer().compose(kernel).messages
        )
        self.assertIn("candidate two", stale)
        self.assertNotIn("candidate one", stale)
        self.assertIn('"currency":"stale"', stale)

    def test_repeat_resident_request_keeps_one_exact_body(self) -> None:
        first = make_result("RESULT-001", payload="alpha" * 100)
        repeated = make_result("RESULT-002", payload="alpha" * 100)
        kernel = delivered_kernel(first)
        kernel = kernel.record_repeat_demand(
            requested_result=repeated,
            resident_result_id="RESULT-001",
            feedback_entry_id="REPEAT-001",
        )
        packet = PacketComposer().compose(kernel)
        contents = "\n".join(row["content"] for row in packet.messages)
        self.assertEqual(contents.count(first.exact_content), 1)
        self.assertIn('"status":"already_resident"', contents)
        self.assertEqual(kernel.project().results["RESULT-001"].demand_count, 2)
        self.assertNotIn("RESULT-002", kernel.project().results)

    def test_externalize_and_reopen_restores_body_only_at_new_entry(self) -> None:
        first = make_result("RESULT-001", payload="alpha" * 100)
        kernel = delivered_kernel(first).externalize("RESULT-001", reason="pressure")
        external_packet = PacketComposer().compose(kernel)
        self.assertNotIn(
            first.exact_content, [row["content"] for row in external_packet.messages]
        )
        kernel = kernel.request_reopen(
            "RESULT-001",
            call_index=3,
            transcript_entry_id="REOPEN-001",
        )
        pending_packet = PacketComposer().compose(kernel)
        self.assertEqual(
            [row["content"] for row in pending_packet.messages].count(
                first.exact_content
            ),
            1,
        )
        kernel = kernel.complete_invocation(
            call_index=3,
            included_result_ids=("RESULT-001",),
            request_sha256="r3",
            response_sha256="a3",
        )
        resident_packet = PacketComposer().compose(kernel)
        self.assertEqual(
            [row["content"] for row in resident_packet.messages].count(
                first.exact_content
            ),
            1,
        )
        self.assertEqual(kernel.project().results["RESULT-001"].reopen_count, 1)

    def test_partial_overlap_and_different_version_are_not_deduplicated(self) -> None:
        first = make_result("RESULT-001", payload="alpha", span="SOURCE-A:1-20")
        overlap = make_result("RESULT-002", payload="alpha", span="SOURCE-A:10-30")
        versioned = make_result(
            "RESULT-003", payload="alpha", span="SOURCE-A:1-20", version="v2"
        )
        self.assertNotEqual(first.body_identity, overlap.body_identity)
        self.assertNotEqual(first.body_identity, versioned.body_identity)

    def test_relief_is_first_positive_and_stops_at_feasibility(self) -> None:
        first = make_result("RESULT-001", payload="a" * 2_000)
        second = make_result("RESULT-002", payload="b" * 2_000, span="SOURCE-B:1-20")
        kernel = delivered_kernel(first)
        kernel = kernel.append_transcript(
            TranscriptEntry("A2", "assistant", "read second")
        )
        kernel = kernel.acquire(second).schedule(
            "RESULT-002", call_index=3, transcript_entry_id="R2"
        )
        kernel = kernel.complete_invocation(
            call_index=3,
            included_result_ids=("RESULT-002",),
            request_sha256="r3",
            response_sha256="a3",
        )
        composer = PacketComposer()
        before = count_chars(composer.compose(kernel).message_list())
        manager = CapacityManager(
            composer=composer,
            count_messages=count_chars,
            prompt_limit=before - 1_000,
        )
        outcome = manager.ensure_feasible(kernel)
        self.assertTrue(outcome.feasible)
        self.assertEqual(outcome.selected_result_ids, ("RESULT-001",))
        self.assertEqual(
            outcome.kernel.project().results["RESULT-001"].delivery_state,
            DeliveryState.DELIVERED_EXTERNAL,
        )
        self.assertEqual(
            outcome.kernel.project().results["RESULT-002"].delivery_state,
            DeliveryState.DELIVERED_RESIDENT,
        )
        self.assertGreater(outcome.audits[0].savings, 0)

    def test_no_positive_relief_has_exact_blocker(self) -> None:
        first = make_result("RESULT-001", payload="x")
        kernel = delivered_kernel(first)
        composer = PacketComposer()
        manager = CapacityManager(
            composer=composer,
            count_messages=count_chars,
            prompt_limit=1,
        )
        outcome = manager.ensure_feasible(kernel)
        self.assertFalse(outcome.feasible)
        self.assertEqual(outcome.blocker, "no_strictly_positive_eligible_relief")


if __name__ == "__main__":
    unittest.main()
