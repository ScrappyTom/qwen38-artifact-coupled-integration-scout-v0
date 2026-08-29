from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from reactive_runtime.canonical import canonical_json_bytes, sha256_bytes


class DeliveryState(str, Enum):
    ACQUIRED = "acquired"
    PENDING = "pending"
    DELIVERED_RESIDENT = "delivered_resident"
    DELIVERED_EXTERNAL = "delivered_external"


class EventKind(str, Enum):
    STATE_SLOT_SET = "state_slot_set"
    TRANSCRIPT_APPENDED = "transcript_appended"
    RESULT_ACQUIRED = "result_acquired"
    RESULT_SCHEDULED = "result_scheduled"
    INVOCATION_COMPLETED = "invocation_completed"
    PROVIDER_FAILED = "provider_failed"
    RESULT_EXTERNALIZED = "result_externalized"
    CANDIDATE_EFFECT_EXTERNALIZED = "candidate_effect_externalized"
    REOPEN_REQUESTED = "reopen_requested"
    REPEAT_DEMAND = "repeat_demand"
    RESPONSE_REJECTED = "response_rejected"
    REJECTED_RESPONSE_EXTERNALIZED = "rejected_response_externalized"
    ACTION_DISPOSITION = "action_disposition"
    REQUEST_BINDING_REJECTED = "request_binding_rejected"
    TERMINAL_RECORDED = "terminal_recorded"


class TerminalCode(str, Enum):
    PROVIDER_FAILURE = "provider_failure"
    INVALID_ACTION = "invalid_action"
    DOMAIN_FAILURE = "domain_failure"
    REQUEST_BINDING_FAILURE = "request_binding_failure"
    CAPACITY_BLOCKED = "capacity_blocked"
    CHECKPOINT_PAUSE = "checkpoint_pause"
    CALL_BUDGET_EXHAUSTED = "call_budget_exhausted"
    TOKEN_BUDGET_EXHAUSTED = "token_budget_exhausted"
    COMPLETED = "completed"


@dataclass(frozen=True, order=True)
class CanonicalBodyIdentity:
    payload_sha256: str
    object_id: str
    object_version: str
    span_key: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "object_id": self.object_id,
            "object_version": self.object_version,
            "payload_sha256": self.payload_sha256,
            "span_key": self.span_key,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CanonicalBodyIdentity":
        return cls(
            payload_sha256=str(value["payload_sha256"]),
            object_id=str(value["object_id"]),
            object_version=str(value["object_version"]),
            span_key=str(value.get("span_key", "")),
        )


@dataclass(frozen=True)
class ExactResult:
    result_id: str
    result_kind: str
    object_id: str
    object_version: str
    exact_content: str
    payload_content: str
    acquired_call: int
    candidate_sha256_after: str
    relief_eligible: bool = True
    evaluated_candidate_sha256: str | None = None
    raw_result_handle: str | None = None
    span_key: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def body_identity(self) -> CanonicalBodyIdentity:
        return CanonicalBodyIdentity(
            payload_sha256=sha256_bytes(self.payload_content.encode("utf-8")),
            object_id=self.object_id,
            object_version=self.object_version,
            span_key=self.span_key,
        )

    @property
    def exact_content_sha256(self) -> str:
        return sha256_bytes(self.exact_content.encode("utf-8"))

    def as_dict(self) -> dict[str, Any]:
        return {
            "acquired_call": self.acquired_call,
            "body_identity": self.body_identity.as_dict(),
            "candidate_sha256_after": self.candidate_sha256_after,
            "evaluated_candidate_sha256": self.evaluated_candidate_sha256,
            "exact_content": self.exact_content,
            "exact_content_sha256": self.exact_content_sha256,
            "metadata": dict(self.metadata),
            "object_id": self.object_id,
            "object_version": self.object_version,
            "payload_content": self.payload_content,
            "raw_result_handle": self.raw_result_handle,
            "relief_eligible": self.relief_eligible,
            "result_id": self.result_id,
            "result_kind": self.result_kind,
            "span_key": self.span_key,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExactResult":
        result = cls(
            result_id=str(value["result_id"]),
            result_kind=str(value["result_kind"]),
            object_id=str(value["object_id"]),
            object_version=str(value["object_version"]),
            exact_content=str(value["exact_content"]),
            payload_content=str(value["payload_content"]),
            acquired_call=int(value["acquired_call"]),
            candidate_sha256_after=str(value["candidate_sha256_after"]),
            relief_eligible=bool(value.get("relief_eligible", True)),
            evaluated_candidate_sha256=(
                None
                if value.get("evaluated_candidate_sha256") is None
                else str(value["evaluated_candidate_sha256"])
            ),
            raw_result_handle=(
                None
                if value.get("raw_result_handle") is None
                else str(value["raw_result_handle"])
            ),
            span_key=str(value.get("span_key", "")),
            metadata=dict(value.get("metadata", {})),
        )
        if value.get("exact_content_sha256") not in (
            None,
            result.exact_content_sha256,
        ):
            raise ValueError(f"exact content hash mismatch: {result.result_id}")
        if value.get("body_identity") not in (
            None,
            result.body_identity.as_dict(),
        ):
            raise ValueError(f"canonical body identity mismatch: {result.result_id}")
        return result


@dataclass(frozen=True)
class ExactStateObject:
    slot_id: str
    object_id: str
    object_version: str
    exact_content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def content_sha256(self) -> str:
        return sha256_bytes(self.exact_content.encode("utf-8"))

    def as_dict(self) -> dict[str, Any]:
        return {
            "content_sha256": self.content_sha256,
            "exact_content": self.exact_content,
            "metadata": dict(self.metadata),
            "object_id": self.object_id,
            "object_version": self.object_version,
            "slot_id": self.slot_id,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExactStateObject":
        state_object = cls(
            slot_id=str(value["slot_id"]),
            object_id=str(value["object_id"]),
            object_version=str(value["object_version"]),
            exact_content=str(value["exact_content"]),
            metadata=dict(value.get("metadata", {})),
        )
        if value.get("content_sha256") not in (None, state_object.content_sha256):
            raise ValueError(f"state object hash mismatch: {state_object.slot_id}")
        return state_object


@dataclass(frozen=True)
class TranscriptEntry:
    entry_id: str
    role: str
    content: str
    result_id: str | None = None
    state_slot_id: str | None = None
    entry_kind: str = "ordinary"

    def as_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "entry_id": self.entry_id,
            "entry_kind": self.entry_kind,
            "result_id": self.result_id,
            "role": self.role,
            "state_slot_id": self.state_slot_id,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TranscriptEntry":
        return cls(
            entry_id=str(value["entry_id"]),
            role=str(value["role"]),
            content=str(value["content"]),
            result_id=(
                None if value.get("result_id") is None else str(value["result_id"])
            ),
            state_slot_id=(
                None
                if value.get("state_slot_id") is None
                else str(value["state_slot_id"])
            ),
            entry_kind=str(value.get("entry_kind", "ordinary")),
        )


@dataclass(frozen=True)
class HostEvent:
    ordinal: int
    event_id: str
    kind: EventKind
    data: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "data": dict(self.data),
            "event_id": self.event_id,
            "kind": self.kind.value,
            "ordinal": self.ordinal,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "HostEvent":
        return cls(
            ordinal=int(value["ordinal"]),
            event_id=str(value["event_id"]),
            kind=EventKind(str(value["kind"])),
            data=dict(value["data"]),
        )


@dataclass(frozen=True)
class ResultProjection:
    result: ExactResult
    delivery_state: DeliveryState
    pending_call: int | None = None
    transcript_entry_id: str | None = None
    first_delivered_call: int | None = None
    last_delivered_call: int | None = None
    demand_count: int = 1
    reopen_count: int = 0


@dataclass(frozen=True)
class ProjectedHostState:
    results: Mapping[str, ResultProjection]
    state_slots: Mapping[str, ExactStateObject]
    transcript: tuple[TranscriptEntry, ...]
    completed_calls: tuple[int, ...]
    failed_calls: tuple[int, ...]
    terminal: TerminalCode | None
    events_sha256: str

    @property
    def pending_result_ids(self) -> tuple[str, ...]:
        return tuple(
            result_id
            for result_id, row in self.results.items()
            if row.delivery_state is DeliveryState.PENDING
        )

    @property
    def resident_result_ids(self) -> tuple[str, ...]:
        return tuple(
            result_id
            for result_id, row in self.results.items()
            if row.delivery_state is DeliveryState.DELIVERED_RESIDENT
        )


@dataclass(frozen=True)
class RunConfiguration:
    run_id: str
    task_id: str
    seed: int
    context_window: int
    response_reserve: int
    execution_manifest_sha256: str
    accepted_finish_reasons: tuple[str, ...] = ("stop",)
    tranche_calls: int = 12
    maximum_calls: int = 60
    maximum_serialized_tokens: int | None = None

    def __post_init__(self) -> None:
        if self.context_window <= 0:
            raise ValueError("context window must be positive")
        if self.response_reserve <= 0:
            raise ValueError("response reserve must be positive")
        if self.response_reserve >= self.context_window:
            raise ValueError("response reserve must be smaller than context window")
        if len(self.execution_manifest_sha256) != 64 or any(
            character not in "0123456789abcdef"
            for character in self.execution_manifest_sha256
        ):
            raise ValueError("execution manifest must be a lowercase SHA-256")
        if not self.accepted_finish_reasons or any(
            not isinstance(value, str) or not value
            for value in self.accepted_finish_reasons
        ):
            raise ValueError("accepted finish reasons must be non-empty strings")
        if self.tranche_calls <= 0 or self.maximum_calls <= 0:
            raise ValueError("call budgets must be positive")
        if self.tranche_calls > self.maximum_calls:
            raise ValueError("tranche calls cannot exceed maximum calls")

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted_finish_reasons": list(self.accepted_finish_reasons),
            "context_window": self.context_window,
            "execution_manifest_sha256": self.execution_manifest_sha256,
            "maximum_calls": self.maximum_calls,
            "maximum_serialized_tokens": self.maximum_serialized_tokens,
            "prompt_limit": self.prompt_limit,
            "response_reserve": self.response_reserve,
            "run_id": self.run_id,
            "seed": self.seed,
            "task_id": self.task_id,
            "tranche_calls": self.tranche_calls,
        }

    @property
    def prompt_limit(self) -> int:
        """Effective prompt allowance after the frozen completion reserve."""

        return self.context_window - self.response_reserve

    @property
    def sha256(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.as_dict()))
