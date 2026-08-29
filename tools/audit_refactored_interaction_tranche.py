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


RUN_ID = "2026-08-29-trellis-refactored-interaction-tranche-v0"
FREEZE_COMMIT = "381e44c9eb3c3c10a793903155c2482f5f8c570f"
RUN_ROOT = ROOT / "qualification_runs" / RUN_ID
OUTPUT = ROOT / "TRELLIS_REFACTORED_INTERACTION_TRANCHE_AUDIT.json"
CONFIGURATIONS = (
    "V0_EXACT_ARTIFACT",
    "V1_TEMPORARY_PROVENANCE_SCAFFOLD",
)


def _review(configuration_id: str) -> dict[str, Any]:
    return load_json(
        RUN_ROOT
        / "cells"
        / configuration_id
        / "tranche-001"
        / "MECHANICAL_REVIEW.json"
    )


def _action_signature(review: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(row["action"]) for row in review["action_dispositions"]]


def _actor_accounting(review: dict[str, Any]) -> dict[str, int]:
    prompt = sum(int(row["usage"]["prompt_tokens"]) for row in review["invocations"])
    completion = sum(
        int(row["usage"]["completion_tokens"]) for row in review["invocations"]
    )
    cached = sum(
        int(row["usage"]["prompt_tokens_details"]["cached_tokens"])
        for row in review["invocations"]
    )
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "serialized_tokens": prompt + completion,
        "cached_prompt_tokens": cached,
    }


def main() -> int:
    aggregate = load_json(RUN_ROOT / "INTERACTION_TRANCHE_RESULT.json")
    finalization = load_json(RUN_ROOT / "FINALIZATION.json")
    authorization = load_json(RUN_ROOT / "AUTHORIZATION_RECEIPT.json")
    reviews = {configuration_id: _review(configuration_id) for configuration_id in CONFIGURATIONS}
    failures = [
        f"seal:{item}"
        for item in verify_tree_seal(RUN_ROOT, RUN_ROOT / "RUN_SEAL.json")
    ]

    if aggregate.get("freeze_commit") != FREEZE_COMMIT:
        failures.append("freeze_commit_mismatch")
    if aggregate.get("run_id") != RUN_ID:
        failures.append("run_id_mismatch")
    if finalization.get("failure") is not None:
        failures.append("run_failure_present")
    expected_totals = {
        "actor_calls": 24,
        "maintenance_calls": 6,
        "provider_calls": 30,
        "serialized_tokens": 379972,
    }
    for key, value in expected_totals.items():
        if aggregate.get(key) != value:
            failures.append(f"aggregate_{key}_mismatch")
    if [row.get("configuration_id") for row in aggregate.get("cells", [])] != list(
        CONFIGURATIONS
    ):
        failures.append("configuration_order_mismatch")
    if any(row.get("disposition") != "checkpoint_pause" for row in aggregate["cells"]):
        failures.append("checkpoint_disposition_mismatch")
    if any(row.get("actor_calls") != 12 for row in aggregate["cells"]):
        failures.append("cell_actor_call_mismatch")
    if any(row.get("evaluation_passed") is not False for row in aggregate["cells"]):
        failures.append("unexpected_checkpoint_evaluation")
    if len({row.get("candidate_sha256") for row in aggregate["cells"]}) != 1:
        failures.append("candidate_hash_divergence")
    if _action_signature(reviews[CONFIGURATIONS[0]]) != _action_signature(
        reviews[CONFIGURATIONS[1]]
    ):
        failures.append("actor_action_sequence_divergence")

    cells: dict[str, Any] = {}
    for configuration_id in CONFIGURATIONS:
        review = reviews[configuration_id]
        lifecycle = review["interaction_lifecycle"]
        register = lifecycle["register"]
        relief = lifecycle["relief_events"]
        externalized = [
            result_id
            for event in relief
            for result_id in event["selected_result_ids"]
        ]
        actor = _actor_accounting(review)
        maintenance_events = lifecycle["maintenance_events"]
        admitted_claim_ids = [
            claim_id
            for event in maintenance_events
            for claim_id in event["admitted_claim_ids"]
        ]
        final_claim_ids = [claim["claim_id"] for claim in register["claims"]]
        cells[configuration_id] = {
            "action_sequence": _action_signature(review),
            "actor": actor,
            "candidate_sha256": aggregate["cells"][CONFIGURATIONS.index(configuration_id)][
                "candidate_sha256"
            ],
            "candidate_transitions": len(review["candidate_transitions"]),
            "checkpoint_evaluation_passed": False,
            "delivered_result_count": sum(
                row["first_delivered_call"] is not None for row in review["results"]
            ),
            "externalized_result_ids": externalized,
            "final_claim_count": len(final_claim_ids),
            "final_claim_ids": final_claim_ids,
            "final_register_sources": sorted(
                {claim["source_id"] for claim in register["claims"]}
            ),
            "maintenance_admitted_claim_count": len(admitted_claim_ids),
            "maintenance_calls": lifecycle["maintenance_calls"],
            "maintenance_dispositions": [
                event["disposition"] for event in maintenance_events
            ],
            "maintenance_rejected_claim_count": sum(
                len(event["rejected_claim_ids"]) for event in maintenance_events
            ),
            "maintenance_serialized_tokens": lifecycle[
                "maintenance_serialized_tokens"
            ],
            "pending_result_ids": review["pending_result_ids"],
            "recurrence": review["recurrence"],
            "relief_events": len(relief),
            "resident_result_ids": review["resident_result_ids"],
            "shed_admitted_claim_count": len(
                set(admitted_claim_ids) - set(final_claim_ids)
            ),
        }

    v0 = cells[CONFIGURATIONS[0]]
    v1 = cells[CONFIGURATIONS[1]]
    if v0["candidate_transitions"] or v1["candidate_transitions"]:
        failures.append("unexpected_candidate_transition")
    if v0["pending_result_ids"] != ["RESULT-012"] or v1["pending_result_ids"] != [
        "RESULT-012"
    ]:
        failures.append("pending_result_mismatch")
    if v0["maintenance_calls"] != 0 or v1["maintenance_calls"] != 6:
        failures.append("maintenance_call_mismatch")
    if v1["maintenance_rejected_claim_count"] != 0:
        failures.append("unexpected_maintenance_claim_rejection")
    if v1["maintenance_admitted_claim_count"] != 20:
        failures.append("maintenance_admission_count_mismatch")
    if v1["final_claim_count"] != 10 or v1["shed_admitted_claim_count"] != 10:
        failures.append("register_replacement_count_mismatch")
    if v0["relief_events"] != 4 or v1["relief_events"] != 6:
        failures.append("relief_event_count_mismatch")
    if len(v0["externalized_result_ids"]) != 5 or len(v1["externalized_result_ids"]) != 7:
        failures.append("externalized_result_count_mismatch")
    for key in (
        "exact_reopen_events",
        "exact_repeat_demand_events",
        "repeated_assistant_messages",
    ):
        if v0["recurrence"][key] or v1["recurrence"][key]:
            failures.append(f"unexpected_recurrence:{key}")

    receipt = {
        "schema": "trellis-refactored-interaction-tranche-audit-v0",
        "run_id": RUN_ID,
        "freeze_commit": FREEZE_COMMIT,
        "passed": not failures,
        "failures": failures,
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
        "aggregate": expected_totals,
        "run_seal_sha256": sha256_file(RUN_ROOT / "RUN_SEAL.json"),
        "actor_action_sequences_identical": _action_signature(reviews[CONFIGURATIONS[0]])
        == _action_signature(reviews[CONFIGURATIONS[1]]),
        "candidate_hashes_identical_and_unchanged": len(
            {row.get("candidate_sha256") for row in aggregate["cells"]}
        )
        == 1
        and not v0["candidate_transitions"]
        and not v1["candidate_transitions"],
        "cells": cells,
        "descriptive_differences": {
            "treatment_incremental_serialized_tokens": aggregate["cells"][1][
                "serialized_tokens"
            ]
            - aggregate["cells"][0]["serialized_tokens"],
            "treatment_incremental_externalized_results": len(
                v1["externalized_result_ids"]
            )
            - len(v0["externalized_result_ids"]),
            "treatment_cached_prompt_token_difference": v1["actor"][
                "cached_prompt_tokens"
            ]
            - v0["actor"]["cached_prompt_tokens"],
        },
        "claim_limits": [
            "The treatment was mechanically active but did not alter the twelve-call actor action sequence.",
            "Neither configuration produced artifact progress before the checkpoint.",
            "The final treatment register retained ten of twenty admitted claims because later chunks replaced prior claims from the same source slots.",
            "Later construction, verification, and utility remain unmeasured without a separately authorized continuation.",
        ],
    }
    write_json(OUTPUT, receipt)
    if failures:
        raise SystemExit("; ".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
