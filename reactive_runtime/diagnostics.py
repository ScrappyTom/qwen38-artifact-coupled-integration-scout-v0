from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

from reactive_runtime.canonical import canonical_json_text, sha256_bytes


READINESS_VALUES = frozenset({"ready", "not_ready", "not_adjudicated"})
CRITERION_STATUS_VALUES = frozenset(
    {
        "pass",
        "fail",
        "met",
        "not_met",
        "partial",
        "not_adjudicated",
        "error",
        "not_observed",
        "skipped",
    }
)


@dataclass(frozen=True)
class RawToolCustody:
    command: tuple[str, ...]
    returncode: int
    execution_status: str
    stdout: bytes
    stderr: bytes
    evaluated_candidate_sha256: str
    raw_result_handle: str

    def receipt(self) -> dict[str, Any]:
        return {
            "command": list(self.command),
            "evaluated_candidate_sha256": self.evaluated_candidate_sha256,
            "execution_status": self.execution_status,
            "raw_result_handle": self.raw_result_handle,
            "returncode": self.returncode,
            "stderr_bytes": len(self.stderr),
            "stderr_sha256": sha256_bytes(self.stderr),
            "stdout_bytes": len(self.stdout),
            "stdout_sha256": sha256_bytes(self.stdout),
        }


def parse_evaluator_stdout(stdout: bytes) -> dict[str, Any]:
    try:
        value = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("evaluator stdout is not one UTF-8 JSON value") from exc
    if not isinstance(value, dict):
        raise ValueError("evaluator stdout must be one JSON object")
    return value


def _require_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"evaluator field {field!r} must be a list of non-empty strings")
    return value


def project_check(
    evaluation: dict[str, Any],
    *,
    evaluated_candidate_sha256: str,
    raw_result_handle: str,
    returncode: int,
    expected_criterion_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Project potentially volatile evaluator output into a stable diagnostic.

    The exact raw stdout/stderr remains separately custodied.  This projection
    intentionally contains no timestamps, UUIDs, temporary paths, or raw
    traceback text.
    """
    passed = evaluation.get("passed")
    if not isinstance(passed, bool):
        raise ValueError("evaluator field 'passed' must be boolean")
    readiness = evaluation.get("closure_readiness", "not_adjudicated")
    if readiness not in READINESS_VALUES:
        raise ValueError("invalid closure_readiness")
    blocking = sorted(set(_require_string_list(evaluation.get("blocking_requirements", []), "blocking_requirements")))
    rows = evaluation.get("criterion_results")
    if not isinstance(rows, list):
        raise ValueError("evaluator field 'criterion_results' must be a list")
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("criterion result must be an object")
        criterion_id = row.get("criterion_id")
        status = row.get("status")
        if not isinstance(criterion_id, str) or not criterion_id:
            raise ValueError("criterion_id must be a non-empty string")
        if criterion_id in seen:
            raise ValueError(f"duplicate criterion_id: {criterion_id}")
        if status not in CRITERION_STATUS_VALUES:
            raise ValueError(f"invalid status for {criterion_id}: {status!r}")
        seen.add(criterion_id)
        item = {"criterion_id": criterion_id, "status": status}
        description = row.get("description")
        if description is not None:
            if not isinstance(description, str):
                raise ValueError(f"description for {criterion_id} must be string")
            item["description"] = description
        normalized.append(item)
    normalized.sort(key=lambda item: item["criterion_id"])

    expected = None if expected_criterion_ids is None else sorted(set(expected_criterion_ids))
    if expected is not None and sorted(seen) != expected:
        raise ValueError(f"criterion identity mismatch: expected {expected}, observed {sorted(seen)}")
    evaluator_id = evaluation.get("evaluator_id", "unspecified-evaluator")
    if not isinstance(evaluator_id, str) or not evaluator_id:
        raise ValueError("evaluator_id must be a non-empty string")

    return {
        "blocking_requirements": blocking,
        "closure_readiness": readiness,
        "criterion_results": normalized,
        "evaluated_candidate_sha256": evaluated_candidate_sha256,
        "evaluator_id": evaluator_id,
        "passed": passed,
        "raw_result_handle": raw_result_handle,
        "raw_result_preserved_exactly": True,
        "returncode_class": "zero" if returncode == 0 else "nonzero",
        "schema": "stable-candidate-bound-check-projection-v1",
        "volatile_fields_excluded": True,
    }


def render_check_projection(projection: dict[str, Any]) -> str:
    return canonical_json_text(projection)


def bind_observation_currency(
    projection: dict[str, Any], *, current_candidate_sha256: str
) -> dict[str, Any]:
    evaluated = projection.get("evaluated_candidate_sha256")
    if not isinstance(evaluated, str):
        raise ValueError("projection lacks evaluated_candidate_sha256")
    bound = dict(projection)
    bound["current_candidate_sha256"] = current_candidate_sha256
    bound["currency"] = "current" if evaluated == current_candidate_sha256 else "stale"
    if evaluated != current_candidate_sha256:
        bound["current_candidate_verification"] = "not_established_by_this_result"
    return bound
