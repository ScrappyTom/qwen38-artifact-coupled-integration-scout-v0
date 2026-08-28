from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from reactive_runtime.canonical import canonical_json_bytes, sha256_bytes

from host_refactor.packet import ModelPacket


class RequestBindingError(ValueError):
    """The final provider request does not preserve the composed packet."""


@dataclass(frozen=True)
class RequestBinding:
    packet_sha256: str
    packet_manifest_sha256: str
    provider_messages_sha256: str
    final_request_sha256: str
    included_result_ids: tuple[str, ...]
    state_slot_exposures: tuple[Mapping[str, Any], ...]

    @classmethod
    def bind(
        cls,
        packet: ModelPacket,
        payload: Mapping[str, Any],
        *,
        expected_max_tokens: int,
    ) -> "RequestBinding":
        if payload.get("max_tokens") != expected_max_tokens:
            raise RequestBindingError(
                "provider maximum completion tokens differ from frozen reserve"
            )
        raw_messages = payload.get("messages")
        if not isinstance(raw_messages, Sequence) or isinstance(
            raw_messages, (str, bytes)
        ):
            raise RequestBindingError("provider payload lacks a message sequence")
        messages: list[dict[str, str]] = []
        for index, row in enumerate(raw_messages):
            if not isinstance(row, Mapping):
                raise RequestBindingError(
                    f"provider message {index} is not an object"
                )
            role = row.get("role")
            content = row.get("content")
            if not isinstance(role, str) or not isinstance(content, str):
                raise RequestBindingError(
                    f"provider message {index} lacks exact role/content"
                )
            if set(row) != {"role", "content"}:
                raise RequestBindingError(
                    f"provider message {index} contains undeclared fields"
                )
            messages.append({"role": role, "content": content})
        if messages != packet.message_list():
            raise RequestBindingError(
                "provider messages differ from the composed packet"
            )
        included_result_ids = tuple(
            row.result_id
            for row in packet.manifest
            if row.representation == "pending_exact_body"
            and row.result_id is not None
        )
        state_slot_exposures = tuple(
            {
                "content_sha256": row.content_sha256,
                "message_index": row.message_index,
                "object_id": row.object_id,
                "object_version": row.object_version,
                "representation": row.representation,
                "state_slot_id": row.state_slot_id,
            }
            for row in packet.manifest
            if row.state_slot_id is not None
            and row.representation == "current_exact_state"
        )
        return cls(
            packet_sha256=packet.sha256,
            packet_manifest_sha256=packet.manifest_sha256,
            provider_messages_sha256=sha256_bytes(canonical_json_bytes(messages)),
            final_request_sha256=sha256_bytes(canonical_json_bytes(dict(payload))),
            included_result_ids=included_result_ids,
            state_slot_exposures=state_slot_exposures,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "final_request_sha256": self.final_request_sha256,
            "included_result_ids": list(self.included_result_ids),
            "packet_manifest_sha256": self.packet_manifest_sha256,
            "packet_sha256": self.packet_sha256,
            "provider_messages_sha256": self.provider_messages_sha256,
            "state_slot_exposures": [dict(row) for row in self.state_slot_exposures],
        }
