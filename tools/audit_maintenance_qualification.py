from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json
from reactive_runtime.seal import verify_tree_seal


RUN_ID = "2026-08-24-artifact-coupled-maintenance-expression-qualification-v0"
FREEZE_COMMIT = "7d71c7d666403da7f0be9494a77a771435144f69"
EXPECTED_CASES = (
    "Q1_INITIALIZE",
    "Q2_REPLACE",
    "Q3_INCREMENTAL_SECTION_ACTION",
    "Q4_TASK_LEDGER_ACTION",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def audit(repository_root: Path = ROOT) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    run_root = repository_root / "qualification_runs" / RUN_ID
    failures: list[str] = []

    required = (
        "AUTHORIZATION_RECEIPT.json",
        "FINALIZATION.json",
        "QUALIFICATION_RESULT.json",
        "RUN_SEAL.json",
        "RUNTIME_ASSET_VERIFICATION.json",
        "model/RUNTIME_GATE.json",
        "model/RUNTIME_RELEASE.json",
    )
    for relative in required:
        if not (run_root / relative).is_file():
            failures.append(f"missing:{relative}")
    if failures:
        return {
            "schema": "artifact-coupled-maintenance-expression-audit-v0",
            "passed": False,
            "failures": failures,
            "run_id": RUN_ID,
        }

    seal_errors = list(verify_tree_seal(run_root, run_root / "RUN_SEAL.json"))
    failures.extend(f"seal:{item}" for item in seal_errors)

    result = load_json(run_root / "QUALIFICATION_RESULT.json")
    authorization = load_json(run_root / "AUTHORIZATION_RECEIPT.json")
    finalization = load_json(run_root / "FINALIZATION.json")
    runtime_gate = load_json(run_root / "model" / "RUNTIME_GATE.json")
    runtime_release = load_json(run_root / "model" / "RUNTIME_RELEASE.json")
    assets = load_json(run_root / "RUNTIME_ASSET_VERIFICATION.json")

    expected_result = {
        "run_id": RUN_ID,
        "freeze_commit": FREEZE_COMMIT,
        "model_calls": 4,
        "passed": True,
        "measured_actor_authorized": False,
    }
    for key, expected in expected_result.items():
        if result.get(key) != expected:
            failures.append(f"result:{key}_mismatch")

    if authorization.get("authorized") is not True:
        failures.append("authorization:not_authorized")
    if authorization.get("authorized_freeze_commit") != FREEZE_COMMIT:
        failures.append("authorization:freeze_commit_mismatch")
    if authorization.get("authorized_run_id") != RUN_ID:
        failures.append("authorization:run_id_mismatch")
    if authorization.get("maximum_model_calls") != 4:
        failures.append("authorization:call_ceiling_mismatch")
    if authorization.get("attempts_per_call") != 1 or authorization.get("retries") != 0:
        failures.append("authorization:attempt_policy_mismatch")

    if runtime_gate.get("passed") is not True:
        failures.append("runtime_gate:not_passed")
    if assets.get("passed") is not True:
        failures.append("runtime_assets:not_passed")
    if runtime_release.get("released") is not True:
        failures.append("runtime_release:not_released")
    if finalization.get("failure") is not None:
        failures.append("finalization:failure_present")
    if finalization.get("release", {}).get("released") is not True:
        failures.append("finalization:release_not_qualified")
    if (run_root / "RUN_FAILURE.json").exists():
        failures.append("run_failure:present")

    rows = result.get("cases")
    if not isinstance(rows, list):
        rows = []
        failures.append("result:cases_not_list")
    case_ids = tuple(row.get("case_id") for row in rows if isinstance(row, dict))
    if case_ids != EXPECTED_CASES:
        failures.append("result:case_order_mismatch")

    total_prompt = 0
    total_completion = 0
    total_serialized = 0
    for row in rows:
        if not isinstance(row, dict):
            failures.append("result:case_not_object")
            continue
        case_id = str(row.get("case_id"))
        if row.get("accepted") is not True:
            failures.append(f"case:{case_id}:not_accepted")
        if row.get("finish_reason") != "stop":
            failures.append(f"case:{case_id}:finish_reason_not_stop")
        usage = row.get("usage")
        if not isinstance(usage, dict):
            failures.append(f"case:{case_id}:usage_missing")
            continue
        prompt = usage.get("prompt_tokens")
        completion = usage.get("completion_tokens")
        total = usage.get("total_tokens")
        if not all(isinstance(item, int) and item >= 0 for item in (prompt, completion, total)):
            failures.append(f"case:{case_id}:usage_invalid")
            continue
        if prompt + completion != total:
            failures.append(f"case:{case_id}:usage_arithmetic")
        total_prompt += prompt
        total_completion += completion
        total_serialized += total
        if case_id in EXPECTED_CASES[:2]:
            validation = row.get("validation")
            if not isinstance(validation, dict) or validation.get("valid") is not True:
                failures.append(f"case:{case_id}:maintenance_validation")
            elif not isinstance(validation.get("output_tokens"), int) or validation["output_tokens"] > 1600:
                failures.append(f"case:{case_id}:maintenance_budget")
        else:
            parsed = row.get("parsed_action")
            if not isinstance(parsed, dict) or parsed.get("action") != row.get("required_action"):
                failures.append(f"case:{case_id}:action_mismatch")
            if row.get("error") is not None:
                failures.append(f"case:{case_id}:parse_error")

    attempt_roots = sorted(run_root.glob("calls/*/provider_attempt"))
    if len(attempt_roots) != 4:
        failures.append(f"provider_attempts:{len(attempt_roots)}")
    for attempt_root in attempt_roots:
        receipt_path = attempt_root / "PROVIDER_CALL_RECEIPT.json"
        if not receipt_path.is_file():
            failures.append(f"provider_receipt_missing:{attempt_root.relative_to(run_root).as_posix()}")
            continue
        receipt = load_json(receipt_path)
        if receipt.get("attempted") is not True:
            failures.append(f"provider_not_attempted:{attempt_root.relative_to(run_root).as_posix()}")
        if receipt.get("outcome") != "valid_completion_response":
            failures.append(f"provider_outcome:{attempt_root.relative_to(run_root).as_posix()}")
        if receipt.get("completion_response_valid") is not True:
            failures.append(f"provider_completion_invalid:{attempt_root.relative_to(run_root).as_posix()}")

    return {
        "schema": "artifact-coupled-maintenance-expression-audit-v0",
        "run_id": RUN_ID,
        "freeze_commit": FREEZE_COMMIT,
        "passed": not failures,
        "failures": failures,
        "seal_verified": not seal_errors,
        "model_calls": len(rows),
        "provider_attempts": len(attempt_roots),
        "attempts_per_call": 1,
        "retries": 0,
        "case_order": list(case_ids),
        "all_cases_accepted": bool(rows) and all(
            isinstance(row, dict) and row.get("accepted") is True for row in rows
        ),
        "prompt_tokens": total_prompt,
        "completion_tokens": total_completion,
        "serialized_tokens": total_serialized,
        "runtime_gate_passed": runtime_gate.get("passed") is True,
        "runtime_released": runtime_release.get("released") is True,
        "measured_actor_authorized": False,
        "qualification_result_sha256": sha256_file(run_root / "QUALIFICATION_RESULT.json"),
        "run_seal_sha256": sha256_file(run_root / "RUN_SEAL.json"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = audit()
    if args.output is not None:
        write_json(args.output.resolve(), receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
