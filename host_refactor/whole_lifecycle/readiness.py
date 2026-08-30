from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from reactive_runtime.canonical import load_json, sha256_file


RULE_NAME = "TRELLIS_CLEAN_WHOLE_LIFECYCLE_READINESS_RULE.json"


def adjudicate_readiness(
    repository_root: Path,
    evaluation: Mapping[str, Any],
    *,
    current_candidate_sha256: str,
) -> dict[str, Any]:
    rule_path = repository_root / RULE_NAME
    rule = load_json(rule_path)
    rows = evaluation.get("criterion_results")
    criteria_all_pass = isinstance(rows, list) and bool(rows) and all(
        isinstance(row, Mapping) and row.get("status") == "pass" for row in rows
    )
    blockers = evaluation.get("blocking_requirements")
    candidate_bound = evaluation.get("candidate_sha256") == current_candidate_sha256
    evaluator_bound = evaluation.get("evaluator_id") == rule["evaluator_id"]
    task_bound = evaluation.get("task_id") == rule["task_id"]
    ready = all(
        (
            candidate_bound,
            evaluator_bound,
            task_bound,
            evaluation.get("passed") is True,
            evaluation.get("mechanical_precheck_passed") is True,
            blockers == [],
            criteria_all_pass,
            evaluation.get("external_readiness_adjudication_required") is True,
        )
    )
    return {
        "actor_visible": False,
        "blocking_requirements": [] if ready else ["frozen_acceptance_rule_not_met"],
        "candidate_bound": candidate_bound,
        "candidate_sha256": current_candidate_sha256,
        "closure_readiness": "ready" if ready else "not_ready",
        "criteria_all_pass": criteria_all_pass,
        "evaluator_bound": evaluator_bound,
        "rule_sha256": sha256_file(rule_path),
        "schema": "trellis-clean-whole-lifecycle-readiness-adjudication-v0",
        "submission_used_as_evidence": False,
        "task_bound": task_bound,
    }
