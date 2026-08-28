from __future__ import annotations

# ruff: noqa: E402

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json
from reactive_runtime.causal_activation import (
    activation_tax,
    detect_causal_fork_activation,
)
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
from reactive_runtime.seal import verify_tree_seal
from reactive_runtime.verification_causal_lifecycle import verification_frame
from tools.offline_tokenizer import OfflineTokenizer


CONTRACT_PATH = ROOT / "KEYSTONE_EVENT_FORK_CONTRACT.json"
OUTPUT_PATH = ROOT / "KEYSTONE_EVENT_FORK_PREFLIGHT.json"
PARENT_RUN = ROOT / "runs" / "2026-08-27-keystone-bounded-causal-pressure-screen-v0"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def row(
    call: int,
    action: str,
    *,
    before: str,
    after: str,
    result_kind: str | None = None,
    rejection_code: str | None = None,
    check_candidate: str | None = None,
) -> dict[str, Any]:
    return {
        "actor_call": call,
        "parsed_action": {"action": action},
        "candidate_sha256_before": before,
        "candidate_sha256_after": after,
        "result_id": None if result_kind is None else f"FIXTURE-{call:03d}",
        "result_kind": result_kind,
        "rejection_code": rejection_code,
        "current_check_binding": (
            None
            if check_candidate is None
            else {
                "evaluator_id": "keystone-evaluator-v0",
                "evaluated_candidate_sha256": check_candidate,
                "passed": False,
                "closure_readiness": "not_ready",
                "criterion_results": [],
                "blocking_requirements": ["fixture_blocker"],
                "raw_result_handle": "raw-tool://fixture/check",
            }
        ),
        "usage": {"total_tokens": 100},
    }


def trigger_fixture(initial_candidate: str) -> list[dict[str, Any]]:
    candidate = "1" * 64
    return [
        row(
            10,
            "upsert_decision_section",
            before=initial_candidate,
            after=candidate,
            result_kind="candidate_effect",
        ),
        row(
            11,
            "begin_verification",
            before=candidate,
            after=candidate,
            result_kind="phase_effect",
        ),
        row(
            12,
            "run_check",
            before=candidate,
            after=candidate,
            result_kind="check_observation",
            check_candidate=candidate,
        ),
        row(
            13,
            "replace_artifact_section",
            before=candidate,
            after=candidate,
            rejection_code="section_version_mismatch",
        ),
        row(
            14,
            "read_source",
            before=candidate,
            after=candidate,
            result_kind="source_observation",
        ),
    ]


def preflight(*, write_outputs: bool = True) -> dict[str, Any]:
    failures: list[str] = []
    contract = load(CONTRACT_PATH)
    parent = contract["parent"]
    locks = contract["source_locks"]

    expected_hashes = {
        PARENT_RUN / "RUN_SEAL.json": parent["run_seal_sha256"],
        PARENT_RUN / "PRESSURE_BOUNDARY.json": parent["pressure_boundary_sha256"],
        PARENT_RUN / "SCREEN_RESULT.json": parent["screen_result_sha256"],
        ROOT / "task_keystone" / "TASK_SOURCE_LOCK.json": locks[
            "task_source_lock_sha256"
        ],
        ROOT / "KEYSTONE_MODEL_PROFILE_LOCK.json": locks["model_profile_lock_sha256"],
        ROOT / "MODEL_PROFILE_LOCK.json": locks["tokenizer_projection_lock_sha256"],
    }
    for path, expected in expected_hashes.items():
        if not path.is_file():
            failures.append(f"missing:{path.relative_to(ROOT).as_posix()}")
        elif sha256_file(path) != expected:
            failures.append(f"sha256:{path.relative_to(ROOT).as_posix()}")

    seal_failures = verify_tree_seal(PARENT_RUN, PARENT_RUN / "RUN_SEAL.json")
    failures.extend(f"parent_seal:{value}" for value in seal_failures)

    boundary = load(PARENT_RUN / "PRESSURE_BOUNDARY.json")
    screen = load(PARENT_RUN / "SCREEN_RESULT.json")
    if boundary.get("pending_result_id") != parent["pending_result_id"]:
        failures.append("parent_pending_result")
    if boundary.get("candidate_sha256") != parent["candidate_sha256"]:
        failures.append("parent_candidate")
    if screen.get("actor_calls") != parent["actor_calls"]:
        failures.append("parent_actor_calls")
    if screen.get("serialized_tokens") != parent["serialized_tokens"]:
        failures.append("parent_serialized_tokens")
    if screen.get("pressure_qualified") is not False:
        failures.append("parent_was_not_a_negative_screen")
    if boundary.get("current_check_binding") is not None:
        failures.append("parent_has_current_check")
    milestone = boundary.get("candidate_construction_milestone") or {}
    if milestone.get("passed") is not False:
        failures.append("parent_candidate_already_constructed")

    tokenizer = OfflineTokenizer()
    messages = deepcopy(boundary["messages"])
    ledger = ResultLedger.from_dict(deepcopy(boundary["result_ledger"]))
    before_tokens = tokenizer.count_messages(messages)
    relief = positive_savings_first_fit_step(
        messages=messages,
        ledger=ledger,
        prompt_limit=int(boundary["prompt_limit"]),
        count_messages=tokenizer.count_messages,
        protected_result_ids=(str(boundary["pending_result_id"]),),
    )
    if before_tokens != boundary.get("ordinary_prospective_prompt_tokens"):
        failures.append("parent_prompt_recount")
    if (
        list(relief.selected_result_ids)
        != contract["common_continuation"]["first_relief_result_ids"]
    ):
        failures.append("common_first_fit_selection")
    if relief.prompt_tokens != boundary.get("counterfactual_relief_prompt_tokens"):
        failures.append("common_first_fit_prompt_tokens")
    if not relief.feasible:
        failures.append("common_first_fit_infeasible")

    pending_id = str(boundary["pending_result_id"])
    pending = ledger.get(pending_id)
    if messages[-1] != {"role": "user", "content": pending.exact_content}:
        failures.append("pending_result_message_binding")
    if (
        pending.previously_visible
        or pending.resident
        or pending.message_index is not None
    ):
        failures.append("pending_result_was_already_visible")
    ledger.mark_model_visible(
        pending_id,
        call_index=int(parent["actor_calls"]) + 1,
        message_index=len(messages) - 1,
    )
    if tokenizer.count_messages(messages) != relief.prompt_tokens:
        failures.append("pending_delivery_changed_prompt_bytes")

    initial_candidate = str(parent["candidate_sha256"])
    fixture = trigger_fixture(initial_candidate)
    activation = detect_causal_fork_activation(
        fixture, initial_candidate_sha256=initial_candidate
    )
    if not activation.qualified or activation.treatment_decision_call != 15:
        failures.append("event_trigger_positive_fixture")

    acquisition_only = [
        row(
            call,
            "read_source",
            before=initial_candidate,
            after=initial_candidate,
            result_kind="source_observation",
        )
        for call in range(1, 15)
    ]
    negative = detect_causal_fork_activation(
        acquisition_only, initial_candidate_sha256=initial_candidate
    )
    if negative.qualified:
        failures.append("count_or_pressure_activated_treatment")

    v0 = verification_frame(
        "V0_CURRENT_ONLY", fixture, history_handle="history://keystone/fixture"
    )
    v1 = verification_frame(
        "V1_BOUNDED_CAUSAL_CONTINUITY",
        fixture,
        history_handle="history://keystone/fixture",
    )
    if v0.get("active_rejected_action") is not None or v0.get("recurrence") is not None:
        failures.append("v0_retained_causal_treatment")
    if (v1.get("active_rejected_action") or {}).get("rejection_code") != (
        "section_version_mismatch"
    ):
        failures.append("v1_lost_active_rejection")

    tax = activation_tax(
        activation,
        parent_calls=int(parent["actor_calls"]),
        parent_serialized_tokens=int(parent["serialized_tokens"]),
        continuation_trace=fixture,
    )

    result = {
        "schema": "keystone-event-triggered-causal-continuation-preflight-v0",
        "passed": not failures,
        "failures": failures,
        "model_calls": 0,
        "provider_calls": 0,
        "gpu_authorized": False,
        "contract_sha256": sha256_file(CONTRACT_PATH),
        "parent": {
            "run_id": parent["run_id"],
            "seal_verified": not seal_failures,
            "actor_calls": parent["actor_calls"],
            "serialized_tokens": parent["serialized_tokens"],
            "candidate_sha256": parent["candidate_sha256"],
            "pending_result_id": pending_id,
        },
        "common_continuation_boundary": {
            "ordinary_prompt_tokens": before_tokens,
            "selected_relief_result_ids": list(relief.selected_result_ids),
            "relieved_prompt_tokens": relief.prompt_tokens,
            "prompt_limit": boundary["prompt_limit"],
            "pending_result_model_visible_call": pending.first_model_visible_call,
            "pending_result_resident": pending.resident,
        },
        "event_activation": activation.as_dict(),
        "acquisition_only_activation": negative.as_dict(),
        "frame_difference": {
            "v0_active_rejected_action": v0.get("active_rejected_action"),
            "v0_recurrence": v0.get("recurrence"),
            "v1_active_rejected_action": v1.get("active_rejected_action"),
            "v1_recurrence": v1.get("recurrence"),
        },
        "activation_tax_fixture": tax,
        "claim_limits": [
            "offline preflight proves exact prefix continuity and event-trigger mechanics only",
            "no evidence yet that the live actor reaches the trigger",
            "no evidence yet that V1 improves repair or closure",
            "no mechanism is promoted into the donor-preserving product path",
        ],
    }
    if write_outputs:
        write_json(OUTPUT_PATH, result)
    return result


def main() -> int:
    result = preflight(write_outputs=True)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
