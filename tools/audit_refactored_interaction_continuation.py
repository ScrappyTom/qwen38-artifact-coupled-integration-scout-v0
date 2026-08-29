from __future__ import annotations

# ruff: noqa: E402

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import load_json, sha256_file, write_json
from reactive_runtime.seal import verify_tree_seal


RUN_ID = "2026-08-29-trellis-refactored-interaction-continuation-v0"
FREEZE_COMMIT = "18e17806e906d57943ab9b7461def708084d69b1"
PARENT_RUN_ID = "2026-08-29-trellis-refactored-interaction-tranche-v0"
RUN_ROOT = ROOT / "qualification_runs" / RUN_ID
PARENT_ROOT = ROOT / "qualification_runs" / PARENT_RUN_ID
OUTPUT = ROOT / "TRELLIS_REFACTORED_INTERACTION_CONTINUATION_AUDIT.json"
V0 = "V0_EXACT_ARTIFACT"
V1 = "V1_TEMPORARY_PROVENANCE_SCAFFOLD"


def _review(root: Path, configuration_id: str) -> dict[str, Any]:
    return load_json(root / "cells" / configuration_id / "tranche-002" / "MECHANICAL_REVIEW.json")


def _parent_review(configuration_id: str) -> dict[str, Any]:
    return load_json(
        PARENT_ROOT
        / "cells"
        / configuration_id
        / "tranche-001"
        / "MECHANICAL_REVIEW.json"
    )


def _new_actions(review: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(row["action"])
        for row in review["action_dispositions"]
        if int(row["call_index"]) >= 13
    ]


def _candidate_effects(
    review: dict[str, Any], relief_by_id: dict[str, bool]
) -> list[dict[str, Any]]:
    return [
        {
            "delivery_state": row["delivery_state"],
            "exact_content_size_bytes": row["exact_content_size_bytes"],
            "relief_eligible": relief_by_id[row["result_id"]],
            "result_id": row["result_id"],
        }
        for row in review["results"]
        if row["result_kind"] == "candidate_effect"
    ]


def main() -> int:
    authorization = load_json(RUN_ROOT / "AUTHORIZATION_RECEIPT.json")
    failure = load_json(RUN_ROOT / "RUN_FAILURE.json")
    v0 = _review(RUN_ROOT, V0)
    v1 = _review(RUN_ROOT, V1)
    parent_v0 = _parent_review(V0)
    parent_v1 = _parent_review(V1)
    v0_tranche = load_json(RUN_ROOT / "cells" / V0 / "tranche-002" / "TRANCHE_RESULT.json")
    v1_tranche = load_json(RUN_ROOT / "cells" / V1 / "tranche-002" / "TRANCHE_RESULT.json")
    v0_cell = load_json(RUN_ROOT / "cells" / V0 / "CELL_RESULT.json")
    v1_evaluation = load_json(
        RUN_ROOT / "cells" / V1 / "EXTERNAL_CHECKPOINT_EVALUATION.json"
    )["evaluation"]
    v1_checkpoint = load_json(
        RUN_ROOT / "cells" / V1 / "tranche-002" / "CHECKPOINT.json"
    )
    relief_by_id = {
        str(event["data"]["result"]["result_id"]): bool(
            event["data"]["result"]["relief_eligible"]
        )
        for event in v1_checkpoint["event_log"]["events"]
        if event["kind"] == "result_acquired"
    }
    failures = [
        f"seal:{item}"
        for item in verify_tree_seal(RUN_ROOT, RUN_ROOT / "RUN_SEAL.json")
    ]
    if git_freeze := load_json(RUN_ROOT / "FREEZE_BINDING.json").get("commit"):
        if git_freeze != FREEZE_COMMIT:
            failures.append("freeze_commit_mismatch")
    if failure.get("error_type") != "RuntimeError" or failure.get("error_message") != (
        "nonqualifying tranche disposition: capacity_blocked"
    ):
        failures.append("unexpected_wrapper_failure")
    if v0_tranche.get("disposition") != "checkpoint_pause":
        failures.append("v0_disposition_mismatch")
    if v1_tranche.get("disposition") != "capacity_blocked":
        failures.append("v1_disposition_mismatch")
    if v0_tranche.get("actor_attempts") != 12 or v1_tranche.get("actor_attempts") != 6:
        failures.append("actor_attempt_count_mismatch")
    if v1_tranche.get("failed_actor_invocations") != 0:
        failures.append("unexpected_failed_actor_invocation")
    if v1_tranche.get("maintenance_attempts") != 5:
        failures.append("maintenance_attempt_count_mismatch")
    if v1["terminal"] != "capacity_blocked":
        failures.append("terminal_state_mismatch")
    if v1["tranche_timing"][-1] != {
        "actor_call": 19,
        "actor_elapsed_ms": None,
        "actor_provider_attempts": 0,
        "cumulative_maintenance_calls": 11,
        "disposition": "capacity_blocked",
        "prompt_tokens": 21041,
    }:
        failures.append("capacity_boundary_mismatch")

    v0_delta_tokens = int(v0["counters"]["serialized_tokens"]) - int(
        parent_v0["counters"]["serialized_tokens"]
    )
    v1_delta_tokens = int(v1["counters"]["serialized_tokens"]) - int(
        parent_v1["counters"]["serialized_tokens"]
    )
    v0_delta_provider = int(v0["counters"]["provider_attempts"]) - int(
        parent_v0["counters"]["provider_attempts"]
    )
    v1_delta_provider = int(v1["counters"]["provider_attempts"]) - int(
        parent_v1["counters"]["provider_attempts"]
    )
    actual = {
        "actor_calls": int(v0_tranche["actor_attempts"]) + int(v1_tranche["actor_attempts"]),
        "maintenance_calls": int(v1_tranche["maintenance_attempts"]),
        "provider_calls": v0_delta_provider + v1_delta_provider,
        "serialized_tokens": v0_delta_tokens + v1_delta_tokens,
    }
    expected_actual = {
        "actor_calls": 18,
        "maintenance_calls": 5,
        "provider_calls": 23,
        "serialized_tokens": 383176,
    }
    if actual != expected_actual:
        failures.append("authorized_delta_accounting_mismatch")
    for key, actual_key in (
        ("maximum_actor_calls", "actor_calls"),
        ("maximum_maintenance_calls", "maintenance_calls"),
        ("maximum_provider_calls", "provider_calls"),
        ("maximum_serialized_tokens", "serialized_tokens"),
    ):
        if actual[actual_key] > int(authorization[key]):
            failures.append(f"authorization_exceeded:{key}")
    if authorization.get("attempts_per_call") != 1 or authorization.get("retries") != 0:
        failures.append("authorization_attempt_policy_mismatch")

    parent_actions = [dict(row["action"]) for row in parent_v0["action_dispositions"]]
    v0_actions = _new_actions(v0)
    if v0_actions != parent_actions:
        failures.append("v0_catalog_replay_mismatch")
    v1_actions = _new_actions(v1)
    expected_v1_action_kinds = [
        "replace_evidence_ledger",
        "upsert_decision_section",
        "upsert_decision_section",
        "upsert_decision_section",
        "upsert_decision_section",
        "upsert_decision_section",
    ]
    if [row["action"] for row in v1_actions] != expected_v1_action_kinds:
        failures.append("v1_action_sequence_mismatch")
    headings = [row.get("heading") for row in v1_actions[1:]]
    if headings != [
        "Authority, scope, and operating states",
        "Heat triggers and geographic staging",
        "Power, water, and cooling continuity",
        "Clinical, shelter, and accessibility operations",
        "Transit, communications, logistics, and staffing",
    ]:
        failures.append("v1_heading_sequence_mismatch")
    effects = _candidate_effects(v1, relief_by_id)
    if len(effects) != 6 or any(row["relief_eligible"] for row in effects):
        failures.append("candidate_effect_relief_mismatch")
    if sum(row["delivery_state"] == "delivered_resident" for row in effects) != 5:
        failures.append("delivered_candidate_effect_count_mismatch")
    if sum(row["delivery_state"] == "pending" for row in effects) != 1:
        failures.append("pending_candidate_effect_count_mismatch")
    current_candidate = next(
        row for row in v1["state_slots"] if row["slot_id"] == "current_candidate"
    )
    if v1_evaluation.get("candidate_sha256") != current_candidate["metadata"][
        "candidate_sha256"
    ]:
        failures.append("evaluation_candidate_binding_mismatch")
    if v1_evaluation.get("closure_readiness") != "not_ready":
        failures.append("unexpected_v1_readiness")
    releases = {
        cfg: load_json(RUN_ROOT / "cells" / cfg / "RUNTIME_RELEASE.json")["release"]
        for cfg in (V0, V1)
    }
    if any(row.get("released") is not True for row in releases.values()):
        failures.append("runtime_release_failure")

    receipt = {
        "schema": "trellis-refactored-interaction-continuation-audit-v0",
        "run_id": RUN_ID,
        "freeze_commit": FREEZE_COMMIT,
        "passed": not failures,
        "failures": failures,
        "run_seal_sha256": sha256_file(RUN_ROOT / "RUN_SEAL.json"),
        "authorization_limits": {
            key: authorization[key]
            for key in (
                "maximum_actor_calls",
                "maximum_maintenance_calls",
                "maximum_provider_calls",
                "maximum_serialized_tokens",
                "attempts_per_call",
                "retries",
            )
        },
        "actual_additional": actual,
        "wrapper_disposition": "sealed_failure_receipt_for_valid_capacity_blocked_system_stop",
        "cells": {
            V0: {
                "additional_actor_calls": v0_tranche["actor_attempts"],
                "additional_maintenance_calls": 0,
                "additional_provider_calls": v0_delta_provider,
                "additional_serialized_tokens": v0_delta_tokens,
                "cumulative_actor_calls": len(v0["completed_actor_calls"]),
                "cumulative_serialized_tokens": v0["counters"]["serialized_tokens"],
                "disposition": v0_tranche["disposition"],
                "catalog_replay_actions": len(v0_actions),
                "candidate_transitions": len(v0["candidate_transitions"]),
                "evaluation_passed": v0_cell["evaluation_passed"],
                "repeated_assistant_messages": v0["recurrence"][
                    "repeated_assistant_messages"
                ],
            },
            V1: {
                "additional_actor_calls": v1_tranche["actor_attempts"],
                "additional_maintenance_calls": v1_tranche["maintenance_attempts"],
                "additional_provider_calls": v1_delta_provider,
                "additional_serialized_tokens": v1_delta_tokens,
                "cumulative_actor_calls": len(v1["completed_actor_calls"]),
                "cumulative_maintenance_calls": v1["interaction_lifecycle"][
                    "maintenance_calls"
                ],
                "cumulative_serialized_tokens": v1["counters"]["serialized_tokens"],
                "disposition": v1_tranche["disposition"],
                "candidate_transitions": len(v1["candidate_transitions"]),
                "candidate_sha256": v1_evaluation["candidate_sha256"],
                "decision_word_count": v1_evaluation["decision_word_count"],
                "decision_source_count": len(v1_evaluation["decision_source_ids"]),
                "ledger_source_count": len(v1_evaluation["ledger_source_ids"]),
                "evaluation_passed": v1_evaluation["passed"],
                "closure_readiness": v1_evaluation["closure_readiness"],
                "candidate_effects": effects,
                "next_prompt_tokens": v1["tranche_timing"][-1]["prompt_tokens"],
            },
        },
        "claim_limits": [
            "V0 repeated the complete catalog through explicit read actions after RESULT-012 delivery; this is behavioral recurrence, not host duplication.",
            "V1 changed action category immediately after RESULT-012 delivery and accumulated an exact ledger plus five decision sections.",
            "The whole V1 configuration, not the scaffold alone, caused the observed divergence.",
            "V1 remained not ready and did not reach verification, repair, recheck, or closure.",
            "Capacity stopped V1 because five delivered and one pending candidate-effect results were non-relief-eligible while the current candidate also remained resident.",
            "The launcher classified capacity_blocked as nonqualifying after writing the exact checkpoint and evaluation; this wrapper failure does not erase the sealed system behavior.",
        ],
    }
    write_json(OUTPUT, receipt)
    if failures:
        raise SystemExit("; ".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
