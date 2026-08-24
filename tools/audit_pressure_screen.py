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
from tools.offline_tokenizer import OfflineTokenizer


RUN_ID = "2026-08-24-artifact-coupled-pressure-screen-v0"
FREEZE_COMMIT = "7423d214d5d2a5b77514b0acff43d547743b422e"
PROMPT_LIMIT = 20_992
EXPECTED_PENDING = "RESULT-008"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(repository_root: Path = ROOT) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    run_root = repository_root / "runs" / RUN_ID
    failures: list[str] = []
    required = (
        "AUTHORIZATION_RECEIPT.json",
        "CALL_TRACE.json",
        "FINALIZATION.json",
        "FINAL_MESSAGES.json",
        "PRESSURE_BOUNDARY.json",
        "QUALIFICATION_HANDOFF.json",
        "RESULT_LEDGER.json",
        "RUN_SEAL.json",
        "RUNTIME_ASSET_VERIFICATION.json",
        "SCREEN_RESULT.json",
        "model/RUNTIME_GATE.json",
        "model/RUNTIME_RELEASE.json",
    )
    for relative in required:
        if not (run_root / relative).is_file():
            failures.append(f"missing:{relative}")
    if failures:
        return {
            "schema": "artifact-coupled-pressure-screen-audit-v0",
            "run_id": RUN_ID,
            "passed": False,
            "failures": failures,
        }

    seal_errors = list(verify_tree_seal(run_root, run_root / "RUN_SEAL.json"))
    failures.extend(f"seal:{item}" for item in seal_errors)

    result = load_json(run_root / "SCREEN_RESULT.json")
    trace = load_json(run_root / "CALL_TRACE.json")
    boundary = load_json(run_root / "PRESSURE_BOUNDARY.json")
    final_messages = load_json(run_root / "FINAL_MESSAGES.json")
    ledger = load_json(run_root / "RESULT_LEDGER.json")
    authorization = load_json(run_root / "AUTHORIZATION_RECEIPT.json")
    finalization = load_json(run_root / "FINALIZATION.json")
    runtime_gate = load_json(run_root / "model" / "RUNTIME_GATE.json")
    runtime_release = load_json(run_root / "model" / "RUNTIME_RELEASE.json")
    runtime_assets = load_json(run_root / "RUNTIME_ASSET_VERIFICATION.json")
    run_handoff = load_json(run_root / "QUALIFICATION_HANDOFF.json")
    root_handoff = load_json(repository_root / "QUALIFICATION_HANDOFF.json")

    expected_result = {
        "freeze_commit": FREEZE_COMMIT,
        "run_id": RUN_ID,
        "seed": 271830,
        "actor_calls": 8,
        "serialized_tokens": 92296,
        "terminal_disposition": "authentic_result_delivery_pressure",
        "pressure_qualified": True,
        "candidate_submitted": False,
    }
    for key, expected in expected_result.items():
        if result.get(key) != expected:
            failures.append(f"result:{key}_mismatch")

    expected_authorization = {
        "authorized": True,
        "authorized_freeze_commit": FREEZE_COMMIT,
        "authorized_scopes": ["artifact_coupled_pressure_screen_v0"],
        "authorized_run_id": RUN_ID,
        "maximum_model_calls": 30,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, expected in expected_authorization.items():
        if authorization.get(key) != expected:
            failures.append(f"authorization:{key}_mismatch")

    if run_handoff != root_handoff:
        failures.append("qualification_handoff_copy_mismatch")
    if runtime_gate.get("passed") is not True:
        failures.append("runtime_gate:not_passed")
    if runtime_assets.get("passed") is not True:
        failures.append("runtime_assets:not_passed")
    if runtime_release.get("released") is not True:
        failures.append("runtime_release:not_released")
    if finalization.get("failure") is not None:
        failures.append("finalization:failure_present")
    if finalization.get("release", {}).get("released") is not True:
        failures.append("finalization:release_not_qualified")
    for forbidden in ("RUN_FAILURE.json", "BUDGET_STOP.json"):
        if (run_root / forbidden).exists():
            failures.append(f"forbidden:{forbidden}")

    if not isinstance(trace, list) or len(trace) != 8:
        failures.append("trace:expected_eight_calls")
        trace = []
    total_serialized = 0
    accepted_results = 0
    rejected_actions = 0
    initial_candidate = result.get("candidate_sha256")
    for index, row in enumerate(trace, 1):
        if not isinstance(row, dict):
            failures.append(f"trace:{index}:not_object")
            continue
        if row.get("actor_call") != index:
            failures.append(f"trace:{index}:ordinal_mismatch")
        if row.get("finish_reason") != "stop":
            failures.append(f"trace:{index}:finish_reason")
        if row.get("candidate_sha256_before") != initial_candidate or row.get(
            "candidate_sha256_after"
        ) != initial_candidate:
            failures.append(f"trace:{index}:candidate_changed")
        usage = row.get("usage")
        if not isinstance(usage, dict):
            failures.append(f"trace:{index}:usage_missing")
        else:
            prompt = usage.get("prompt_tokens")
            completion = usage.get("completion_tokens")
            total = usage.get("total_tokens")
            if not all(isinstance(value, int) and value >= 0 for value in (prompt, completion, total)):
                failures.append(f"trace:{index}:usage_invalid")
            elif prompt + completion != total:
                failures.append(f"trace:{index}:usage_arithmetic")
            else:
                total_serialized += total
        if row.get("result_id") is None:
            if row.get("rejection_code") is None:
                failures.append(f"trace:{index}:neither_result_nor_rejection")
            else:
                rejected_actions += 1
        else:
            if row.get("rejection_code") is not None:
                failures.append(f"trace:{index}:result_and_rejection")
            accepted_results += 1
    if total_serialized != 92296:
        failures.append("trace:serialized_total_mismatch")
    if accepted_results != 5 or rejected_actions != 3:
        failures.append("trace:acceptance_counts_mismatch")

    attempt_roots = sorted(run_root.glob("actor/call-*/provider_attempt"))
    if len(attempt_roots) != 8:
        failures.append(f"provider_attempts:{len(attempt_roots)}")
    for attempt_root in attempt_roots:
        receipt_path = attempt_root / "PROVIDER_CALL_RECEIPT.json"
        if not receipt_path.is_file():
            failures.append(f"provider_receipt_missing:{attempt_root.relative_to(run_root)}")
            continue
        receipt = load_json(receipt_path)
        if receipt.get("attempted") is not True:
            failures.append(f"provider_not_attempted:{attempt_root.relative_to(run_root)}")
        if receipt.get("outcome") != "valid_completion_response":
            failures.append(f"provider_outcome:{attempt_root.relative_to(run_root)}")
        if receipt.get("completion_response_valid") is not True:
            failures.append(f"provider_invalid:{attempt_root.relative_to(run_root)}")

    boundary_messages = boundary.get("messages")
    if boundary_messages != final_messages:
        failures.append("boundary:messages_do_not_match_final")
    if not isinstance(boundary_messages, list) or not boundary_messages:
        failures.append("boundary:messages_missing")
        boundary_messages = []
    boundary_tokens = OfflineTokenizer().count_messages(boundary_messages)
    expected_boundary = {
        "actor_calls_completed": 8,
        "pending_result_id": EXPECTED_PENDING,
        "ordinary_prospective_prompt_tokens": 21959,
        "prompt_limit": PROMPT_LIMIT,
        "overflow_tokens": 967,
        "candidate_sha256": initial_candidate,
    }
    for key, expected in expected_boundary.items():
        if boundary.get(key) != expected:
            failures.append(f"boundary:{key}_mismatch")
    if boundary_tokens != boundary.get("ordinary_prospective_prompt_tokens"):
        failures.append("boundary:offline_token_reconstruction_mismatch")
    if boundary.get("ordinary_prospective_prompt_tokens", 0) - PROMPT_LIMIT != boundary.get(
        "overflow_tokens"
    ):
        failures.append("boundary:overflow_arithmetic")

    records = ledger.get("records") if isinstance(ledger, dict) else None
    if not isinstance(records, list) or len(records) != 5:
        failures.append("ledger:expected_five_records")
        records = []
    pending = next(
        (row for row in records if isinstance(row, dict) and row.get("result_id") == EXPECTED_PENDING),
        None,
    )
    if pending is None:
        failures.append("ledger:pending_result_missing")
    else:
        if pending.get("acquired_call") != 8:
            failures.append("ledger:pending_acquired_call")
        if pending.get("first_model_visible_call") is not None:
            failures.append("ledger:pending_improperly_delivered")
        if pending.get("resident") is not False:
            failures.append("ledger:pending_residency")
        if not final_messages or final_messages[-1].get("role") != "user":
            failures.append("ledger:pending_message_role")
        elif final_messages[-1].get("content") != pending.get("exact_content"):
            failures.append("ledger:pending_bytes_do_not_match_last_message")
    delivered = [row for row in records if isinstance(row, dict) and row.get("result_id") != EXPECTED_PENDING]
    if not all(isinstance(row.get("first_model_visible_call"), int) for row in delivered):
        failures.append("ledger:prior_result_not_delivered")

    if (run_root / "maintenance").exists() or (run_root / "relief").exists():
        failures.append("policy:maintenance_or_relief_present")

    return {
        "schema": "artifact-coupled-pressure-screen-audit-v0",
        "run_id": RUN_ID,
        "freeze_commit": FREEZE_COMMIT,
        "passed": not failures,
        "failures": failures,
        "seal_verified": not seal_errors,
        "actor_calls": len(trace),
        "provider_attempts": len(attempt_roots),
        "attempts_per_call": 1,
        "retries": 0,
        "accepted_results": accepted_results,
        "rejected_actions": rejected_actions,
        "serialized_tokens": total_serialized,
        "candidate_changed": False,
        "candidate_submitted": False,
        "pending_result_id": EXPECTED_PENDING,
        "pending_result_delivered": False,
        "ordinary_prospective_prompt_tokens": boundary_tokens,
        "prompt_limit": PROMPT_LIMIT,
        "overflow_tokens": boundary_tokens - PROMPT_LIMIT,
        "runtime_gate_passed": runtime_gate.get("passed") is True,
        "runtime_released": runtime_release.get("released") is True,
        "screen_result_sha256": sha256_file(run_root / "SCREEN_RESULT.json"),
        "pressure_boundary_sha256": sha256_file(run_root / "PRESSURE_BOUNDARY.json"),
        "final_messages_sha256": sha256_file(run_root / "FINAL_MESSAGES.json"),
        "result_ledger_sha256": sha256_file(run_root / "RESULT_LEDGER.json"),
        "run_seal_sha256": sha256_file(run_root / "RUN_SEAL.json"),
        "measured_fork_authorized": False,
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
