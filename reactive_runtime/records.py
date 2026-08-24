from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from reactive_runtime.canonical import canonical_json_text, sha256_bytes


def wrap_action_result(
    *,
    result_id: str,
    result_kind: str,
    object_id: str,
    object_version: str,
    body: str,
) -> str:
    """Create the exact, model-visible result body kept in external custody."""
    header = canonical_json_text(
        {
            "object_id": object_id,
            "object_version": object_version,
            "result_id": result_id,
            "result_kind": result_kind,
            "schema": "ceiba-action-result-v1",
        }
    )
    return f"{header}\n--- exact result body ---\n{body}"


@dataclass
class ResultRecord:
    result_id: str
    result_kind: str
    object_id: str
    object_version: str
    exact_content: str
    acquired_call: int
    candidate_sha256_after: str
    first_model_visible_call: int | None = None
    message_index: int | None = None
    resident: bool = False
    relief_eligible: bool = True
    evaluated_candidate_sha256: str | None = None
    raw_result_handle: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def content_bytes(self) -> bytes:
        return self.exact_content.encode("utf-8")

    @property
    def content_sha256(self) -> str:
        return sha256_bytes(self.content_bytes)

    @property
    def size_bytes(self) -> int:
        return len(self.content_bytes)

    @property
    def previously_visible(self) -> bool:
        return self.first_model_visible_call is not None

    def receipt(self) -> str:
        if not self.previously_visible:
            raise ValueError(f"undelivered result cannot become a receipt: {self.result_id}")
        source_id = self.metadata.get("source_id")
        segments = self.metadata.get("segments")
        batch = isinstance(segments, list)
        source_ids = self.metadata.get("source_ids") if batch else None
        if batch and not isinstance(source_ids, list):
            source_ids = []
        observed_ranges = (
            [
                {
                    "end_line": row.get("end_line"),
                    "source_id": row.get("source_id"),
                    "start_line": row.get("start_line"),
                }
                for row in segments
                if isinstance(row, dict)
            ]
            if batch
            else None
        )
        observed_range = None
        if not batch and source_id is not None:
            observed_range = {
                "start_line": self.metadata.get("start_line"),
                "end_line": self.metadata.get("end_line"),
            }
        value: dict[str, Any] = {
            "delivery_ordinal": self.first_model_visible_call,
            "exact_result_sha256": self.content_sha256,
            "exact_result_size_bytes": self.size_bytes,
            "object_id": self.object_id,
            "object_version": self.object_version,
            "observed_range": observed_range,
            "previously_model_visible": True,
            "reopen_handle": f"result://sha256/{self.content_sha256}",
            "reopen_action": {"action": "reopen_exact", "result_id": self.result_id},
            "resident": False,
            "result_id": self.result_id,
            "result_kind": self.result_kind,
            "schema_version": "ceiba-exact-result-receipt-v1",
            "source_id": source_id,
            "source_path": self.metadata.get("source_path"),
            "source_sha256": self.metadata.get("source_sha256"),
            "source_size_bytes": self.metadata.get("source_size_bytes"),
        }
        if batch:
            value.pop("observed_range")
            value.update(
                {
                    "observed_ranges": observed_ranges,
                    "source_ids": source_ids,
                    "total_source_bytes": self.metadata.get("total_source_bytes"),
                }
            )
        return canonical_json_text(value)

    def as_dict(self, *, include_exact_content: bool = False) -> dict[str, Any]:
        value: dict[str, Any] = {
            "acquired_call": self.acquired_call,
            "candidate_sha256_after": self.candidate_sha256_after,
            "content_sha256": self.content_sha256,
            "evaluated_candidate_sha256": self.evaluated_candidate_sha256,
            "first_model_visible_call": self.first_model_visible_call,
            "message_index": self.message_index,
            "metadata": self.metadata,
            "object_id": self.object_id,
            "object_version": self.object_version,
            "raw_result_handle": self.raw_result_handle,
            "relief_eligible": self.relief_eligible,
            "resident": self.resident,
            "result_id": self.result_id,
            "result_kind": self.result_kind,
            "size_bytes": self.size_bytes,
        }
        if include_exact_content:
            value["exact_content"] = self.exact_content
        return value


class ResultLedger:
    """Ordered exact-result custody with explicit delivery and residency state."""

    def __init__(self) -> None:
        self._records: dict[str, ResultRecord] = {}

    def __contains__(self, result_id: str) -> bool:
        return result_id in self._records

    def __len__(self) -> int:
        return len(self._records)

    def add(self, record: ResultRecord) -> None:
        if record.result_id in self._records:
            raise ValueError(f"duplicate result id: {record.result_id}")
        self._records[record.result_id] = record

    def get(self, result_id: str) -> ResultRecord:
        try:
            return self._records[result_id]
        except KeyError as exc:
            raise KeyError(f"unknown result id: {result_id}") from exc

    def records(self) -> tuple[ResultRecord, ...]:
        return tuple(self._records.values())

    def mark_model_visible(
        self,
        result_id: str,
        *,
        call_index: int,
        message_index: int | None,
    ) -> None:
        record = self.get(result_id)
        if record.first_model_visible_call is None:
            record.first_model_visible_call = call_index
        record.message_index = message_index
        record.resident = message_index is not None

    def mark_external(self, result_id: str) -> None:
        record = self.get(result_id)
        record.resident = False
        record.message_index = None

    def exact_reopen(self, result_id: str) -> ResultRecord:
        record = self.get(result_id)
        if not record.previously_visible:
            raise ValueError(f"result did not cross a model boundary: {result_id}")
        if record.resident or record.message_index is not None:
            raise ValueError(f"result remains resident and cannot be reopened: {result_id}")
        return record

    def eligible(self, *, kinds: Iterable[str] | None = None) -> tuple[ResultRecord, ...]:
        selected_kinds = None if kinds is None else frozenset(kinds)
        selected = tuple(
            record
            for record in self._records.values()
            if record.previously_visible
            and record.resident
            and record.relief_eligible
            and record.message_index is not None
            and (selected_kinds is None or record.result_kind in selected_kinds)
        )
        return tuple(
            sorted(
                selected,
                key=lambda record: (
                    int(record.first_model_visible_call),
                    record.result_id,
                ),
            )
        )

    def as_dict(self, *, include_exact_content: bool = False) -> dict[str, Any]:
        return {
            "schema": "ceiba-result-ledger-v1",
            "records": [
                record.as_dict(include_exact_content=include_exact_content)
                for record in self._records.values()
            ],
        }
