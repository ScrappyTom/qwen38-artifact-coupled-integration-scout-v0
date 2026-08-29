from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from reactive_runtime.canonical import (
    canonical_json_bytes,
    canonical_json_text,
    sha256_bytes,
)

from host_refactor.kernel import HostKernel, InvalidTransition
from host_refactor.model import DeliveryState, ExactResult


@dataclass(frozen=True)
class PacketManifestEntry:
    transcript_entry_id: str
    role: str
    representation: str
    message_index: int
    result_id: str | None = None
    canonical_body_identity: Mapping[str, str] | None = None
    state_slot_id: str | None = None
    content_sha256: str | None = None
    object_id: str | None = None
    object_version: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "canonical_body_identity": (
                None
                if self.canonical_body_identity is None
                else dict(self.canonical_body_identity)
            ),
            "content_sha256": self.content_sha256,
            "message_index": self.message_index,
            "object_id": self.object_id,
            "object_version": self.object_version,
            "representation": self.representation,
            "result_id": self.result_id,
            "role": self.role,
            "state_slot_id": self.state_slot_id,
            "transcript_entry_id": self.transcript_entry_id,
        }


@dataclass(frozen=True)
class ModelPacket:
    messages: tuple[Mapping[str, str], ...]
    manifest: tuple[PacketManifestEntry, ...]
    state_sha256: str

    def message_list(self) -> list[dict[str, str]]:
        return [dict(message) for message in self.messages]

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.message_list())

    @property
    def sha256(self) -> str:
        return sha256_bytes(self.canonical_bytes)

    def manifest_dict(self) -> dict[str, Any]:
        return {
            "entries": [row.as_dict() for row in self.manifest],
            "message_count": len(self.messages),
            "packet_sha256": self.sha256,
            "schema": "bounded-host-packet-manifest-v0",
            "state_sha256": self.state_sha256,
        }

    @property
    def manifest_sha256(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.manifest_dict()))


def exact_receipt(result: ExactResult) -> str:
    metadata = dict(result.metadata)
    return canonical_json_text(
        {
            "canonical_body_identity": result.body_identity.as_dict(),
            "exact_result_sha256": result.exact_content_sha256,
            "object_id": result.object_id,
            "object_version": result.object_version,
            "observed_ranges": metadata.get("segments"),
            "previously_model_visible": True,
            "reopen_action": {"action": "reopen_exact", "result_id": result.result_id},
            "reopen_handle": f"result://sha256/{result.exact_content_sha256}",
            "resident": False,
            "result_id": result.result_id,
            "result_kind": result.result_kind,
            "schema": "bounded-host-exact-result-receipt-v0",
        }
    )


def applied_candidate_effect_receipt(result: ExactResult) -> str:
    """Render compact model-facing custody for an applied candidate effect."""

    return canonical_json_text(
        {
            "candidate_sha256_after": result.candidate_sha256_after,
            "exact_result_sha256": result.exact_content_sha256,
            "reopen_action": {
                "action": "reopen_exact",
                "result_id": result.result_id,
            },
            "result_id": result.result_id,
            "schema": "bounded-host-applied-candidate-effect-receipt-v0",
        }
    )


def duplicate_suppression(result: ExactResult, resident_result_id: str) -> str:
    return canonical_json_text(
        {
            "canonical_body_identity": result.body_identity.as_dict(),
            "resident_result_id": resident_result_id,
            "schema": "bounded-host-duplicate-suppressed-v0",
            "suppressed_result_id": result.result_id,
            "status": "exact_body_already_rendered",
        }
    )


class PacketComposer:
    """Pure model-packet projection from the authoritative event kernel."""

    def compose(self, kernel: HostKernel) -> ModelPacket:
        state = kernel.project()
        messages: list[Mapping[str, str]] = []
        manifest: list[PacketManifestEntry] = []
        rendered_bodies: dict[object, str] = {}
        for entry in state.transcript:
            content = entry.content
            representation = entry.entry_kind
            body_identity: Mapping[str, str] | None = None
            object_id: str | None = None
            object_version: str | None = None
            if entry.state_slot_id is not None:
                try:
                    state_object = state.state_slots[entry.state_slot_id]
                except KeyError as exc:
                    raise InvalidTransition(
                        f"transcript references unknown state slot: {entry.state_slot_id}"
                    ) from exc
                content = state_object.exact_content
                representation = "current_exact_state"
                object_id = state_object.object_id
                object_version = state_object.object_version
            if entry.result_id is not None:
                try:
                    projected = state.results[entry.result_id]
                except KeyError as exc:
                    raise InvalidTransition(
                        f"transcript references unknown result: {entry.result_id}"
                    ) from exc
                result = projected.result
                body_identity = result.body_identity.as_dict()
                object_id = result.object_id
                object_version = result.object_version
                if projected.delivery_state is DeliveryState.ACQUIRED:
                    raise InvalidTransition(
                        f"acquired result cannot have model-facing entry: {entry.result_id}"
                    )
                if (
                    projected.delivery_state is DeliveryState.DELIVERED_EXTERNAL
                    or entry.entry_id != projected.transcript_entry_id
                ):
                    if (
                        projected.delivery_state is DeliveryState.DELIVERED_EXTERNAL
                        and result.result_kind == "candidate_effect"
                    ):
                        content = applied_candidate_effect_receipt(result)
                        representation = "applied_candidate_effect_receipt"
                    else:
                        content = exact_receipt(result)
                        representation = "exact_receipt"
                else:
                    identity = result.body_identity
                    prior = rendered_bodies.get(identity)
                    if prior is None:
                        rendered_bodies[identity] = result.result_id
                        content = result.exact_content
                        representation = (
                            "pending_exact_body"
                            if projected.delivery_state is DeliveryState.PENDING
                            else "resident_exact_body"
                        )
                    else:
                        content = duplicate_suppression(result, prior)
                        representation = "duplicate_exact_body_suppressed"
            message_index = len(messages)
            messages.append({"role": entry.role, "content": content})
            manifest.append(
                PacketManifestEntry(
                    transcript_entry_id=entry.entry_id,
                    role=entry.role,
                    representation=representation,
                    message_index=message_index,
                    result_id=entry.result_id,
                    canonical_body_identity=body_identity,
                    content_sha256=sha256_bytes(content.encode("utf-8")),
                    object_id=object_id,
                    object_version=object_version,
                    state_slot_id=entry.state_slot_id,
                )
            )
        currentness = self._currentness_message(kernel)
        if currentness is not None:
            message_index = len(messages)
            messages.append({"role": "user", "content": currentness})
            manifest.append(
                PacketManifestEntry(
                    transcript_entry_id="MECHANICAL-CHECK-CURRENTNESS",
                    role="user",
                    representation="mechanical_check_currentness",
                    message_index=message_index,
                    content_sha256=sha256_bytes(currentness.encode("utf-8")),
                )
            )
        self._validate_active_body_uniqueness(kernel, manifest)
        return ModelPacket(
            messages=tuple(messages),
            manifest=tuple(manifest),
            state_sha256=state.events_sha256,
        )

    @staticmethod
    def _validate_active_body_uniqueness(
        kernel: HostKernel, manifest: list[PacketManifestEntry]
    ) -> None:
        state = kernel.project()
        active: set[tuple[tuple[str, str], ...]] = set()
        for row in manifest:
            if row.representation not in {
                "pending_exact_body",
                "resident_exact_body",
            }:
                continue
            if row.result_id is None:
                raise InvalidTransition("exact-body manifest entry lacks result id")
            result = state.results[row.result_id].result
            identity = tuple(sorted(result.body_identity.as_dict().items()))
            if identity in active:
                raise InvalidTransition("duplicate canonical exact body rendered")
            active.add(identity)

    @staticmethod
    def _currentness_message(kernel: HostKernel) -> str | None:
        state = kernel.project()
        checks = [
            row
            for row in state.results.values()
            if row.result.evaluated_candidate_sha256 is not None
            and row.first_delivered_call is not None
        ]
        if not checks:
            return None
        latest = max(
            checks,
            key=lambda row: (row.result.acquired_call, row.result.result_id),
        )
        candidate_slot = state.state_slots.get("current_candidate")
        current_candidate = (
            None
            if candidate_slot is None
            else candidate_slot.metadata.get("candidate_sha256")
        )
        evaluated = latest.result.evaluated_candidate_sha256
        currency = (
            "unknown"
            if current_candidate is None
            else "current"
            if evaluated == current_candidate
            else "stale"
        )
        return canonical_json_text(
            {
                "current_candidate_sha256": current_candidate,
                "currency": currency,
                "delivery_state": latest.delivery_state.value,
                "evaluated_candidate_sha256": evaluated,
                "result_id": latest.result.result_id,
                "schema": "bounded-host-current-check-binding-v0",
            }
        )
