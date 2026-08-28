from __future__ import annotations

import json
import tempfile
from copy import deepcopy
from pathlib import Path

from reactive_runtime.anchored_provenance import AnchoredProvenanceRegister
from reactive_runtime.canonical import sha256_file
from reactive_runtime.causal_activation import detect_causal_fork_activation
from reactive_runtime.keystone_event_fork import (
    CommonForkState,
    branch_binding,
    clone_common_state,
)
from reactive_runtime.keystone_world import KeystoneWorld
from reactive_runtime.records import ResultLedger
from reactive_runtime.verification_causal_lifecycle import verification_frame
from reactive_runtime.world import ActionRejected
from tools.keystone_stage0 import (
    TASK,
    bound_repair_action,
    execute_and_record,
    fixture_decision,
    fixture_ledger,
    trace_row,
)
from tools.preflight_keystone_event_fork import preflight
from tools.run_keystone_event_fork import trace_metrics
from tools.qualify_keystone_event_fork_runner import qualify


ROOT = Path(__file__).resolve().parents[1]


def test_event_fork_preflight_preserves_parent_and_retires_count_activation() -> None:
    result = preflight(write_outputs=False)
    assert result["passed"] is True
    assert result["failures"] == []
    assert result["model_calls"] == 0
    assert result["provider_calls"] == 0
    assert result["gpu_authorized"] is False
    assert result["parent"]["seal_verified"] is True
    assert result["parent"]["actor_calls"] == 9
    assert result["parent"]["serialized_tokens"] == 102_009
    assert result["common_continuation_boundary"] == {
        "ordinary_prompt_tokens": 22_267,
        "selected_relief_result_ids": ["RESULT-001"],
        "relieved_prompt_tokens": 20_648,
        "prompt_limit": 20_992,
        "pending_result_model_visible_call": 10,
        "pending_result_resident": True,
    }
    assert result["event_activation"]["qualified"] is True
    assert result["acquisition_only_activation"]["qualified"] is False


def test_contract_has_one_integrated_run_and_no_product_promotion() -> None:
    contract = json.loads(
        (ROOT / "KEYSTONE_EVENT_FORK_CONTRACT.json").read_text(encoding="utf-8")
    )
    authorization = json.loads(
        (ROOT / "KEYSTONE_EVENT_FORK_AUTHORIZATION_REQUEST.json").read_text(
            encoding="utf-8"
        )
    )
    frozen_preflight = json.loads(
        (ROOT / "KEYSTONE_EVENT_FORK_PREFLIGHT.json").read_text(encoding="utf-8")
    )
    assert frozen_preflight["contract_sha256"] == sha256_file(
        ROOT / "KEYSTONE_EVENT_FORK_CONTRACT.json"
    )
    assert contract["activation"]["unit"] == "exact_lifecycle_event_sequence"
    assert "source_count" in contract["activation"]["excluded_units"]
    assert contract["common_continuation"]["positive_savings_first_fit_relief"] is True
    assert contract["budgets"]["maximum_common_continuation_calls"] == 18
    assert contract["budgets"]["maximum_calls_per_arm"] == 8
    assert contract["runner"]["runner_sha256"] == sha256_file(
        ROOT / contract["runner"]["path"]
    )
    assert contract["runner"]["qualification_sha256"] == sha256_file(
        ROOT / contract["runner"]["qualification_path"]
    )
    assert contract["promotion"] == {
        "product_default_authorized": False,
        "custom_controller_authorized": False,
        "new_acquisition_gate_authorized": False,
        "same_task_retry_authorized": False,
    }
    assert contract["gpu_authorized"] is False
    assert authorization["authorized"] is False
    assert authorization["authorized_freeze_commit"] is None


def test_effect_uptake_requires_a_later_actor_decision() -> None:
    effect = {
        "actor_call": 20,
        "result_id": "RESULT-020",
        "result_kind": "candidate_effect",
        "candidate_sha256_after": "1" * 64,
    }
    final_effect = trace_metrics([effect], fork_trace_length=0)
    assert final_effect["alternative_repair"] is not None
    assert final_effect["effect_uptake"] is False

    later_decision = {
        "actor_call": 21,
        "result_id": "RESULT-021",
        "result_kind": "check_observation",
        "current_check_binding": {"currency": "current"},
    }
    delivered_effect = trace_metrics([effect, later_decision], fork_trace_length=0)
    assert delivered_effect["effect_uptake"] is True


def test_integrated_runner_qualifies_provider_free_without_gpu_authority() -> None:
    result = qualify(write_output=False)
    assert result["passed"] is True
    assert result["model_calls"] == 0
    assert result["provider_calls"] == 0
    assert result["gpu_authorized"] is False
    assert result["branch_bindings_equal_before_projection"] is True
    assert result["branch_mutable_state_independent"] is True
    assert result["bound_repair_live_schema_closed"] is True
    assert len(result["runner_sha256"]) == 64
    assert result["runner_source_bound"] is True


def test_routing_documents_keep_product_and_research_separate() -> None:
    reset = (ROOT / "PROJECT_ROUTING_RESET.md").read_text(encoding="utf-8")
    plan = (ROOT / "KEYSTONE_EVENT_FORK_PLAN.md").read_text(encoding="utf-8")
    transfer = (
        ROOT / "NEXT_SYSTEM_INTERACTION_BOUNDED_CAUSAL_VERIFICATION_TRANSFER.md"
    ).read_text(encoding="utf-8")
    assert "donor-preserving writable integration" in reset
    assert "There will be no replacement ten-source screen" in reset
    assert "If the exact trigger never occurs" in reset
    assert "Source count, evidence-domain count" in plan
    assert "one attempt per model call" in plan
    assert "No GPU call is authorized" in transfer


def test_provider_free_common_trigger_clones_exact_independent_branches() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        world = KeystoneWorld(TASK, root / "common")
        ledger = ResultLedger()
        initial = world.candidate_sha256
        trace: list[dict[str, object]] = []

        evidence = execute_and_record(
            world,
            ledger,
            {"action": "replace_evidence_ledger", "content": fixture_ledger()},
            "RESULT-001",
            1,
        )
        trace.append(
            trace_row(
                actor_call=1,
                action={"action": "replace_evidence_ledger"},
                candidate_before=initial,
                candidate_after=world.candidate_sha256,
                result_id=evidence.result_id,
                result_kind=evidence.result_kind,
            )
        )
        before_decision = world.candidate_sha256
        decision = execute_and_record(
            world,
            ledger,
            {"action": "replace_decision", "content": fixture_decision(defective=True)},
            "RESULT-002",
            2,
        )
        trace.append(
            trace_row(
                actor_call=2,
                action={"action": "replace_decision"},
                candidate_before=before_decision,
                candidate_after=world.candidate_sha256,
                result_id=decision.result_id,
                result_kind=decision.result_kind,
            )
        )
        phase_candidate = world.candidate_sha256
        phase = execute_and_record(
            world, ledger, {"action": "begin_verification"}, "RESULT-003", 3
        )
        trace.append(
            trace_row(
                actor_call=3,
                action={"action": "begin_verification"},
                candidate_before=phase_candidate,
                candidate_after=world.candidate_sha256,
                result_id=phase.result_id,
                result_kind=phase.result_kind,
            )
        )
        check_candidate = world.candidate_sha256
        check = execute_and_record(
            world, ledger, {"action": "run_check"}, "RESULT-004", 4
        )
        trace.append(
            trace_row(
                actor_call=4,
                action={"action": "run_check"},
                candidate_before=check_candidate,
                candidate_after=world.candidate_sha256,
                result_id=check.result_id,
                result_kind=check.result_kind,
                current_check_binding=world.current_check_binding(),
            )
        )
        valid_repair = bound_repair_action(world)
        rejected_repair = deepcopy(valid_repair)
        rejected_repair["expected_section_sha256"] = "0" * 64
        rejection = None
        try:
            world.execute(rejected_repair, result_id="RESULT-005", ledger=ledger)
        except ActionRejected as exc:
            rejection = exc.code
        trace.append(
            trace_row(
                actor_call=5,
                action=rejected_repair,
                candidate_before=world.candidate_sha256,
                candidate_after=world.candidate_sha256,
                rejection_code=rejection,
                current_check_binding=world.current_check_binding(),
            )
        )
        observation_candidate = world.candidate_sha256
        observation = execute_and_record(
            world,
            ledger,
            {
                "action": "read_source",
                "source_id": "POWER",
                "start_line": 1,
                "end_line": 20,
            },
            "RESULT-006",
            6,
        )
        trace.append(
            trace_row(
                actor_call=6,
                action={
                    "action": "read_source",
                    "source_id": "POWER",
                    "start_line": 1,
                    "end_line": 20,
                },
                candidate_before=observation_candidate,
                candidate_after=world.candidate_sha256,
                result_id=observation.result_id,
                result_kind=observation.result_kind,
                current_check_binding=world.current_check_binding(),
            )
        )
        activation = detect_causal_fork_activation(
            trace, initial_candidate_sha256=initial
        )
        assert activation.qualified is True
        assert activation.treatment_decision_call == 7

        common = CommonForkState(
            messages=[{"role": "user", "content": observation.exact_content}],
            ledger=ledger,
            trace=trace,
            register=AnchoredProvenanceRegister(),
            phase="verification",
            pending_result_id=observation.result_id,
            next_result_ordinal=7,
            latest_effect_result_id=decision.result_id,
            actor_calls_completed=6,
            model_calls_completed=0,
            serialized_tokens=0,
        )
        left = clone_common_state(common, world, root / "left")
        right = clone_common_state(common, world, root / "right")
        assert branch_binding(left) == common.binding(world)
        assert branch_binding(right) == common.binding(world)

        v0 = verification_frame(
            "V0_CURRENT_ONLY", left.trace, history_handle="history://fixture"
        )
        v1 = verification_frame(
            "V1_BOUNDED_CAUSAL_CONTINUITY",
            right.trace,
            history_handle="history://fixture",
        )
        assert v0["active_rejected_action"] is None
        assert v1["active_rejected_action"]["rejection_code"] == (
            "section_version_mismatch"
        )

        before_left = left.world.candidate_sha256
        left.world.execute(valid_repair, result_id="RESULT-007", ledger=left.ledger)
        assert left.world.candidate_sha256 != before_left
        assert right.world.candidate_sha256 == world.candidate_sha256
