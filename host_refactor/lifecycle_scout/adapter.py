from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from host_refactor.trellis_adapter import TrellisDomainAdapter, TrellisRuntimeSpec
from reactive_runtime.canonical import write_bytes, write_json
from reactive_runtime.diagnostics import (
    RawToolCustody,
    bind_observation_currency,
    parse_evaluator_stdout,
    render_check_projection,
)
from reactive_runtime.keystone_world import KeystoneWorld
from reactive_runtime.world import ExecutionResult


def compact_check_projection(
    evaluation: dict[str, Any],
    *,
    evaluated_candidate_sha256: str,
    raw_result_handle: str,
    returncode: int,
) -> dict[str, Any]:
    passed = evaluation.get("passed")
    if not isinstance(passed, bool):
        raise ValueError("evaluator passed field is not boolean")
    readiness = evaluation.get("closure_readiness")
    if readiness not in {"ready", "not_ready", "not_adjudicated"}:
        raise ValueError("evaluator closure readiness is invalid")
    rows = evaluation.get("criterion_results")
    if not isinstance(rows, list):
        raise ValueError("evaluator criterion results are not a list")
    failures: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("evaluator criterion row is not an object")
        criterion_id = row.get("criterion_id")
        status = row.get("status")
        if not isinstance(criterion_id, str) or not criterion_id:
            raise ValueError("evaluator criterion ID is invalid")
        if criterion_id in seen:
            raise ValueError("evaluator criterion ID is duplicated")
        if status not in {"pass", "fail", "partial", "not_evaluated"}:
            raise ValueError("evaluator criterion status is invalid")
        seen.add(criterion_id)
        if status == "pass":
            continue
        item = {
            "criterion_id": criterion_id,
            "status": str(status),
            "description": str(row.get("description", "criterion did not pass")),
        }
        expected = row.get("expected")
        if isinstance(expected, str) and expected:
            item["expected"] = expected
        failures.append(item)
    evaluator_id = evaluation.get("evaluator_id")
    if not isinstance(evaluator_id, str) or not evaluator_id:
        raise ValueError("evaluator ID is invalid")
    return {
        "blocking_criterion_ids": [row["criterion_id"] for row in failures],
        "closure_readiness": readiness,
        "evaluated_candidate_sha256": evaluated_candidate_sha256,
        "evaluator_id": evaluator_id,
        "failed_criteria": failures,
        "passed": passed,
        "raw_result_handle": raw_result_handle,
        "raw_result_preserved_exactly": True,
        "returncode_class": "zero" if returncode == 0 else "nonzero",
        "schema": "trellis-compact-candidate-bound-check-projection-v0",
        "semantic_repair": False,
        "volatile_fields_excluded": True,
    }


class LifecycleScoutWorld(KeystoneWorld):
    """Trellis world with an exact-raw, bounded actor-visible check projection."""

    def _run_check(self, result_id: str) -> ExecutionResult:
        evaluated = self.candidate_sha256
        evaluator_id = self.evaluator_config["evaluator_id"]
        raw_handle = f"raw-tool://{result_id}/evaluator"
        command = (
            sys.executable,
            str(self.evaluator_script_path),
            str(self.candidate_root),
        )
        process = subprocess.run(
            command,
            cwd=self.task_root,
            capture_output=True,
            check=False,
            timeout=180,
        )
        raw = RawToolCustody(
            command,
            process.returncode,
            "completed",
            process.stdout,
            process.stderr,
            evaluated,
            raw_handle,
        )
        raw_root = self.cell_root / "raw_tool_results" / result_id
        write_bytes(raw_root / "stdout.bin", process.stdout)
        write_bytes(raw_root / "stderr.bin", process.stderr)
        write_json(raw_root / "RAW_TOOL_RECEIPT.json", raw.receipt())
        try:
            evaluation = parse_evaluator_stdout(process.stdout)
            if evaluation.get("candidate_sha256") != evaluated:
                raise ValueError("evaluator candidate hash mismatch")
            projection = compact_check_projection(
                evaluation,
                evaluated_candidate_sha256=evaluated,
                raw_result_handle=raw_handle,
                returncode=process.returncode,
            )
        except ValueError as exc:
            projection = {
                "blocking_criterion_ids": ["evaluator_protocol_error"],
                "closure_readiness": "not_ready",
                "evaluated_candidate_sha256": evaluated,
                "evaluator_id": evaluator_id,
                "failed_criteria": [
                    {
                        "criterion_id": "evaluator_protocol_error",
                        "description": type(exc).__name__,
                        "status": "fail",
                    }
                ],
                "passed": False,
                "raw_result_handle": raw_handle,
                "raw_result_preserved_exactly": True,
                "returncode_class": (
                    "zero" if process.returncode == 0 else "nonzero"
                ),
                "schema": "trellis-compact-candidate-bound-check-projection-v0",
                "semantic_repair": False,
                "volatile_fields_excluded": True,
            }
        self.last_check_projection = projection
        return ExecutionResult(
            "check_observation",
            f"evaluator:{evaluator_id}",
            evaluated,
            render_check_projection(projection),
            self.candidate_sha256,
            evaluated_candidate_sha256=evaluated,
            raw_tool_custody=raw,
            metadata={"check_projection": projection},
        )

    def current_check_binding(self) -> dict[str, Any] | None:
        if self.last_check_projection is None:
            return None
        return bind_observation_currency(
            self.last_check_projection,
            current_candidate_sha256=self.candidate_sha256,
        )


class LifecycleScoutAdapter(TrellisDomainAdapter):
    def __init__(
        self,
        *,
        spec: TrellisRuntimeSpec,
        trajectory_root: Path,
        count_text: Callable[[str], int] | None = None,
    ) -> None:
        self.spec = spec
        self.world = LifecycleScoutWorld(
            spec.paths.task_root,
            trajectory_root,
            count_text=count_text,
        )
        self.next_result_index = 1
