from __future__ import annotations

import json
from pathlib import Path

from reactive_runtime.seal import verify_tree_seal


ROOT = Path(__file__).resolve().parents[1]
RUN = (
    ROOT
    / "qualification_runs"
    / "2026-08-29-trellis-e97-verification-lifecycle-scout-v0"
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def actor_response(call: int) -> dict:
    return load(RUN / "tranche-001" / f"call-{call:03d}" / "actor" / "RESPONSE.json")


def test_live_result_is_sealed_bounded_and_not_ready() -> None:
    assert verify_tree_seal(RUN, RUN / "RUN_SEAL.json") == ()
    result = load(ROOT / "TRELLIS_E97_VERIFICATION_LIFECYCLE_SCOUT_RESULT.json")
    assert result["freeze_commit"] == "520d8237e42e313fb014ad146aefb4c51feb8a3e"
    assert result["actual"]["additional_actor_calls"] == 4
    assert result["actual"]["additional_provider_calls"] == 4
    assert result["actual"]["additional_serialized_tokens"] == 82_646
    assert result["actual"]["prospective_next_prompt_tokens"] == 23_811
    assert result["actual"]["runtime_released"] is True
    assert result["candidate"]["closure_readiness"] == "not_ready"
    assert result["candidate"]["substantive_requirement_groups_passed"] == 0
    assert result["candidate"]["submitted"] is False


def test_live_calls_cross_construction_and_phase_but_not_check() -> None:
    call19 = actor_response(19)
    call20 = actor_response(20)
    assert call19["finish_reason"] == "stop"
    assert json.loads(call19["content"])["action"] == "upsert_decision_section"
    assert call20["finish_reason"] == "stop"
    assert json.loads(call20["content"])["action"] == "begin_verification"

    call21_request = load(
        RUN / "tranche-001" / "call-021" / "actor" / "REQUEST.json"
    )
    rendered = "\n".join(str(message["content"]) for message in call21_request["messages"])
    assert '"action":"run_check"' not in rendered
    assert '"action":"replace_artifact_section"' not in rendered
    assert '"check_binding":null' in rendered


def test_two_length_rejections_are_exact_prefix_recurrence() -> None:
    call21 = actor_response(21)
    call22 = actor_response(22)
    assert call21["finish_reason"] == "length"
    assert call22["finish_reason"] == "length"
    assert call21["usage"]["completion_tokens"] == 4_096
    assert call22["usage"]["completion_tokens"] == 4_096
    assert len(call21["content"]) == 18_963
    assert len(call22["content"]) == 18_969
    assert call22["content"].startswith(call21["content"])
    assert call21["content"].count(
        "Execution, rollback, verification, and closure (repeated)"
    ) == 6


def test_external_checkpoint_evaluation_remains_not_ready() -> None:
    value = load(RUN / "EXTERNAL_CHECKPOINT_EVALUATION.json")
    evaluation = value["evaluation"]
    assert evaluation["candidate_sha256"] == (
        "8a7a6ec5bd77dcd758b20e2577817b3164c14546ab431da30b42715186ad980a"
    )
    assert evaluation["decision_word_count"] == 1_145
    assert evaluation["closure_readiness"] == "not_ready"
    assert evaluation["passed"] is False
    for criterion in (f"T0{index}_{name}" for index, name in enumerate(
        (
            "authority",
            "heat",
            "power",
            "water",
            "clinic_shelter",
            "transit_comms",
            "supply_labor",
            "currentness",
        ),
        start=1,
    )):
        row = next(item for item in evaluation["criterion_results"] if item["criterion_id"] == criterion)
        assert row["status"] == "fail"
