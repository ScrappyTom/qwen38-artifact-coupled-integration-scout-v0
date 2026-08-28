from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from typing import Any, Mapping

from reactive_runtime.canonical import (
    canonical_json_bytes,
    load_json,
    sha256_bytes,
    write_json,
)

from host_refactor.kernel import HostKernel
from host_refactor.model import EventKind, RunConfiguration
from host_refactor.packet import PacketComposer


@dataclass(frozen=True)
class RuntimeCounters:
    serialized_tokens: int = 0
    provider_attempts: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "provider_attempts": self.provider_attempts,
            "serialized_tokens": self.serialized_tokens,
        }


@dataclass(frozen=True)
class CheckpointDecision:
    pause: bool
    reason: str | None


class CheckpointController:
    def __init__(self, configuration: RunConfiguration) -> None:
        self.configuration = configuration

    def decision(
        self, kernel: HostKernel, counters: RuntimeCounters
    ) -> CheckpointDecision:
        state = kernel.project()
        completed = len(state.completed_calls)
        if state.terminal is not None:
            return CheckpointDecision(False, None)
        if completed >= self.configuration.maximum_calls:
            return CheckpointDecision(True, "maximum_call_budget")
        if (
            self.configuration.maximum_serialized_tokens is not None
            and counters.serialized_tokens
            >= self.configuration.maximum_serialized_tokens
        ):
            return CheckpointDecision(True, "maximum_serialized_token_budget")
        if completed > 0 and completed % self.configuration.tranche_calls == 0:
            return CheckpointDecision(True, "scheduled_review_tranche")
        return CheckpointDecision(False, None)

    def snapshot(
        self,
        kernel: HostKernel,
        counters: RuntimeCounters,
        *,
        parent_checkpoint_sha256: str | None = None,
        domain_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "configuration": self.configuration.as_dict(),
            "configuration_sha256": self.configuration.sha256,
            "counters": counters.as_dict(),
            "domain_state": None if domain_state is None else dict(domain_state),
            "event_log": kernel.as_dict(),
            "parent_checkpoint_sha256": parent_checkpoint_sha256,
            "schema": "bounded-host-checkpoint-v0",
        }
        return {
            **payload,
            "checkpoint_sha256": sha256_bytes(canonical_json_bytes(payload)),
        }

    def write(
        self,
        path: Path,
        kernel: HostKernel,
        counters: RuntimeCounters,
        *,
        parent_checkpoint_sha256: str | None = None,
        domain_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        value = self.snapshot(
            kernel,
            counters,
            parent_checkpoint_sha256=parent_checkpoint_sha256,
            domain_state=domain_state,
        )
        write_json(path, value)
        return value

    @staticmethod
    def hydrate(
        value: Mapping[str, Any], configuration: RunConfiguration
    ) -> tuple[HostKernel, RuntimeCounters]:
        if value.get("schema") != "bounded-host-checkpoint-v0":
            raise ValueError("unsupported checkpoint schema")
        payload = dict(value)
        observed_hash = str(payload.pop("checkpoint_sha256"))
        if sha256_bytes(canonical_json_bytes(payload)) != observed_hash:
            raise ValueError("checkpoint hash mismatch")
        if value.get("configuration_sha256") != configuration.sha256:
            raise ValueError("checkpoint configuration mismatch")
        kernel = HostKernel.from_dict(value["event_log"])
        counters = RuntimeCounters(
            serialized_tokens=int(value["counters"]["serialized_tokens"]),
            provider_attempts=int(value["counters"]["provider_attempts"]),
        )
        return kernel, counters

    @staticmethod
    def hydrate_with_domain(
        value: Mapping[str, Any], configuration: RunConfiguration
    ) -> tuple[HostKernel, RuntimeCounters, Mapping[str, Any] | None]:
        kernel, counters = CheckpointController.hydrate(value, configuration)
        raw_domain = value.get("domain_state")
        if raw_domain is not None and not isinstance(raw_domain, Mapping):
            raise ValueError("checkpoint domain state must be an object or null")
        return (
            kernel,
            counters,
            None if raw_domain is None else dict(raw_domain),
        )

    @staticmethod
    def read(
        path: Path, configuration: RunConfiguration
    ) -> tuple[HostKernel, RuntimeCounters]:
        return CheckpointController.hydrate(load_json(path), configuration)

    def review_packet(
        self,
        kernel: HostKernel,
        counters: RuntimeCounters,
        composer: PacketComposer,
    ) -> dict[str, Any]:
        state = kernel.project()
        events_by_kind: dict[str, int] = {}
        for event in kernel.events:
            events_by_kind[event.kind.value] = (
                events_by_kind.get(event.kind.value, 0) + 1
            )
        results = []
        for result_id, row in state.results.items():
            results.append(
                {
                    "body_identity": row.result.body_identity.as_dict(),
                    "candidate_sha256_after": row.result.candidate_sha256_after,
                    "delivery_state": row.delivery_state.value,
                    "demand_count": row.demand_count,
                    "first_delivered_call": row.first_delivered_call,
                    "last_delivered_call": row.last_delivered_call,
                    "object_id": row.result.object_id,
                    "object_version": row.result.object_version,
                    "reopen_count": row.reopen_count,
                    "result_id": result_id,
                    "result_kind": row.result.result_kind,
                    "exact_content_sha256": row.result.exact_content_sha256,
                    "exact_content_size_bytes": len(
                        row.result.exact_content.encode("utf-8")
                    ),
                }
            )
        packet = composer.compose(kernel)
        invocation_rows = []
        failed_invocation_rows = []
        action_dispositions = []
        transcript_rows = []
        state_history = []
        for event in kernel.events:
            if event.kind is EventKind.INVOCATION_COMPLETED:
                invocation_rows.append(dict(event.data))
            elif event.kind is EventKind.PROVIDER_FAILED:
                failed_invocation_rows.append(dict(event.data))
            elif event.kind is EventKind.ACTION_DISPOSITION:
                action_dispositions.append(dict(event.data))
            elif event.kind is EventKind.STATE_SLOT_SET:
                value = event.data["state_object"]
                state_history.append(
                    {
                        "content_sha256": value["content_sha256"],
                        "event_id": event.event_id,
                        "object_id": value["object_id"],
                        "object_version": value["object_version"],
                        "slot_id": value["slot_id"],
                    }
                )
        for entry in state.transcript:
            transcript_rows.append(
                {
                    "content_sha256": sha256_bytes(entry.content.encode("utf-8")),
                    "content_size_bytes": len(entry.content.encode("utf-8")),
                    "entry_id": entry.entry_id,
                    "entry_kind": entry.entry_kind,
                    "result_id": entry.result_id,
                    "role": entry.role,
                }
            )
        assistant_hashes = [
            row["content_sha256"]
            for row in transcript_rows
            if row["role"] == "assistant"
        ]
        repeated_assistant_messages = len(assistant_hashes) - len(set(assistant_hashes))
        candidate_events = [
            event
            for event in kernel.events
            if event.kind is EventKind.STATE_SLOT_SET
            and event.data["state_object"]["slot_id"] == "current_candidate"
        ]
        candidate_transitions = []
        for before, after in zip(candidate_events, candidate_events[1:]):
            left = before.data["state_object"]
            right = after.data["state_object"]
            diff = "".join(
                unified_diff(
                    str(left["exact_content"]).splitlines(keepends=True),
                    str(right["exact_content"]).splitlines(keepends=True),
                    fromfile=str(left["object_version"]),
                    tofile=str(right["object_version"]),
                )
            )
            candidate_transitions.append(
                {
                    "from_content_sha256": left["content_sha256"],
                    "from_object_version": left["object_version"],
                    "to_content_sha256": right["content_sha256"],
                    "to_object_version": right["object_version"],
                    "unified_diff": diff,
                }
            )
        provider_usage: dict[str, int | float] = {}
        for invocation in invocation_rows:
            for key, value in dict(invocation.get("usage", {})).items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    provider_usage[key] = provider_usage.get(key, 0) + value
        provider_custody = [
            dict(invocation["provider_custody"])
            for invocation in [*invocation_rows, *failed_invocation_rows]
            if invocation.get("provider_custody")
        ]
        unchanged_candidate_transitions = sum(
            row.get("candidate_sha256_before")
            == row.get("candidate_sha256_after")
            for row in action_dispositions
        )
        return {
            "action_dispositions": action_dispositions,
            "candidate_transitions": candidate_transitions,
            "completed_actor_calls": list(state.completed_calls),
            "configuration_sha256": self.configuration.sha256,
            "counters": counters.as_dict(),
            "event_counts": events_by_kind,
            "event_interval": [1, len(kernel.events)] if kernel.events else [],
            "events_sha256": state.events_sha256,
            "failed_calls": list(state.failed_calls),
            "failed_invocations": failed_invocation_rows,
            "invocations": invocation_rows,
            "next_packet_manifest": packet.manifest_dict(),
            "pending_result_ids": list(state.pending_result_ids),
            "provider_custody": provider_custody,
            "provider_usage": provider_usage,
            "provider_timing": [],
            "recurrence": {
                "exact_repeat_demand_events": events_by_kind.get(
                    EventKind.REPEAT_DEMAND.value, 0
                ),
                "exact_reopen_events": events_by_kind.get(
                    EventKind.REOPEN_REQUESTED.value, 0
                ),
                "repeated_assistant_messages": repeated_assistant_messages,
                "unchanged_candidate_transitions": unchanged_candidate_transitions,
            },
            "resident_result_ids": list(state.resident_result_ids),
            "results": results,
            "state_slots": [
                {
                    "content_sha256": value.content_sha256,
                    "metadata": dict(value.metadata),
                    "object_id": value.object_id,
                    "object_version": value.object_version,
                    "slot_id": slot_id,
                }
                for slot_id, value in sorted(state.state_slots.items())
            ],
            "state_transition_history": state_history,
            "remaining_call_budget": max(
                0,
                self.configuration.maximum_calls - len(state.completed_calls),
            ),
            "remaining_serialized_token_budget": (
                None
                if self.configuration.maximum_serialized_tokens is None
                else max(
                    0,
                    self.configuration.maximum_serialized_tokens
                    - counters.serialized_tokens,
                )
            ),
            "schema": "bounded-host-mechanical-review-v0",
            "semantic_judgment": None,
            "terminal": None if state.terminal is None else state.terminal.value,
            "transcript": transcript_rows,
        }
