from __future__ import annotations

import json
from pathlib import Path

from reactive_runtime.keystone_world import KeystoneWorld
from reactive_runtime.configuration import causal_verification_actor_actions
from tools import keystone_stage0
from tools import run_keystone_pressure_screen


ROOT = Path(__file__).resolve().parents[1]


def test_keystone_task_is_fresh_locked_and_fourteen_source() -> None:
    lock = json.loads(
        (ROOT / "task_keystone" / "TASK_SOURCE_LOCK.json").read_text(
            encoding="utf-8"
        )
    )
    assert lock["task_id"] == "keystone-rail-restoration-decision-v0"
    assert len(lock["source_custody"]) == 14
    assert len({row["evidence_domain"] for row in lock["source_custody"]}) == 14
    assert KeystoneWorld.__name__ == "KeystoneWorld"


def test_stage0_passes_with_authentic_pressure_and_zero_calls() -> None:
    assert keystone_stage0.main() == 0
    result = json.loads(
        (ROOT / "KEYSTONE_STAGE0_PREFLIGHT.json").read_text(encoding="utf-8")
    )
    assert result["passed"] is True
    assert result["model_calls"] == 0
    assert result["provider_calls"] == 0
    pressure = result["prospective_pressure"]
    assert pressure["delivered_source_count"] >= 10
    assert pressure["ordinary_prompt_tokens"] > result["prompt_limit"]
    assert pressure["relieved_prompt_tokens"] <= result["prompt_limit"]
    assert pressure["selected_result_ids"] == ["RESULT-001"]


def test_v0_v1_share_repair_outcome_but_differ_in_causal_continuity() -> None:
    result = json.loads(
        (ROOT / "KEYSTONE_STAGE0_PREFLIGHT.json").read_text(encoding="utf-8")
    )
    rows = {row["configuration_id"]: row for row in result["provider_free_lifecycles"]}
    v0 = rows["V0_CURRENT_ONLY"]
    v1 = rows["V1_BOUNDED_CAUSAL_CONTINUITY"]
    assert v0["frame_after_recurrence_observation"]["active_rejected_action"] is None
    assert v0["frame_after_recurrence_observation"]["recurrence"] is None
    assert v1["frame_after_recurrence_observation"]["active_rejected_action"][
        "rejection_code"
    ] == "section_version_mismatch"
    assert v1["frame_after_recurrence_observation"]["recurrence"][
        "count_in_current_candidate_epoch"
    ] == 2
    assert v0["final_candidate_sha256"] == v1["final_candidate_sha256"]
    assert all(row["recheck_passed"] and row["submitted"] for row in rows.values())
    assert all(
        row["independent_readiness"]["closure_readiness"] == "ready"
        for row in rows.values()
    )


def test_red_team_and_common_bound_repair_qualified() -> None:
    result = json.loads(
        (ROOT / "KEYSTONE_STAGE0_PREFLIGHT.json").read_text(encoding="utf-8")
    )
    assert all(row["caught"] for row in result["red_team"])
    assert all(
        row["valid_repair_action_tokens"] <= 1200
        for row in result["provider_free_lifecycles"]
    )
    assert max(
        max(row["prompt_tokens_after_observation"], row["prompt_tokens_after_recheck"])
        for row in result["provider_free_lifecycles"]
    ) <= result["prompt_limit"]
    assert "replace_artifact_section" in causal_verification_actor_actions(
        "V1_BOUNDED_CAUSAL_CONTINUITY", phase="verification"
    )


def test_fixture_readiness_is_candidate_bound_and_not_reused_for_measurement() -> None:
    adjudication = json.loads(
        (ROOT / "KEYSTONE_STAGE0_READINESS_ADJUDICATION.json").read_text(
            encoding="utf-8"
        )
    )
    result = json.loads(
        (ROOT / "KEYSTONE_STAGE0_PREFLIGHT.json").read_text(encoding="utf-8")
    )
    assert adjudication["candidate_sha256"] == result["provider_free_lifecycles"][0][
        "final_candidate_sha256"
    ]
    assert adjudication["closure_readiness"] == "ready"
    assert adjudication["applies_to_future_measured_candidates"] is False


def test_pressure_screen_is_frozen_but_not_authorized() -> None:
    contract = json.loads(
        (ROOT / "KEYSTONE_PRESSURE_SCREEN_CONTRACT.json").read_text(encoding="utf-8")
    )
    authorization = json.loads(
        (ROOT / "KEYSTONE_PRESSURE_SCREEN_AUTHORIZATION_REQUEST.json").read_text(
            encoding="utf-8"
        )
    )
    assert run_keystone_pressure_screen.RUN_ID == contract["run_id"]
    assert run_keystone_pressure_screen.MAX_CALLS == 30
    assert contract["treatment_present"] is False
    assert contract["gpu_authorized"] is False
    assert authorization["authorized"] is False
    assert authorization["authorized_freeze_commit"] is None


def test_docs_preserve_claim_limits_and_full_lifecycle() -> None:
    plan = (ROOT / "KEYSTONE_STAGE0_PLAN.md").read_text(encoding="utf-8")
    result = (ROOT / "KEYSTONE_STAGE0_RESULT.md").read_text(encoding="utf-8")
    assert "viable end-to-end configurations" in plan
    assert "not Orchard with renamed sources" in plan
    assert "unresolved rejection" in result
    assert "does not show" in result
    assert "No measured V0/V1 runner" in result
