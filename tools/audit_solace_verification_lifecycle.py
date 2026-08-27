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
from task_solace.evaluator_v1.evaluate import evaluate  # noqa: E402
from tools import run_solace_verification_lifecycle as measured  # noqa: E402


RUN_ROOT = ROOT / "runs" / measured.RUN_ID
OUTPUT = ROOT / "SOLACE_VERIFICATION_LIFECYCLE_AUDIT.json"
EXPECTED_COMMIT = "a2c9270c676e2d0d8427b119f81ec39b3f21b2d1"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fail_if(condition: bool, failures: list[str], message: str) -> None:
    if condition:
        failures.append(message)


def cell_audit(configuration_id: str, failures: list[str]) -> dict[str, Any]:
    cell_root = RUN_ROOT / "cells" / configuration_id
    seal_errors = list(verify_tree_seal(cell_root, cell_root / "RUN_SEAL.json"))
    failures.extend(f"{configuration_id}:seal:{item}" for item in seal_errors)
    cell = load(cell_root / "CELL_RESULT.json")
    trace: list[dict[str, Any]] = load(cell_root / "ACTOR_TRACE.json")
    relief: list[dict[str, Any]] = load(cell_root / "RELIEF_TRACE.json")
    initial = load(cell_root / "INITIAL_STATE.json")
    release = load(cell_root / "model" / "RUNTIME_RELEASE.json")
    provider_receipts = sorted(cell_root.glob("actor/call-*/provider_attempt/PROVIDER_CALL_RECEIPT.json"))
    receipt_rows = [load(path) for path in provider_receipts]
    prompt_tokens = sum(int(row["usage"]["prompt_tokens"]) for row in trace)
    completion_tokens = sum(int(row["usage"]["completion_tokens"]) for row in trace)
    total_tokens = sum(int(row["usage"]["total_tokens"]) for row in trace)
    cached_tokens = sum(int(row["usage"].get("cached_tokens") or 0) for row in trace)
    actions = [(row.get("parsed_action") or {}).get("action", "rejected") for row in trace]
    action_counts = dict(sorted(Counter(actions).items()))
    candidate_root = cell_root / "trajectory" / "world" / "candidate"
    final_evaluation = evaluate(candidate_root)

    fail_if(cell.get("configuration_id") != configuration_id, failures, f"{configuration_id}:cell id")
    fail_if(initial.get("candidate_sha256") != "82d14bff607d8e323899d09b72739ee4bf14bc067013c6675365b580093ecf5a", failures, f"{configuration_id}:donor candidate")
    fail_if(cell.get("candidate_sha256") != final_evaluation["candidate_sha256"], failures, f"{configuration_id}:candidate binding")
    fail_if(int(cell.get("serialized_tokens", -1)) != total_tokens, failures, f"{configuration_id}:serialized total")
    fail_if(int(cell.get("actor_calls", -1)) != len(trace), failures, f"{configuration_id}:actor calls")
    fail_if(len(provider_receipts) != len(trace), failures, f"{configuration_id}:provider receipt count")
    fail_if(any(row.get("outcome") != "valid_completion_response" for row in receipt_rows), failures, f"{configuration_id}:provider outcome")
    fail_if(any(row.get("attempted") is not True for row in receipt_rows), failures, f"{configuration_id}:provider attempt")
    fail_if(any(row.get("rejection_code") is not None for row in trace), failures, f"{configuration_id}:unexpected rejection")
    fail_if(release.get("released") is not True, failures, f"{configuration_id}:runtime release")
    fail_if(cell.get("terminal_disposition") != "verification_prompt_pressure_without_feasible_relief", failures, f"{configuration_id}:terminal disposition")
    fail_if(cell.get("candidate_submitted") is not False, failures, f"{configuration_id}:submission")
    fail_if(final_evaluation.get("blocking_requirements") != ["decision_heading_order: exact ordered level-two headings"], failures, f"{configuration_id}:offline evaluator blockers")
    fail_if(final_evaluation.get("closure_readiness") != "not_ready", failures, f"{configuration_id}:offline readiness")

    expected_register = configuration_id.startswith("A1_")
    fail_if((initial.get("register_sha256") is not None) != expected_register, failures, f"{configuration_id}:register treatment")
    expected_actions = (
        ["run_check", "read_batch", "read_batch", "patch_decision", "run_check", "patch_decision", "run_check", "patch_decision", "run_check", "patch_decision"]
        if configuration_id.startswith("A0_")
        else ["run_check", "read_batch", "read_batch", "patch_decision"]
    )
    fail_if(actions != expected_actions, failures, f"{configuration_id}:action sequence")
    expected_relief = (
        [(["RESULT-017"], True, 20_073), (["RESULT-018"], True, 18_167), ([], False, 21_990)]
        if configuration_id.startswith("A0_")
        else [(["RESULT-017"], True, 20_209), (["RESULT-018"], False, 21_145), ([], False, 21_145)]
    )
    observed_relief = [(row.get("selected_result_ids"), row.get("feasible"), row.get("prompt_tokens")) for row in relief]
    fail_if(observed_relief != expected_relief, failures, f"{configuration_id}:relief trace")

    return {
        "configuration_id": configuration_id,
        "seal_passed": not seal_errors,
        "actor_calls": len(trace),
        "provider_calls": len(provider_receipts),
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cached_tokens": cached_tokens,
            "cache_ratio": 0 if prompt_tokens == 0 else cached_tokens / prompt_tokens,
        },
        "actions": actions,
        "action_counts": action_counts,
        "candidate_mutation_calls": [
            int(row["actor_call"])
            for row in trace
            if row["candidate_sha256_before"] != row["candidate_sha256_after"]
        ],
        "check_calls": [int(row["actor_call"]) for row in trace if (row.get("parsed_action") or {}).get("action") == "run_check"],
        "read_batches": [
            [request["source_id"] for request in row["parsed_action"]["requests"]]
            for row in trace
            if (row.get("parsed_action") or {}).get("action") == "read_batch"
        ],
        "relief_events": relief,
        "candidate_sha256": cell["candidate_sha256"],
        "final_effect_crossed_later_model_boundary": False,
        "candidate_submitted": cell["candidate_submitted"],
        "terminal_disposition": cell["terminal_disposition"],
        "offline_final_evaluation": final_evaluation,
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
    fail_if(authorization.get("maximum_provider_calls") != 24, failures, "authorization provider budget")
    fail_if(authorization.get("attempts_per_call") != 1 or authorization.get("retries") != 0, failures, "authorization attempt policy")
    fail_if(run.get("configuration_order") != list(measured.CONFIGURATION_ORDER), failures, "configuration order")
    fail_if(run.get("failure") is not None, failures, "aggregate failure")

    cells = [cell_audit(configuration_id, failures) for configuration_id in measured.CONFIGURATION_ORDER]
    total_calls = sum(int(row["provider_calls"]) for row in cells)
    total_tokens = sum(int(row["usage"]["total_tokens"]) for row in cells)
    fail_if(total_calls != 14 or run.get("provider_calls") != total_calls, failures, "aggregate provider calls")
    fail_if(run.get("actor_calls") != total_calls, failures, "aggregate actor calls")
    fail_if(total_tokens != 243_637 or run.get("serialized_tokens") != total_tokens, failures, "aggregate serialized tokens")

    output = {
        "schema": "solace-verification-lifecycle-audit-v0",
        "run_id": measured.RUN_ID,
        "freeze_commit": EXPECTED_COMMIT,
        "passed": not failures,
        "failures": failures,
        "aggregate_seal_passed": not aggregate_seal_errors,
        "configuration_order": list(measured.CONFIGURATION_ORDER),
        "actor_calls": total_calls,
        "provider_calls": total_calls,
        "serialized_tokens": total_tokens,
        "cells": cells,
        "comparison": {
            "A1_minus_A0_actor_calls": cells[1]["actor_calls"] - cells[0]["actor_calls"],
            "A1_minus_A0_total_tokens": cells[1]["usage"]["total_tokens"] - cells[0]["usage"]["total_tokens"],
            "A1_over_A0_initial_prompt_tokens": 15_339 - 8_693,
            "common_offline_mechanical_blocker": "decision_heading_order",
            "both_final_effects_undelivered": True,
        },
        "run_seal_sha256": sha256_file(RUN_ROOT / "RUN_SEAL.json"),
        "claim_limits": [
            "The offline evaluator is deterministic and candidate-bound but tests required concepts more strongly than semantic relationships.",
            "Budget-stop cells did not receive the runner's normal external-final-evaluation step; this audit evaluates their sealed final candidates without altering the raw run.",
            "The final candidate effects did not cross a later actor boundary, so neither final artifact was rechecked in the measured trajectory.",
        ],
    }
    write_json(OUTPUT, output)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
