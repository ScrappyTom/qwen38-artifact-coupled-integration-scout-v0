from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable, Mapping

from reactive_runtime.canonical import canonical_json_bytes, sha256_bytes
from reactive_runtime.canonical import canonical_json_text

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
                "request_sha256": request_sha256,
            },
        )
        return failed.record_terminal(TerminalCode.PROVIDER_FAILURE)

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
