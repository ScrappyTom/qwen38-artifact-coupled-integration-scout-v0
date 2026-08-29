from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable, Mapping

from reactive_runtime.canonical import (
    canonical_json_bytes,
    canonical_json_text,
    sha256_bytes,
)

from host_refactor.model import (
    DeliveryState,
    EventKind,
    ExactResult,
    ExactStateObject,
    HostEvent,
    ProjectedHostState,
    ResultProjection,
    TerminalCode,
    TranscriptEntry,
)


class InvalidTransition(ValueError):
    """Raised when an event would violate the frozen host lifecycle."""


class HostKernel:
    """Append-only authority for host result delivery and residency.

    The kernel performs no prompt rendering and no provider calls. Every public
    mutator validates by replaying the proposed event before returning a new
    immutable kernel instance.
    """

    def __init__(self, events: Iterable[HostEvent] = ()) -> None:
        self._events = tuple(events)
        self._validate_event_sequence()
        self.project()

    @property
    def events(self) -> tuple[HostEvent, ...]:
        return self._events

    @property
    def next_ordinal(self) -> int:
        return len(self._events) + 1

    def _validate_event_sequence(self) -> None:
        expected = 1
        event_ids: set[str] = set()
        for event in self._events:
            if event.ordinal != expected:
                raise InvalidTransition(
                    f"event ordinal {event.ordinal} does not equal {expected}"
                )
            if event.event_id in event_ids:
                raise InvalidTransition(f"duplicate event id: {event.event_id}")
            event_ids.add(event.event_id)
            expected += 1

    def _append(self, kind: EventKind, data: Mapping[str, Any]) -> "HostKernel":
        ordinal = self.next_ordinal
        event = HostEvent(
            ordinal=ordinal,
            event_id=f"EVENT-{ordinal:06d}",
            kind=kind,
            data=dict(data),
        )
        return HostKernel((*self._events, event))

    def append_transcript(self, entry: TranscriptEntry) -> "HostKernel":
        state = self.project()
        if any(row.entry_id == entry.entry_id for row in state.transcript):
            raise InvalidTransition(f"duplicate transcript entry: {entry.entry_id}")
        if entry.result_id is not None and entry.result_id not in state.results:
            raise InvalidTransition(
                f"result transcript entry precedes acquisition: {entry.result_id}"
            )
        if (
            entry.state_slot_id is not None
            and entry.state_slot_id not in state.state_slots
        ):
            raise InvalidTransition(
                f"state transcript entry precedes slot value: {entry.state_slot_id}"
            )
        if entry.result_id is not None and entry.state_slot_id is not None:
            raise InvalidTransition(
                "transcript entry cannot bind result and state slot"
            )
        return self._append(EventKind.TRANSCRIPT_APPENDED, {"entry": entry.as_dict()})

    def set_state_object(self, state_object: ExactStateObject) -> "HostKernel":
        state = self.project()
        prior = state.state_slots.get(state_object.slot_id)
        if prior is not None and prior.as_dict() == state_object.as_dict():
            raise InvalidTransition(
                f"state slot already has exact value: {state_object.slot_id}"
            )
        return self._append(
            EventKind.STATE_SLOT_SET,
            {"state_object": state_object.as_dict()},
        )

    def acquire(self, result: ExactResult) -> "HostKernel":
        state = self.project()
        if result.result_id in state.results:
            raise InvalidTransition(f"duplicate result id: {result.result_id}")
        return self._append(EventKind.RESULT_ACQUIRED, {"result": result.as_dict()})

    def schedule(
        self,
        result_id: str,
        *,
        call_index: int,
        transcript_entry_id: str,
    ) -> "HostKernel":
        state = self.project()
        row = self._result(state, result_id)
        if call_index in state.completed_calls or call_index in state.failed_calls:
            raise InvalidTransition(f"call already resolved: {call_index}")
        if row.delivery_state not in {
            DeliveryState.ACQUIRED,
            DeliveryState.DELIVERED_EXTERNAL,
        }:
            raise InvalidTransition(
                f"cannot schedule {result_id} from {row.delivery_state.value}"
            )
        if any(
            projection.delivery_state is DeliveryState.PENDING
            and projection.pending_call == call_index
            for projection in state.results.values()
        ):
            raise InvalidTransition(
                f"call already has pending exact result: {call_index}"
            )
        scheduled = self._append(
            EventKind.RESULT_SCHEDULED,
            {
                "call_index": call_index,
                "result_id": result_id,
                "transcript_entry_id": transcript_entry_id,
            },
        )
        return scheduled.append_transcript(
            TranscriptEntry(
                entry_id=transcript_entry_id,
                role="user",
                content=row.result.exact_content,
                result_id=result_id,
                entry_kind="exact_result",
            )
        )

    def complete_invocation(
        self,
        *,
        call_index: int,
        included_result_ids: Iterable[str],
        request_sha256: str,
        response_sha256: str,
        usage: Mapping[str, Any] | None = None,
        request_binding: Mapping[str, Any] | None = None,
        finish_reason: str = "stop",
        provider_custody: Mapping[str, str] | None = None,
    ) -> "HostKernel":
        state = self.project()
        if call_index in state.completed_calls or call_index in state.failed_calls:
            raise InvalidTransition(f"call already resolved: {call_index}")
        included = tuple(included_result_ids)
        expected = tuple(
            result_id
            for result_id, row in state.results.items()
            if row.delivery_state is DeliveryState.PENDING
            and row.pending_call == call_index
        )
        if set(included) != set(expected):
            raise InvalidTransition(
                f"completed call {call_index} included {included}; pending was {expected}"
            )
        return self._append(
            EventKind.INVOCATION_COMPLETED,
            {
                "call_index": call_index,
                "included_result_ids": list(included),
                "finish_reason": finish_reason,
                "provider_custody": dict(provider_custody or {}),
                "request_binding": dict(request_binding or {}),
                "request_sha256": request_sha256,
                "response_sha256": response_sha256,
                "usage": dict(usage or {}),
            },
        )

    def fail_provider(
        self,
        *,
        call_index: int,
        request_sha256: str,
        error_type: str,
        error_message: str,
        request_binding: Mapping[str, Any] | None = None,
        provider_custody: Mapping[str, str] | None = None,
    ) -> "HostKernel":
        state = self.project()
        if call_index in state.completed_calls or call_index in state.failed_calls:
            raise InvalidTransition(f"call already resolved: {call_index}")
        failed = self._append(
            EventKind.PROVIDER_FAILED,
            {
                "call_index": call_index,
                "error_message": error_message,
                "error_type": error_type,
                "provider_custody": dict(provider_custody or {}),
                "request_binding": dict(request_binding or {}),
                "request_sha256": request_sha256,
            },
        )
        return failed.record_terminal(TerminalCode.PROVIDER_FAILURE)

    def record_response_rejection(
        self,
        *,
        call_index: int,
        finish_reason: str,
        response_sha256: str,
        rejection_result_id: str,
    ) -> "HostKernel":
        return self._append(
            EventKind.RESPONSE_REJECTED,
            {
                "call_index": call_index,
                "finish_reason": finish_reason,
                "rejection_result_id": rejection_result_id,
                "response_sha256": response_sha256,
            },
        )

    def externalize_rejected_response(
        self,
        *,
        call_index: int,
        finish_reason: str,
        response_sha256: str,
        rejection_result_id: str,
        transcript_entry_id: str,
    ) -> "HostKernel":
        """Remove an unadmitted response body from ordinary prompt residency.

        The exact body remains in the append-only event log and provider custody.
        This transition is allowed only after the completed invocation has been
        explicitly rejected and therefore caused no admitted domain action.
        """

        return self._append(
            EventKind.REJECTED_RESPONSE_EXTERNALIZED,
            {
                "call_index": call_index,
                "finish_reason": finish_reason,
                "rejection_result_id": rejection_result_id,
                "response_sha256": response_sha256,
                "transcript_entry_id": transcript_entry_id,
            },
        )

    def record_request_binding_rejection(
        self,
        *,
        call_index: int,
        packet_sha256: str,
        packet_manifest_sha256: str,
        error_message: str,
    ) -> "HostKernel":
        return self._append(
            EventKind.REQUEST_BINDING_REJECTED,
            {
                "call_index": call_index,
                "error_message": error_message,
                "packet_manifest_sha256": packet_manifest_sha256,
                "packet_sha256": packet_sha256,
            },
        )

    def record_action_disposition(
        self,
        *,
        call_index: int,
        status: str,
        response_sha256: str,
        candidate_sha256_before: str | None,
        candidate_sha256_after: str | None,
        action: Mapping[str, Any] | None = None,
        rejection_code: str | None = None,
        rejection_message: str | None = None,
        result_id: str | None = None,
    ) -> "HostKernel":
        if status not in {"accepted", "rejected", "response_rejected"}:
            raise ValueError(f"unsupported action disposition: {status}")
        return self._append(
            EventKind.ACTION_DISPOSITION,
            {
                "action": None if action is None else dict(action),
                "call_index": call_index,
                "candidate_sha256_after": candidate_sha256_after,
                "candidate_sha256_before": candidate_sha256_before,
                "rejection_code": rejection_code,
                "rejection_message": rejection_message,
                "response_sha256": response_sha256,
                "result_id": result_id,
                "status": status,
            },
        )

    def externalize(self, result_id: str, *, reason: str) -> "HostKernel":
        state = self.project()
        row = self._result(state, result_id)
        if row.delivery_state is not DeliveryState.DELIVERED_RESIDENT:
            raise InvalidTransition(
                f"cannot externalize {result_id} from {row.delivery_state.value}"
            )
        if not row.result.relief_eligible:
            raise InvalidTransition(f"result is not relief eligible: {result_id}")
        return self._append(
            EventKind.RESULT_EXTERNALIZED,
            {"reason": reason, "result_id": result_id},
        )

    def externalize_applied_candidate_effect(
        self,
        result_id: str,
        *,
        current_candidate_sha256: str,
    ) -> "HostKernel":
        """Move a delivered effect out of residency after exact lineage proof.

        This is a lifecycle transition, not ordinary pressure relief. The
        result's exact bytes and delivery history remain in the event ledger.
        """

        state = self.project()
        row = self._result(state, result_id)
        if row.delivery_state is not DeliveryState.DELIVERED_RESIDENT:
            raise InvalidTransition(
                f"cannot lifecycle-externalize {result_id} from "
                f"{row.delivery_state.value}"
            )
        if row.result.result_kind != "candidate_effect":
            raise InvalidTransition(
                f"result is not a candidate effect: {result_id}"
            )
        observed_current = self._current_candidate_sha256(state)
        if observed_current != current_candidate_sha256:
            raise InvalidTransition("declared current candidate hash mismatch")
        if not self._effect_is_ancestor_of_current(state, result_id):
            raise InvalidTransition(
                f"candidate effect is not in current candidate lineage: {result_id}"
            )
        action_entry_id = f"CALL-{row.result.acquired_call:06d}-ASSISTANT"
        try:
            action_entry = next(
                entry
                for entry in state.transcript
                if entry.entry_id == action_entry_id
            )
        except StopIteration as exc:
            raise InvalidTransition(
                f"candidate effect lacks exact causal action: {result_id}"
            ) from exc
        if action_entry.role != "assistant" or action_entry.result_id is not None:
            raise InvalidTransition(
                f"candidate effect causal action is not ordinary assistant output: "
                f"{result_id}"
            )
        action_sha256 = sha256_bytes(action_entry.content.encode("utf-8"))
        return self._append(
            EventKind.CANDIDATE_EFFECT_EXTERNALIZED,
            {
                "action_entry_id": action_entry_id,
                "action_sha256": action_sha256,
                "current_candidate_sha256": current_candidate_sha256,
                "reason": "effect_represented_by_current_candidate",
                "result_id": result_id,
            },
        )

    def request_reopen(
        self,
        result_id: str,
        *,
        call_index: int,
        transcript_entry_id: str,
    ) -> "HostKernel":
        state = self.project()
        row = self._result(state, result_id)
        if row.delivery_state is not DeliveryState.DELIVERED_EXTERNAL:
            raise InvalidTransition(
                f"cannot reopen {result_id} from {row.delivery_state.value}"
            )
        reopened = self._append(
            EventKind.REOPEN_REQUESTED,
            {"call_index": call_index, "result_id": result_id},
        )
        return reopened.schedule(
            result_id,
            call_index=call_index,
            transcript_entry_id=transcript_entry_id,
        )

    def record_repeat_demand(
        self,
        *,
        requested_result: ExactResult,
        resident_result_id: str,
        feedback_entry_id: str,
    ) -> "HostKernel":
        state = self.project()
        resident = self._result(state, resident_result_id)
        if resident.delivery_state is not DeliveryState.DELIVERED_RESIDENT:
            raise InvalidTransition(
                f"repeat target is not resident: {resident_result_id}"
            )
        if requested_result.body_identity != resident.result.body_identity:
            raise InvalidTransition(
                "repeat demand body identity does not match resident target"
            )
        if requested_result.result_id in state.results:
            raise InvalidTransition(
                f"duplicate result id: {requested_result.result_id}"
            )
        feedback = {
            "canonical_body_identity": resident.result.body_identity.as_dict(),
            "requested_result_id": requested_result.result_id,
            "resident_result_id": resident_result_id,
            "schema": "bounded-host-already-resident-v0",
            "status": "already_resident",
        }
        repeated = self._append(
            EventKind.REPEAT_DEMAND,
            {
                "feedback": feedback,
                "feedback_entry_id": feedback_entry_id,
                "requested_result": requested_result.as_dict(),
                "resident_result_id": resident_result_id,
            },
        )
        return repeated.append_transcript(
            TranscriptEntry(
                entry_id=feedback_entry_id,
                role="user",
                content=canonical_json_text(feedback),
                entry_kind="already_resident",
            )
        )

    def record_terminal(self, code: TerminalCode) -> "HostKernel":
        state = self.project()
        if state.terminal is not None:
            raise InvalidTransition(
                f"terminal already recorded: {state.terminal.value}"
            )
        return self._append(EventKind.TERMINAL_RECORDED, {"code": code.value})

    def resident_match(self, result: ExactResult) -> str | None:
        for result_id, row in self.project().results.items():
            if (
                row.delivery_state is DeliveryState.DELIVERED_RESIDENT
                and row.result.body_identity == result.body_identity
            ):
                return result_id
        return None

    def project(self) -> ProjectedHostState:
        results: dict[str, ResultProjection] = {}
        state_slots: dict[str, ExactStateObject] = {}
        transcript: list[TranscriptEntry] = []
        completed: list[int] = []
        failed: list[int] = []
        completed_responses: dict[int, dict[str, str]] = {}
        rejected_responses: dict[int, dict[str, str]] = {}
        terminal: TerminalCode | None = None
        for event in self._events:
            data = event.data
            if event.kind is EventKind.STATE_SLOT_SET:
                state_object = ExactStateObject.from_dict(data["state_object"])
                prior = state_slots.get(state_object.slot_id)
                if prior is not None and prior.as_dict() == state_object.as_dict():
                    raise InvalidTransition(
                        f"state slot already has exact value: {state_object.slot_id}"
                    )
                state_slots[state_object.slot_id] = state_object
            elif event.kind is EventKind.RESULT_ACQUIRED:
                result = ExactResult.from_dict(data["result"])
                if result.result_id in results:
                    raise InvalidTransition(f"duplicate result id: {result.result_id}")
                results[result.result_id] = ResultProjection(
                    result=result,
                    delivery_state=DeliveryState.ACQUIRED,
                )
            elif event.kind is EventKind.TRANSCRIPT_APPENDED:
                entry = TranscriptEntry.from_dict(data["entry"])
                if any(row.entry_id == entry.entry_id for row in transcript):
                    raise InvalidTransition(
                        f"duplicate transcript entry: {entry.entry_id}"
                    )
                transcript.append(entry)
            elif event.kind is EventKind.RESULT_SCHEDULED:
                result_id = str(data["result_id"])
                row = self._result_map(results, result_id)
                if row.delivery_state not in {
                    DeliveryState.ACQUIRED,
                    DeliveryState.DELIVERED_EXTERNAL,
                }:
                    raise InvalidTransition(
                        f"cannot schedule {result_id} from {row.delivery_state.value}"
                    )
                call_index = int(data["call_index"])
                if any(
                    projection.delivery_state is DeliveryState.PENDING
                    and projection.pending_call == call_index
                    for projection in results.values()
                ):
                    raise InvalidTransition(
                        f"call already has pending exact result: {call_index}"
                    )
                results[result_id] = replace(
                    row,
                    delivery_state=DeliveryState.PENDING,
                    pending_call=call_index,
                    transcript_entry_id=str(data["transcript_entry_id"]),
                    reopen_count=(
                        row.reopen_count + 1
                        if row.first_delivered_call is not None
                        else row.reopen_count
                    ),
                )
            elif event.kind is EventKind.INVOCATION_COMPLETED:
                call_index = int(data["call_index"])
                if call_index in completed or call_index in failed:
                    raise InvalidTransition(f"call already resolved: {call_index}")
                included = tuple(str(value) for value in data["included_result_ids"])
                expected = tuple(
                    result_id
                    for result_id, row in results.items()
                    if row.delivery_state is DeliveryState.PENDING
                    and row.pending_call == call_index
                )
                if set(included) != set(expected):
                    raise InvalidTransition(
                        f"completed call {call_index} included {included}; pending was {expected}"
                    )
                for result_id in included:
                    row = results[result_id]
                    results[result_id] = replace(
                        row,
                        delivery_state=DeliveryState.DELIVERED_RESIDENT,
                        pending_call=None,
                        first_delivered_call=(
                            call_index
                            if row.first_delivered_call is None
                            else row.first_delivered_call
                        ),
                        last_delivered_call=call_index,
                    )
                completed.append(call_index)
                completed_responses[call_index] = {
                    "finish_reason": str(data["finish_reason"]),
                    "response_sha256": str(data["response_sha256"]),
                }
            elif event.kind is EventKind.PROVIDER_FAILED:
                call_index = int(data["call_index"])
                if call_index in completed or call_index in failed:
                    raise InvalidTransition(f"call already resolved: {call_index}")
                failed.append(call_index)
            elif event.kind is EventKind.RESULT_EXTERNALIZED:
                result_id = str(data["result_id"])
                row = self._result_map(results, result_id)
                if row.delivery_state is not DeliveryState.DELIVERED_RESIDENT:
                    raise InvalidTransition(
                        f"cannot externalize {result_id} from {row.delivery_state.value}"
                    )
                if not row.result.relief_eligible:
                    raise InvalidTransition(
                        f"result is not relief eligible: {result_id}"
                    )
                results[result_id] = replace(
                    row,
                    delivery_state=DeliveryState.DELIVERED_EXTERNAL,
                )
            elif event.kind is EventKind.CANDIDATE_EFFECT_EXTERNALIZED:
                result_id = str(data["result_id"])
                row = self._result_map(results, result_id)
                if row.delivery_state is not DeliveryState.DELIVERED_RESIDENT:
                    raise InvalidTransition(
                        f"cannot lifecycle-externalize {result_id} from "
                        f"{row.delivery_state.value}"
                    )
                if row.result.result_kind != "candidate_effect":
                    raise InvalidTransition(
                        f"result is not a candidate effect: {result_id}"
                    )
                declared_current = str(data["current_candidate_sha256"])
                if self._current_candidate_sha256_from_slots(state_slots) != declared_current:
                    raise InvalidTransition("declared current candidate hash mismatch")
                projected_state = ProjectedHostState(
                    results=results,
                    state_slots=state_slots,
                    transcript=tuple(transcript),
                    completed_calls=tuple(completed),
                    failed_calls=tuple(failed),
                    terminal=terminal,
                    events_sha256="",
                )
                if not self._effect_is_ancestor_of_current(
                    projected_state, result_id
                ):
                    raise InvalidTransition(
                        f"candidate effect is not in current candidate lineage: {result_id}"
                    )
                action_entry_id = str(data["action_entry_id"])
                expected_action_entry_id = (
                    f"CALL-{row.result.acquired_call:06d}-ASSISTANT"
                )
                if action_entry_id != expected_action_entry_id:
                    raise InvalidTransition(
                        f"candidate effect causal action mismatch: {result_id}"
                    )
                try:
                    action_index = next(
                        index
                        for index, entry in enumerate(transcript)
                        if entry.entry_id == action_entry_id
                    )
                except StopIteration as exc:
                    raise InvalidTransition(
                        f"candidate effect lacks exact causal action: {result_id}"
                    ) from exc
                action_entry = transcript[action_index]
                action_sha256 = sha256_bytes(
                    action_entry.content.encode("utf-8")
                )
                if action_sha256 != data["action_sha256"]:
                    raise InvalidTransition(
                        f"candidate effect causal action hash mismatch: {result_id}"
                    )
                transcript[action_index] = replace(
                    action_entry,
                    content=self._applied_candidate_action_receipt(
                        row.result,
                        action_entry_id=action_entry_id,
                        action_sha256=action_sha256,
                    ),
                    entry_kind="applied_candidate_action_receipt",
                )
                results[result_id] = replace(
                    row,
                    delivery_state=DeliveryState.DELIVERED_EXTERNAL,
                )
            elif event.kind is EventKind.REOPEN_REQUESTED:
                result_id = str(data["result_id"])
                row = self._result_map(results, result_id)
                if row.delivery_state is not DeliveryState.DELIVERED_EXTERNAL:
                    raise InvalidTransition(
                        f"cannot reopen {result_id} from {row.delivery_state.value}"
                    )
            elif event.kind is EventKind.REPEAT_DEMAND:
                requested = ExactResult.from_dict(data["requested_result"])
                resident_id = str(data["resident_result_id"])
                resident = self._result_map(results, resident_id)
                if resident.delivery_state is not DeliveryState.DELIVERED_RESIDENT:
                    raise InvalidTransition(
                        f"repeat target is not resident: {resident_id}"
                    )
                if requested.body_identity != resident.result.body_identity:
                    raise InvalidTransition("repeat body identity mismatch")
                results[resident_id] = replace(
                    resident,
                    demand_count=resident.demand_count + 1,
                )
            elif event.kind is EventKind.RESPONSE_REJECTED:
                call_index = int(data["call_index"])
                invocation = completed_responses.get(call_index)
                if invocation is None:
                    raise InvalidTransition(
                        f"response rejection precedes completed call: {call_index}"
                    )
                if invocation != {
                    "finish_reason": str(data["finish_reason"]),
                    "response_sha256": str(data["response_sha256"]),
                }:
                    raise InvalidTransition(
                        f"response rejection does not bind completed call: {call_index}"
                    )
                rejected_responses[call_index] = {
                    "finish_reason": str(data["finish_reason"]),
                    "rejection_result_id": str(data["rejection_result_id"]),
                    "response_sha256": str(data["response_sha256"]),
                }
            elif event.kind is EventKind.REJECTED_RESPONSE_EXTERNALIZED:
                call_index = int(data["call_index"])
                rejection = rejected_responses.get(call_index)
                expected_rejection = {
                    "finish_reason": str(data["finish_reason"]),
                    "rejection_result_id": str(data["rejection_result_id"]),
                    "response_sha256": str(data["response_sha256"]),
                }
                if rejection != expected_rejection:
                    raise InvalidTransition(
                        f"rejected response externalization lacks exact rejection: {call_index}"
                    )
                entry_id = str(data["transcript_entry_id"])
                try:
                    entry_index = next(
                        index
                        for index, entry in enumerate(transcript)
                        if entry.entry_id == entry_id
                    )
                except StopIteration as exc:
                    raise InvalidTransition(
                        f"rejected response transcript entry missing: {entry_id}"
                    ) from exc
                entry = transcript[entry_index]
                if entry.role != "assistant":
                    raise InvalidTransition(
                        f"rejected response transcript role is not assistant: {entry_id}"
                    )
                if entry.entry_kind == "rejected_assistant_response_receipt":
                    raise InvalidTransition(
                        f"rejected response already externalized: {entry_id}"
                    )
                if (
                    sha256_bytes(entry.content.encode("utf-8"))
                    != expected_rejection["response_sha256"]
                ):
                    raise InvalidTransition(
                        f"rejected response transcript hash mismatch: {entry_id}"
                    )
                transcript[entry_index] = replace(
                    entry,
                    content=self._rejected_response_receipt(
                        call_index=call_index,
                        finish_reason=expected_rejection["finish_reason"],
                        response_sha256=expected_rejection["response_sha256"],
                        rejection_result_id=expected_rejection[
                            "rejection_result_id"
                        ],
                        transcript_entry_id=entry_id,
                    ),
                    entry_kind="rejected_assistant_response_receipt",
                )
            elif event.kind in {
                EventKind.ACTION_DISPOSITION,
                EventKind.REQUEST_BINDING_REJECTED,
            }:
                # These events are exact audit facts and do not independently
                # mutate result, state-slot, or terminal projections.
                pass
            elif event.kind is EventKind.TERMINAL_RECORDED:
                if terminal is not None:
                    raise InvalidTransition(
                        f"terminal already recorded: {terminal.value}"
                    )
                terminal = TerminalCode(str(data["code"]))
            else:  # pragma: no cover - Enum exhaustiveness guard
                raise InvalidTransition(f"unsupported event kind: {event.kind}")
        event_bytes = canonical_json_bytes([event.as_dict() for event in self._events])
        return ProjectedHostState(
            results=results,
            state_slots=state_slots,
            transcript=tuple(transcript),
            completed_calls=tuple(completed),
            failed_calls=tuple(failed),
            terminal=terminal,
            events_sha256=sha256_bytes(event_bytes),
        )

    @staticmethod
    def _rejected_response_receipt(
        *,
        call_index: int,
        finish_reason: str,
        response_sha256: str,
        rejection_result_id: str,
        transcript_entry_id: str,
    ) -> str:
        return canonical_json_text(
            {
                "admitted_action": False,
                "call_index": call_index,
                "exact_response_retained_externally": True,
                "finish_reason": finish_reason,
                "history_handle": f"response://sha256/{response_sha256}",
                "rejection_result_id": rejection_result_id,
                "response_sha256": response_sha256,
                "schema": "bounded-host-rejected-response-receipt-v0",
                "transcript_entry_id": transcript_entry_id,
                "world_transition_applied": False,
            }
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "events": [event.as_dict() for event in self._events],
            "events_sha256": self.project().events_sha256,
            "schema": "bounded-host-event-log-v0",
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "HostKernel":
        if value.get("schema") != "bounded-host-event-log-v0":
            raise ValueError("unsupported host event-log schema")
        events = tuple(HostEvent.from_dict(row) for row in value.get("events", []))
        kernel = cls(events)
        if value.get("events_sha256") not in (None, kernel.project().events_sha256):
            raise ValueError("host event-log hash mismatch")
        return kernel

    @staticmethod
    def _result(state: ProjectedHostState, result_id: str) -> ResultProjection:
        return HostKernel._result_map(state.results, result_id)

    @staticmethod
    def _result_map(
        results: Mapping[str, ResultProjection], result_id: str
    ) -> ResultProjection:
        try:
            return results[result_id]
        except KeyError as exc:
            raise InvalidTransition(f"unknown result id: {result_id}") from exc

    @staticmethod
    def _current_candidate_sha256(state: ProjectedHostState) -> str | None:
        return HostKernel._current_candidate_sha256_from_slots(state.state_slots)

    @staticmethod
    def _current_candidate_sha256_from_slots(
        state_slots: Mapping[str, ExactStateObject],
    ) -> str | None:
        candidate = state_slots.get("current_candidate")
        if candidate is None:
            return None
        value = candidate.metadata.get("candidate_sha256")
        return None if value is None else str(value)

    @staticmethod
    def _effect_is_ancestor_of_current(
        state: ProjectedHostState,
        result_id: str,
    ) -> bool:
        effects = sorted(
            (
                row.result
                for row in state.results.values()
                if row.result.result_kind == "candidate_effect"
            ),
            key=lambda result: (result.acquired_call, result.result_id),
        )
        try:
            start = next(
                index
                for index, result in enumerate(effects)
                if result.result_id == result_id
            )
        except StopIteration:
            return False
        after = effects[start].candidate_sha256_after
        for later in effects[start + 1 :]:
            if later.metadata.get("before_sha256") != after:
                return False
            after = later.candidate_sha256_after
        return after == HostKernel._current_candidate_sha256(state)

    @staticmethod
    def _applied_candidate_action_receipt(
        result: ExactResult,
        *,
        action_entry_id: str,
        action_sha256: str,
    ) -> str:
        return canonical_json_text(
            {
                "candidate_sha256_after": result.candidate_sha256_after,
                "exact_action_sha256": action_sha256,
                "exact_history_entry_id": action_entry_id,
                "result_id": result.result_id,
                "schema": "bounded-host-applied-candidate-action-receipt-v0",
            }
        )
