from __future__ import annotations

import unittest

from host_refactor.kernel import HostKernel, InvalidTransition
from host_refactor.model import (
    DeliveryState,
    ExactResult,
    ExactStateObject,
    TranscriptEntry,
)
from reactive_runtime.canonical import sha256_bytes


def result(result_id: str = "RESULT-001", *, version: str = "v1") -> ExactResult:
    return ExactResult(
        result_id=result_id,
        result_kind="source_observation",
        object_id="SOURCE-A:1-2",
        object_version=version,
        exact_content=f"header {result_id}\n--- exact result body ---\nalpha\nbeta",
        payload_content="alpha\nbeta",
        acquired_call=1,
        candidate_sha256_after="candidate-0",
        span_key="SOURCE-A:1-2",
    )


class HostKernelTests(unittest.TestCase):
    def test_acquisition_schedule_and_completed_delivery_are_distinct(self) -> None:
        kernel = HostKernel().acquire(result())
        self.assertEqual(
            kernel.project().results["RESULT-001"].delivery_state,
            DeliveryState.ACQUIRED,
        )
        kernel = kernel.schedule(
            "RESULT-001", call_index=2, transcript_entry_id="ENTRY-001"
        )
        self.assertEqual(
            kernel.project().results["RESULT-001"].delivery_state,
            DeliveryState.PENDING,
        )
        kernel = kernel.complete_invocation(
            call_index=2,
            included_result_ids=("RESULT-001",),
            request_sha256="request",
            response_sha256="response",
        )
        row = kernel.project().results["RESULT-001"]
        self.assertEqual(row.delivery_state, DeliveryState.DELIVERED_RESIDENT)
        self.assertEqual(row.first_delivered_call, 2)

    def test_provider_failure_does_not_commit_delivery(self) -> None:
        kernel = (
            HostKernel()
            .acquire(result())
            .schedule("RESULT-001", call_index=2, transcript_entry_id="ENTRY-001")
        )
        kernel = kernel.fail_provider(
            call_index=2,
            request_sha256="request",
            error_type="TimeoutError",
            error_message="timed out",
        )
        self.assertEqual(
            kernel.project().results["RESULT-001"].delivery_state,
            DeliveryState.PENDING,
        )
        self.assertEqual(kernel.project().failed_calls, (2,))

    def test_invalid_lifecycle_transitions_fail(self) -> None:
        kernel = HostKernel().acquire(result())
        with self.assertRaises(InvalidTransition):
            kernel.externalize("RESULT-001", reason="invalid")
        with self.assertRaises(InvalidTransition):
            kernel.complete_invocation(
                call_index=1,
                included_result_ids=("RESULT-001",),
                request_sha256="request",
                response_sha256="response",
            )

    def test_same_bytes_under_different_version_are_distinct(self) -> None:
        self.assertNotEqual(
            result().body_identity, result("RESULT-002", version="v2").body_identity
        )

    def test_event_round_trip_is_hash_stable(self) -> None:
        kernel = HostKernel().append_transcript(
            TranscriptEntry("SYSTEM", "system", "system")
        )
        hydrated = HostKernel.from_dict(kernel.as_dict())
        self.assertEqual(hydrated.as_dict(), kernel.as_dict())
        self.assertEqual(
            hydrated.project().events_sha256,
            kernel.project().events_sha256,
        )

    def test_rejected_response_externalization_requires_exact_prior_rejection(
        self,
    ) -> None:
        content = '{"action":"partial"}'
        response_sha256 = sha256_bytes(content.encode("utf-8"))
        kernel = (
            HostKernel()
            .complete_invocation(
                call_index=1,
                included_result_ids=(),
                request_sha256="request",
                response_sha256=response_sha256,
                finish_reason="length",
            )
            .append_transcript(
                TranscriptEntry(
                    "CALL-000001-ASSISTANT",
                    "assistant",
                    content,
                )
            )
        )
        with self.assertRaises(InvalidTransition):
            kernel.externalize_rejected_response(
                call_index=1,
                finish_reason="length",
                response_sha256=response_sha256,
                rejection_result_id="REJECTION-1",
                transcript_entry_id="CALL-000001-ASSISTANT",
            )
        rejected = kernel.record_response_rejection(
            call_index=1,
            finish_reason="length",
            response_sha256=response_sha256,
            rejection_result_id="REJECTION-1",
        )
        with self.assertRaises(InvalidTransition):
            rejected.externalize_rejected_response(
                call_index=1,
                finish_reason="length",
                response_sha256="wrong",
                rejection_result_id="REJECTION-1",
                transcript_entry_id="CALL-000001-ASSISTANT",
            )
        externalized = rejected.externalize_rejected_response(
            call_index=1,
            finish_reason="length",
            response_sha256=response_sha256,
            rejection_result_id="REJECTION-1",
            transcript_entry_id="CALL-000001-ASSISTANT",
        )
        receipt = externalized.project().transcript[-1]
        self.assertEqual(
            receipt.entry_kind, "rejected_assistant_response_receipt"
        )
        self.assertNotIn(content, receipt.content)
        with self.assertRaises(InvalidTransition):
            externalized.externalize_rejected_response(
                call_index=1,
                finish_reason="length",
                response_sha256=response_sha256,
                rejection_result_id="REJECTION-1",
                transcript_entry_id="CALL-000001-ASSISTANT",
            )

    def test_state_slot_replaces_current_value_without_rewriting_history(self) -> None:
        first = ExactStateObject(
            "current_candidate",
            "candidate:task",
            "v1",
            "candidate one",
            {"candidate_sha256": "c1"},
        )
        second = ExactStateObject(
            "current_candidate",
            "candidate:task",
            "v2",
            "candidate two",
            {"candidate_sha256": "c2"},
        )
        kernel = (
            HostKernel()
            .set_state_object(first)
            .append_transcript(
                TranscriptEntry(
                    "CANDIDATE",
                    "user",
                    first.exact_content,
                    state_slot_id="current_candidate",
                )
            )
        )
        kernel = kernel.set_state_object(second)
        self.assertEqual(
            kernel.project().state_slots["current_candidate"].object_version,
            "v2",
        )
        self.assertEqual(len(kernel.events), 3)
        with self.assertRaises(InvalidTransition):
            kernel.set_state_object(second)


if __name__ == "__main__":
    unittest.main()
