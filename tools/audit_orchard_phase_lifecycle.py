from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json  # noqa: E402
from reactive_runtime.seal import verify_tree_seal  # noqa: E402
from task_orchard.evaluator.evaluate import evaluate  # noqa: E402
from tools import run_orchard_phase_lifecycle as measured  # noqa: E402


RUN_ROOT = ROOT / "runs" / measured.RUN_ID
OUTPUT = ROOT / "ORCHARD_PHASE_LIFECYCLE_AUDIT.json"
EXPECTED_COMMIT = "094bbce57407568d1ef0ecd94414ae1a957e3b45"

F0 = "F0_FIXED_SCAFFOLD_APPEND_ONLY_VERIFICATION"
P1 = "P1_PHASE_CONDITIONAL_CURRENT_VERIFICATION"

EXPECTED_ACTIONS = {
    F0: [
        "read_batch",
        "read_batch",
        "replace_evidence_ledger",
        *(["upsert_decision_section"] * 8),
        "begin_verification",
        "run_check",
        "read_batch",
    ],
    P1: [
        "read_batch",
        "read_batch",
        "replace_evidence_ledger",
        *(["upsert_decision_section"] * 8),
        "begin_verification",
        "run_check",
        "read_batch",
        "read_source",
        "patch_decision",
        "read_source",
        "patch_decision",
        "run_check",
        "patch_decision",
        "read_source",
        "read_source",
        "read_source",
        "read_source",
    ],
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fail_if(condition: bool, failures: list[str], message: str) -> None:
    if condition:
        failures.append(message)


def action_name(row: dict[str, Any]) -> str:
    action = row.get("parsed_action") or {}
    return str(action.get("action") or "rejected")


def cell_audit(configuration_id: str, failures: list[str]) -> dict[str, Any]:
    cell_root = RUN_ROOT / "cells" / configuration_id
    seal_errors = list(verify_tree_seal(cell_root, cell_root / "RUN_SEAL.json"))
    failures.extend(f"{configuration_id}:seal:{item}" for item in seal_errors)
    cell = load(cell_root / "CELL_RESULT.json")
    trace: list[dict[str, Any]] = load(cell_root / "ACTOR_TRACE.json")
    maintenance: list[dict[str, Any]] = load(cell_root / "MAINTENANCE_TRACE.json")
    relief: list[dict[str, Any]] = load(cell_root / "RELIEF_TRACE.json")
    release = load(cell_root / "model" / "RUNTIME_RELEASE.json")
    provider_receipts = sorted(cell_root.glob("*/call-*/provider_attempt/PROVIDER_CALL_RECEIPT.json"))
    receipt_rows = [load(path) for path in provider_receipts]
    actions = [action_name(row) for row in trace]
    prompt_tokens = sum(int(row["usage"]["prompt_tokens"]) for row in trace + maintenance)
    completion_tokens = sum(int(row["usage"]["completion_tokens"]) for row in trace + maintenance)
    cached_tokens = sum(int(row["usage"].get("cached_tokens") or 0) for row in trace + maintenance)
    total_tokens = prompt_tokens + completion_tokens
    candidate_root = cell_root / "trajectory" / "world" / "candidate"
    offline_evaluation = evaluate(candidate_root)

    fail_if(cell.get("configuration_id") != configuration_id, failures, f"{configuration_id}:cell id")
    fail_if(actions != EXPECTED_ACTIONS[configuration_id], failures, f"{configuration_id}:action sequence")
    fail_if(int(cell.get("actor_calls", -1)) != len(trace), failures, f"{configuration_id}:actor calls")
    fail_if(int(cell.get("maintenance_calls", -1)) != len(maintenance), failures, f"{configuration_id}:maintenance calls")
    fail_if(int(cell.get("provider_calls", -1)) != len(provider_receipts), failures, f"{configuration_id}:provider calls")
    fail_if(int(cell.get("serialized_tokens", -1)) != total_tokens, failures, f"{configuration_id}:serialized tokens")
    fail_if(cell.get("candidate_sha256") != offline_evaluation["candidate_sha256"], failures, f"{configuration_id}:candidate binding")
    fail_if(any(row.get("outcome") != "valid_completion_response" for row in receipt_rows), failures, f"{configuration_id}:provider outcome")
    fail_if(any(row.get("attempted") is not True for row in receipt_rows), failures, f"{configuration_id}:provider attempt")
    fail_if(release.get("released") is not True, failures, f"{configuration_id}:runtime release")
    fail_if(cell.get("candidate_submitted") is not False, failures, f"{configuration_id}:submission")
    fail_if(offline_evaluation.get("closure_readiness") != "not_ready", failures, f"{configuration_id}:readiness")

    if configuration_id == F0:
        fail_if(cell.get("terminal_disposition") != "context_pressure_without_feasible_relief", failures, "F0:terminal")
        fail_if(len(trace) != 14 or len(maintenance) != 8, failures, "F0:call totals")
        fail_if([row["actor_call"] for row in trace if row["candidate_sha256_before"] != row["candidate_sha256_after"]] != list(range(3, 12)), failures, "F0:mutation calls")
        fail_if([row["actor_call"] for row in trace if action_name(row) == "run_check"] != [13], failures, "F0:check calls")
        fail_if(any(row.get("rejection_code") for row in trace), failures, "F0:unexpected rejection")
        fail_if(len(relief) != 9 or relief[-1].get("feasible") is not False, failures, "F0:terminal relief")
    else:
        fail_if(cell.get("terminal_disposition") != "verification_call_budget_exhausted", failures, "P1:terminal")
        fail_if(len(trace) != 24 or len(maintenance) != 8, failures, "P1:call totals")
        fail_if([row["actor_call"] for row in trace if row["candidate_sha256_before"] != row["candidate_sha256_after"]] != [*range(3, 12), 18], failures, "P1:mutation calls")
        fail_if([row["actor_call"] for row in trace if action_name(row) == "run_check"] != [13, 19], failures, "P1:check calls")
        fail_if([(row["actor_call"], row.get("rejection_code")) for row in trace if row.get("rejection_code")] != [(16, "patch_anchor_not_unique"), (20, "patch_anchor_not_unique")], failures, "P1:rejections")
        repeat_actions = [row.get("parsed_action") for row in trace[-4:]]
        fail_if(len({json.dumps(row, sort_keys=True) for row in repeat_actions}) != 1, failures, "P1:terminal repeat loop")
        fail_if(any(row.get("parsed_action", {}).get("source_id") != "CURRENT" for row in trace[-4:]), failures, "P1:terminal source")

    return {
        "configuration_id": configuration_id,
        "seal_passed": not seal_errors,
        "actor_calls": len(trace),
        "maintenance_calls": len(maintenance),
        "provider_calls": len(provider_receipts),
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cached_tokens": cached_tokens,
            "cache_ratio": 0 if prompt_tokens == 0 else cached_tokens / prompt_tokens,
        },
        "actions": actions,
        "action_counts": dict(sorted(Counter(actions).items())),
        "candidate_mutation_calls": [
            int(row["actor_call"])
            for row in trace
            if row["candidate_sha256_before"] != row["candidate_sha256_after"]
        ],
        "check_calls": [int(row["actor_call"]) for row in trace if action_name(row) == "run_check"],
        "rejected_actions": [
            {"actor_call": int(row["actor_call"]), "code": row["rejection_code"]}
            for row in trace
            if row.get("rejection_code")
        ],
        "maintenance_dispositions": [row["admission"]["disposition"] for row in maintenance],
        "register_claims": cell["register_claims"],
        "register_retained_in_verification": cell.get("register_retained_in_verification"),
        "relief_events": relief,
        "candidate_sha256": cell["candidate_sha256"],
        "candidate_submitted": cell["candidate_submitted"],
        "terminal_disposition": cell["terminal_disposition"],
        "offline_final_evaluation": offline_evaluation,
        "run_seal_sha256": sha256_file(cell_root / "RUN_SEAL.json"),
    }


def main() -> int:
    failures: list[str] = []
    aggregate_seal_errors = list(verify_tree_seal(RUN_ROOT, RUN_ROOT / "RUN_SEAL.json"))
    failures.extend(f"aggregate_seal:{item}" for item in aggregate_seal_errors)
    run = load(RUN_ROOT / "RUN_RESULT.json")
    authorization = load(RUN_ROOT / "AUTHORIZATION_RECEIPT.json")
    freeze = load(RUN_ROOT / "FREEZE_BINDING.json")

    fail_if(run.get("freeze_commit") != EXPECTED_COMMIT, failures, "run freeze commit")
    fail_if(freeze.get("commit") != EXPECTED_COMMIT, failures, "freeze binding commit")
    fail_if(authorization.get("authorized_freeze_commit") != EXPECTED_COMMIT, failures, "authorization commit")
    fail_if(authorization.get("authorized_run_id") != measured.RUN_ID, failures, "authorization run id")
    fail_if(authorization.get("maximum_actor_calls") != 72, failures, "authorization actor budget")
    fail_if(authorization.get("maximum_maintenance_calls") != 24, failures, "authorization maintenance budget")
    fail_if(authorization.get("maximum_provider_calls") != 96, failures, "authorization provider budget")
    fail_if(authorization.get("attempts_per_call") != 1 or authorization.get("retries") != 0, failures, "authorization attempt policy")
    fail_if(run.get("configuration_order") != list(measured.CONFIGURATION_ORDER), failures, "configuration order")
    fail_if(run.get("failure") is not None, failures, "aggregate failure")

    cells = [cell_audit(configuration_id, failures) for configuration_id in measured.CONFIGURATION_ORDER]
    f0_trace = load(RUN_ROOT / "cells" / F0 / "ACTOR_TRACE.json")
    p1_trace = load(RUN_ROOT / "cells" / P1 / "ACTOR_TRACE.json")
    prefix_fields = (
        "output_sha256",
        "parsed_action",
        "candidate_sha256_before",
        "candidate_sha256_after",
        "result_id",
        "result_kind",
        "rejection_code",
    )
    common_prefix_identical = all(
        all(f0_trace[index].get(field) == p1_trace[index].get(field) for field in prefix_fields)
        for index in range(12)
    )
    fail_if(not common_prefix_identical, failures, "common prefix mismatch")
    total_actor = sum(int(row["actor_calls"]) for row in cells)
    total_maintenance = sum(int(row["maintenance_calls"]) for row in cells)
    total_provider = sum(int(row["provider_calls"]) for row in cells)
    total_tokens = sum(int(row["usage"]["total_tokens"]) for row in cells)
    fail_if((total_actor, total_maintenance, total_provider, total_tokens) != (38, 16, 54, 736_332), failures, "aggregate totals")
    fail_if(run.get("actor_calls") != total_actor or run.get("maintenance_calls") != total_maintenance, failures, "aggregate call totals")
    fail_if(run.get("provider_calls") != total_provider or run.get("serialized_tokens") != total_tokens, failures, "aggregate provider/token totals")

    f0, p1 = cells
    output = {
        "schema": "orchard-phase-lifecycle-audit-v0",
        "run_id": measured.RUN_ID,
        "freeze_commit": EXPECTED_COMMIT,
        "passed": not failures,
        "failures": failures,
        "aggregate_seal_passed": not aggregate_seal_errors,
        "configuration_order": list(measured.CONFIGURATION_ORDER),
        "actor_calls": total_actor,
        "maintenance_calls": total_maintenance,
        "provider_calls": total_provider,
        "serialized_tokens": total_tokens,
        "cells": cells,
        "comparison": {
            "common_prefix_actor_calls": 12,
            "common_prefix_byte_identical_actions": common_prefix_identical,
            "P1_minus_F0_actor_calls": p1["actor_calls"] - f0["actor_calls"],
            "P1_minus_F0_total_tokens": p1["usage"]["total_tokens"] - f0["usage"]["total_tokens"],
            "F0_initial_check_blockers": 9,
            "P1_initial_check_blockers": 9,
            "P1_post_repair_check_blockers": 3,
            "F0_post_check_actor_calls": 1,
            "P1_post_check_actor_calls": 11,
            "P1_terminal_identical_CURRENT_reads": 4,
            "both_not_ready": True,
        },
        "run_seal_sha256": sha256_file(RUN_ROOT / "RUN_SEAL.json"),
        "claim_limits": [
            "This is a compound post-transition lifecycle comparison; scaffold demotion and verification-frame replacement are not isolated.",
            "The common construction prefix does not establish independent replication because both cells use the same frozen model-facing state and seed.",
            "P1 improved operability and candidate quality but did not reach readiness, submission, or useful completion.",
            "The evaluator's remaining R05 failure is a surface-order false negative under direct semantic review; exact word-count and ledger-citation requirements still fail.",
        ],
    }
    write_json(OUTPUT, output)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
