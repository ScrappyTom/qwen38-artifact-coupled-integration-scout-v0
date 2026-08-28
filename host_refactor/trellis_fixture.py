from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from reactive_runtime.canonical import canonical_json_text, sha256_bytes

from host_refactor.kernel import HostKernel
from host_refactor.model import ExactResult, TranscriptEntry
from host_refactor.packet import ModelPacket, PacketComposer


RUN_ID = "2026-08-28-trellis-artifact-centered-pressure-screen-v0"
RESULT_MARKER = "\n--- exact result body ---\n"


def _payload(exact_content: str) -> str:
    if RESULT_MARKER not in exact_content:
        return exact_content
    return exact_content.split(RESULT_MARKER, 1)[1]


def _span_key(metadata: Mapping[str, Any]) -> str:
    segments = metadata.get("segments")
    if isinstance(segments, list):
        normalized = [
            {
                "end_line": row.get("end_line"),
                "source_id": row.get("source_id"),
                "start_line": row.get("start_line"),
            }
            for row in segments
            if isinstance(row, Mapping)
        ]
        return canonical_json_text(normalized)
    if metadata.get("source_id") is not None:
        return canonical_json_text(
            {
                "end_line": metadata.get("end_line"),
                "source_id": metadata.get("source_id"),
                "start_line": metadata.get("start_line"),
            }
        )
    return ""


def historical_result(row: Mapping[str, Any]) -> ExactResult:
    metadata = dict(row.get("metadata", {}))
    return ExactResult(
        result_id=str(row["result_id"]),
        result_kind=str(row["result_kind"]),
        object_id=str(row["object_id"]),
        object_version=str(row["object_version"]),
        exact_content=str(row["exact_content"]),
        payload_content=_payload(str(row["exact_content"])),
        acquired_call=int(row["acquired_call"]),
        candidate_sha256_after=str(row["candidate_sha256_after"]),
        relief_eligible=bool(row["relief_eligible"]),
        evaluated_candidate_sha256=(
            None
            if row.get("evaluated_candidate_sha256") is None
            else str(row["evaluated_candidate_sha256"])
        ),
        raw_result_handle=(
            None
            if row.get("raw_result_handle") is None
            else str(row["raw_result_handle"])
        ),
        span_key=_span_key(metadata),
        metadata=metadata,
    )


def build_e83_kernel(repository_root: Path) -> HostKernel:
    run_root = repository_root / "runs" / RUN_ID
    messages = json.loads(
        (run_root / "FINAL_MESSAGES.json").read_text(encoding="utf-8")
    )
    ledger_value = json.loads(
        (run_root / "RESULT_LEDGER.json").read_text(encoding="utf-8")
    )
    rows = {str(row["result_id"]): row for row in ledger_value["records"]}
    kernel = HostKernel()
    for index, message in enumerate(messages[:4]):
        kernel = kernel.append_transcript(
            TranscriptEntry(
                entry_id=f"E83-MESSAGE-{index:03d}",
                role=str(message["role"]),
                content=str(message["content"]),
            )
        )
    previous_result_id: str | None = None
    for call_index in range(1, 8):
        call_root = run_root / "actor" / f"call-{call_index:03d}"
        assistant_index = 4 + (call_index - 1) * 2
        result_index = assistant_index + 1
        assistant = messages[assistant_index]
        request_bytes = (call_root / "messages.json").read_bytes()
        response_bytes = (call_root / "assistant_content.txt").read_bytes()
        included = () if previous_result_id is None else (previous_result_id,)
        kernel = kernel.complete_invocation(
            call_index=call_index,
            included_result_ids=included,
            request_sha256=sha256_bytes(request_bytes),
            response_sha256=sha256_bytes(response_bytes),
            usage=json.loads((call_root / "RESULT.json").read_text(encoding="utf-8"))[
                "usage"
            ],
        )
        kernel = kernel.append_transcript(
            TranscriptEntry(
                entry_id=f"E83-MESSAGE-{assistant_index:03d}",
                role=str(assistant["role"]),
                content=str(assistant["content"]),
            )
        )
        result_id = f"RESULT-{call_index:03d}"
        result = historical_result(rows[result_id])
        if messages[result_index]["content"] != result.exact_content:
            raise ValueError(f"E83 result/message mismatch: {result_id}")
        kernel = kernel.acquire(result)
        kernel = kernel.schedule(
            result_id,
            call_index=call_index + 1,
            transcript_entry_id=f"E83-MESSAGE-{result_index:03d}",
        )
        previous_result_id = result_id
    return kernel


def e83_packet(repository_root: Path) -> ModelPacket:
    return PacketComposer().compose(build_e83_kernel(repository_root))


def complete_e83_pending(repository_root: Path) -> HostKernel:
    kernel = build_e83_kernel(repository_root)
    packet = PacketComposer().compose(kernel)
    kernel = kernel.complete_invocation(
        call_index=8,
        included_result_ids=("RESULT-007",),
        request_sha256=packet.sha256,
        response_sha256=sha256_bytes(b"{}"),
        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    )
    return kernel.append_transcript(
        TranscriptEntry(
            entry_id="E83-SYNTHETIC-ASSISTANT-008",
            role="assistant",
            content="{}",
        )
    )


def delivered_source_ids(kernel: HostKernel) -> tuple[str, ...]:
    state = kernel.project()
    values: set[str] = set()
    for row in state.results.values():
        if row.first_delivered_call is None:
            continue
        source_ids = row.result.metadata.get("source_ids", [])
        if isinstance(source_ids, list):
            values.update(str(value) for value in source_ids)
    return tuple(sorted(values))


def pending_source_ids(kernel: HostKernel) -> tuple[str, ...]:
    state = kernel.project()
    values: set[str] = set()
    for result_id in state.pending_result_ids:
        source_ids = state.results[result_id].result.metadata.get("source_ids", [])
        if isinstance(source_ids, list):
            values.update(str(value) for value in source_ids)
    return tuple(sorted(values))
