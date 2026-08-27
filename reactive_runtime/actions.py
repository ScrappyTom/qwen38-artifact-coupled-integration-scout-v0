from __future__ import annotations

import json
from typing import Any, Iterable

from reactive_runtime.canonical import canonical_json_text


MAX_READ_LINES = 120
MAX_BATCH_RANGES = 2
MAX_BATCH_TOTAL_LINES = 160
MAX_BATCH_SOURCE_BYTES = 12_000
# Applies to every newly acquired source observation, whether it was requested
# through read_source or read_batch.  A result-object count is deliberately not
# part of pressure eligibility because one object may contain one or two ranges.
MAX_SOURCE_RESULT_TOKENS = 6_500
# Historical import name retained for the measured runner and old receipts.
MAX_BATCH_RESULT_TOKENS = MAX_SOURCE_RESULT_TOKENS
MAX_ARTIFACT_BYTES = 250_000
MAX_PATCH_EDITS = 24
MAX_PATCH_OLD_BYTES = 2_000
MAX_PATCH_NEW_BYTES = 12_000

DECISION_HEADINGS = (
    "Decision, scope, and authority",
    "Hazard triggers and zone sequencing",
    "Population, transport, and route clearance",
    "Shelter, medical, and accessibility continuity",
    "Warnings, accountability, and community support",
    "Power, fuel, and resource contracting",
    "Forty-eight-hour execution and contingencies",
    "Verification, readiness, blockers, and falsifiers",
)

ACTION_FIELDS: dict[str, dict[str, type]] = {
    "read_source": {"source_id": str, "start_line": int, "end_line": int},
    "read_batch": {"requests": list},
    "reopen_exact": {"result_id": str},
    "replace_evidence_ledger": {"content": str},
    "upsert_evidence_slot": {"source_id": str, "source_version": str, "content": str},
    "upsert_decision_section": {"heading": str, "body": str},
    "patch_decision": {"edits": list},
    "replace_decision": {"content": str},
    "run_check": {},
    "submit": {},
}


def render_action_rejection(
    *, call_index: int, code: str, message: str, candidate_sha256: str
) -> str:
    return canonical_json_text(
        {
            "call_index": call_index,
            "candidate_sha256": candidate_sha256,
            "code": code,
            "message": message,
            "repaired": False,
            "schema": "architecture-action-rejection-v0",
        }
    )


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key: {key}")
        value[key] = item
    return value


def _validate_range(request: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError(f"{label} must be an object")
    expected = {"source_id", "start_line", "end_line"}
    if set(request) != expected:
        raise ValueError(f"{label} fields must be exactly {sorted(expected)}")
    source_id, start, end = (
        request["source_id"], request["start_line"], request["end_line"]
    )
    if not isinstance(source_id, str) or not source_id:
        raise ValueError(f"{label}.source_id must be a non-empty string")
    if type(start) is not int or type(end) is not int:
        raise ValueError(f"{label} bounds must be integers")
    if start < 1 or end < start or end - start + 1 > MAX_READ_LINES:
        raise ValueError(f"{label} must contain 1..{MAX_READ_LINES} lines")
    return request


def parse_action(
    content: str,
    allowed: Iterable[str],
    *,
    decision_headings: Iterable[str] = DECISION_HEADINGS,
) -> dict[str, Any]:
    value = json.loads(content, parse_constant=_reject_constant, object_pairs_hook=_unique_object)
    if not isinstance(value, dict) or not isinstance(value.get("action"), str):
        raise ValueError("assistant content is not one action object")
    action = value["action"]
    if action not in frozenset(allowed):
        raise ValueError(f"action {action!r} is not currently allowed")
    fields = ACTION_FIELDS[action]
    expected = {"action", *fields}
    if set(value) != expected:
        raise ValueError(f"fields for {action} must be exactly {sorted(expected)}")
    if action == "read_batch":
        requests = value["requests"]
        if not isinstance(requests, list) or not 1 <= len(requests) <= MAX_BATCH_RANGES:
            raise ValueError(f"read_batch must contain 1..{MAX_BATCH_RANGES} ranges")
        rows = [_validate_range(row, label=f"requests[{i}]") for i, row in enumerate(requests)]
        if sum(row["end_line"] - row["start_line"] + 1 for row in rows) > MAX_BATCH_TOTAL_LINES:
            raise ValueError(f"read_batch may contain at most {MAX_BATCH_TOTAL_LINES} lines")
        for i, left in enumerate(rows):
            for right in rows[i + 1 :]:
                if left["source_id"] == right["source_id"] and not (
                    left["end_line"] < right["start_line"]
                    or right["end_line"] < left["start_line"]
                ):
                    raise ValueError("same-source batch ranges may not overlap")
        return value
    if action == "patch_decision":
        edits = value["edits"]
        if not isinstance(edits, list) or not 1 <= len(edits) <= MAX_PATCH_EDITS:
            raise ValueError(f"patch_decision must contain 1..{MAX_PATCH_EDITS} edits")
        total_new = 0
        for index, edit in enumerate(edits):
            if not isinstance(edit, dict) or set(edit) != {"old", "new"}:
                raise ValueError(f"edits[{index}] fields must be exactly ['new', 'old']")
            old, new = edit["old"], edit["new"]
            if not isinstance(old, str) or not old:
                raise ValueError(f"edits[{index}].old must be a non-empty string")
            if not isinstance(new, str):
                raise ValueError(f"edits[{index}].new must be a string")
            if len(old.encode("utf-8")) > MAX_PATCH_OLD_BYTES:
                raise ValueError(f"edits[{index}].old exceeds {MAX_PATCH_OLD_BYTES} bytes")
            total_new += len(new.encode("utf-8"))
        if total_new > MAX_PATCH_NEW_BYTES:
            raise ValueError(f"patch_decision new text exceeds {MAX_PATCH_NEW_BYTES} bytes")
        return value
    for field, expected_type in fields.items():
        observed = value[field]
        if expected_type is int and isinstance(observed, bool):
            raise ValueError(f"{field} must be int")
        if not isinstance(observed, expected_type):
            raise ValueError(f"{field} must be {expected_type.__name__}")
        if expected_type is str and not observed:
            raise ValueError(f"{field} must be non-empty")
    if action == "read_source":
        _validate_range({key: value[key] for key in ("source_id", "start_line", "end_line")}, label=action)
    if action == "upsert_decision_section" and value["heading"] not in tuple(decision_headings):
        raise ValueError("heading is not a declared decision section")
    if action in {"replace_evidence_ledger", "replace_decision", "upsert_evidence_slot"}:
        size = len(value["content"].encode("utf-8"))
        if not 1 <= size <= MAX_ARTIFACT_BYTES:
            raise ValueError(f"artifact content must contain 1..{MAX_ARTIFACT_BYTES} bytes")
    return value


def _range_properties(sources: list[str]) -> dict[str, Any]:
    return {
        "source_id": {"type": "string", "enum": sources},
        "start_line": {"type": "integer", "minimum": 1},
        "end_line": {"type": "integer", "minimum": 1},
    }


def action_json_schema(
    allowed: Iterable[str],
    *,
    source_ids: Iterable[str],
    reopen_result_ids: Iterable[str],
    decision_headings: Iterable[str] = DECISION_HEADINGS,
    schema_name: str = "cedar_actor_action_v0",
) -> dict[str, Any]:
    sources = sorted(set(source_ids))
    reopen = sorted(set(reopen_result_ids))
    alternatives: list[dict[str, Any]] = []
    for action in allowed:
        if action == "reopen_exact" and not reopen:
            continue
        properties: dict[str, Any] = {"action": {"type": "string", "const": action}}
        required = ["action"]
        if action == "read_batch":
            properties["requests"] = {
                "type": "array",
                "minItems": 1,
                "maxItems": MAX_BATCH_RANGES,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": _range_properties(sources),
                    "required": ["source_id", "start_line", "end_line"],
                },
            }
            required.append("requests")
        elif action == "patch_decision":
            properties["edits"] = {
                "type": "array",
                "minItems": 1,
                "maxItems": MAX_PATCH_EDITS,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "old": {"type": "string", "minLength": 1},
                        "new": {"type": "string"},
                    },
                    "required": ["old", "new"],
                },
            }
            required.append("edits")
        else:
            for field, kind in ACTION_FIELDS[action].items():
                rule: dict[str, Any] = {"type": "integer" if kind is int else "string"}
                if kind is str:
                    rule["minLength"] = 1
                if field == "source_id":
                    rule["enum"] = sources
                if field == "result_id":
                    rule["enum"] = reopen
                if field == "heading":
                    rule["enum"] = list(decision_headings)
                if field in {"start_line", "end_line"}:
                    rule["minimum"] = 1
                properties[field] = rule
                required.append(field)
        alternatives.append(
            {
                "type": "object",
                "additionalProperties": False,
                "properties": properties,
                "required": required,
            }
        )
    if not alternatives:
        raise ValueError("no currently reachable actions")
    return {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "strict": True,
            "schema": {"oneOf": alternatives},
        },
    }
