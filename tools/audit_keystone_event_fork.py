from __future__ import annotations

# ruff: noqa: E402

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import load_json, sha256_file, write_json
from reactive_runtime.causal_activation import (
    activation_tax,
    detect_causal_fork_activation,
)
from reactive_runtime.seal import verify_tree_seal


RUN_ROOT = ROOT / "runs" / "2026-08-27-keystone-event-triggered-causal-continuation-v0"
PARENT_ROOT = ROOT / "runs" / "2026-08-27-keystone-bounded-causal-pressure-screen-v0"
OUTPUT = ROOT / "KEYSTONE_EVENT_FORK_AUDIT.json"


def load_list(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise ValueError(f"expected JSON object list: {path}")
    return value


def usage_tokens(rows: list[dict[str, Any]]) -> int:
    return sum(int(row["usage"]["total_tokens"]) for row in rows)


def source_ids(ledger: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for record in ledger["records"]:
        if record.get("result_kind") != "source_observation":
            continue
        metadata = record.get("metadata")
        if not isinstance(metadata, dict):
            continue
        for source_id in metadata.get("source_ids", []):
            if isinstance(source_id, str):
                values.add(source_id)
    return values


def audit() -> dict[str, Any]:
    run_result = load_json(RUN_ROOT / "RUN_RESULT.json")
    common_result = load_json(RUN_ROOT / "common" / "COMMON_RESULT.json")
    finalization = load_json(RUN_ROOT / "common" / "FINALIZATION.json")
    parent = load_json(PARENT_ROOT / "SCREEN_RESULT.json")
    task_lock = load_json(ROOT / "task_keystone" / "TASK_SOURCE_LOCK.json")
    ledger = load_json(RUN_ROOT / "common" / "RESULT_LEDGER.json")
    actor_trace = load_list(RUN_ROOT / "common" / "ACTOR_TRACE.json")
    maintenance_trace = load_list(RUN_ROOT / "common" / "MAINTENANCE_TRACE.json")

    activation = detect_causal_fork_activation(
        actor_trace,
        initial_candidate_sha256=str(parent["candidate_sha256"]),
    )
    corrected_tax = activation_tax(
        activation,
        parent_calls=int(parent["actor_calls"]),
        parent_serialized_tokens=int(parent["serialized_tokens"]),
        continuation_trace=actor_trace,
        maintenance_trace=maintenance_trace,
    )
    expected_sources = {str(row["source_id"]) for row in task_lock["source_custody"]}
    observed_sources = source_ids(ledger)
    actor_tokens = usage_tokens(actor_trace)
    maintenance_tokens = usage_tokens(maintenance_trace)
    assistant_call_6 = (
        (RUN_ROOT / "common" / "actor" / "call-006" / "assistant_content.txt")
        .read_text(encoding="utf-8")
        .strip()
    )

    action_sequence = []
    for row in actor_trace:
        action = row.get("parsed_action")
        action_sequence.append(
            {
                "common_actor_call": row["common_actor_call"],
                "action": action,
                "result_kind": row.get("result_kind"),
                "rejection_code": row.get("rejection_code"),
            }
        )

    failures: list[str] = []
    failures.extend(
        f"run_seal:{item}"
        for item in verify_tree_seal(RUN_ROOT, RUN_ROOT / "RUN_SEAL.json")
    )
    failures.extend(
        f"common_seal:{item}"
        for item in verify_tree_seal(
            RUN_ROOT / "common", RUN_ROOT / "common" / "RUN_SEAL.json"
        )
    )
    checks = {
        "run_has_no_failure": run_result["failure"] is None,
        "common_terminal_is_trigger_absent": common_result["terminal_disposition"]
        == "causal_trigger_not_observed",
        "treatment_not_activated": run_result["treatment_activated"] is False,
        "no_branches_executed": run_result["branches"] == []
        and run_result["branches_completed"] == 0,
        "candidate_remained_initial": common_result["candidate_sha256"]
        == parent["candidate_sha256"],
        "phase_remained_construction": common_result["phase"] == "construction",
        "all_sources_observed": observed_sources == expected_sources,
        "actor_count_matches": len(actor_trace) == common_result["actor_calls"] == 8,
        "maintenance_count_matches": len(maintenance_trace)
        == common_result["maintenance_calls"]
        == 10,
        "common_model_count_matches": len(actor_trace) + len(maintenance_trace)
        == common_result["model_calls"]
        == 18,
        "common_token_count_matches": actor_tokens + maintenance_tokens
        == common_result["serialized_tokens"]
        == 198_745,
        "server_and_gpu_released": finalization["release"]["released"] is True
        and finalization["release"]["active_llama_server_pids_after"] == []
        and finalization["release"]["port_open_after"] is False,
        "terminal_activation_recomputed_from_nonempty_trace": activation.qualified
        is False
        and "empty_trace" not in activation.failures,
        "invalid_batch_was_custodied": actor_trace[5]["rejection_code"]
        == "invalid_action"
        and '"action":"read_batch"' in assistant_call_6,
        "embedded_activation_snapshot_is_stale": common_result["activation"]["failures"]
        == ["empty_trace"],
        "embedded_activation_tax_omits_maintenance": common_result["activation_tax"][
            "calls_before_first_treatment_decision"
        ]
        == 17,
    }
    failures.extend(name for name, passed in checks.items() if not passed)

    return {
        "schema": "keystone-event-fork-postrun-audit-v0",
        "passed": not failures,
        "run_id": run_result["run_id"],
        "freeze_commit": run_result["freeze_commit"],
        "run_seal_sha256": sha256_file(RUN_ROOT / "RUN_SEAL.json"),
        "common_seal_sha256": sha256_file(RUN_ROOT / "common" / "RUN_SEAL.json"),
        "checks": checks,
        "failures": failures,
        "scientific_disposition": {
            "run_valid": True,
            "causal_treatment_activated": False,
            "causal_treatment_evaluated": False,
            "keystone_disposition": "non_diagnostic_closed",
            "another_same_world_attempt_authorized": False,
            "promotion_authorized": False,
        },
        "behavior": {
            "all_source_ids": sorted(observed_sources),
            "distinct_sources_observed": len(observed_sources),
            "action_sequence": action_sequence,
            "invalid_action_exact_output": assistant_call_6,
            "candidate_sha256": common_result["candidate_sha256"],
            "phase": common_result["phase"],
        },
        "corrected_activation": activation.as_dict(),
        "corrected_activation_tax": corrected_tax,
        "token_breakdown": {
            "parent_actor_tokens": int(parent["serialized_tokens"]),
            "common_actor_tokens": actor_tokens,
            "common_maintenance_tokens": maintenance_tokens,
            "common_total_tokens": actor_tokens + maintenance_tokens,
            "whole_pre_treatment_tokens": (
                int(parent["serialized_tokens"]) + actor_tokens + maintenance_tokens
            ),
        },
        "embedded_summary_defect": {
            "custody_or_run_invalidated": False,
            "stale_activation_failure": common_result["activation"]["failures"],
            "reported_calls_before_treatment": common_result["activation_tax"][
                "calls_before_first_treatment_decision"
            ],
            "correct_calls_before_treatment": corrected_tax[
                "calls_before_first_treatment_decision"
            ],
            "reported_tokens_before_treatment": common_result["activation_tax"][
                "serialized_tokens_before_first_treatment_decision"
            ],
            "correct_tokens_before_treatment": corrected_tax[
                "serialized_tokens_before_first_treatment_decision"
            ],
            "cause": (
                "the terminal detector was not recomputed outside verification and "
                "activation tax counted actor calls but omitted semantic-maintenance calls"
            ),
        },
        "claim_limits": [
            "the run evaluates common-system reachability, not V0 versus V1",
            "observing all source objects does not establish semantic integration",
            "no causal-continuity treatment decision occurred",
            "no same-world rerun or successor mechanism is authorized",
            "the donor-preserving writable product path was not involved",
        ],
    }


def main() -> int:
    receipt = audit()
    write_json(OUTPUT, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
