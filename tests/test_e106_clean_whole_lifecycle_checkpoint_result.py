from __future__ import annotations

import json
from pathlib import Path

from reactive_runtime.seal import verify_tree_seal


ROOT = Path(__file__).resolve().parents[1]
RUN = (
    ROOT
    / "qualification_runs"
    / "2026-08-30-trellis-clean-whole-lifecycle-v0"
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_checkpoint_summary_matches_sealed_live_records() -> None:
    summary = load(ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CHECKPOINT_RESULT.json")
    literal = load(RUN / "TRANCHE_RESULT.json")
    review = load(RUN / "tranche-001" / "MECHANICAL_REVIEW.json")

    assert verify_tree_seal(RUN, RUN / "RUN_SEAL.json") == ()
    assert summary["freeze_commit"] == literal["freeze_commit"]
    assert summary["disposition"] == literal["disposition"] == "checkpoint_pause"
    assert summary["actor_calls"] == literal["actor_calls"] == 12
    assert summary["maintenance_calls"] == literal["maintenance_calls"] == 6
    assert summary["provider_calls"] == literal["provider_calls"] == 18
    assert summary["serialized_tokens"] == literal["serialized_tokens"] == 205399
    assert review["failed_calls"] == []
    assert review["failed_invocations"] == []
    assert review["pending_result_ids"] == ["RESULT-012"]


def test_live_trajectory_is_novel_acquisition_not_recurrence_or_work() -> None:
    review = load(RUN / "tranche-001" / "MECHANICAL_REVIEW.json")
    dispositions = review["action_dispositions"]

    assert len(dispositions) == 12
    assert all(row["status"] == "accepted" for row in dispositions)
    assert all(row["action"]["action"] == "read_batch" for row in dispositions)
    assert review["recurrence"] == {
        "exact_reopen_events": 0,
        "exact_repeat_demand_events": 0,
        "repeated_assistant_messages": 0,
        "unchanged_candidate_transitions": 12,
    }
    assert review["interaction_lifecycle"]["maintenance_calls"] == 6
    assert len(review["interaction_lifecycle"]["maintenance_events"]) == 6
    assert all(
        row["disposition"] == "full_admission"
        for row in review["interaction_lifecycle"]["maintenance_events"]
    )
    assert len(review["interaction_lifecycle"]["register"]["claims"]) == 10


def test_checkpoint_is_not_ready_and_not_terminal() -> None:
    literal = load(RUN / "TRANCHE_RESULT.json")
    review = load(RUN / "tranche-001" / "MECHANICAL_REVIEW.json")

    assert literal["candidate_sha256"] == (
        "e7a12171c6523e8881fddf7cdcd0cba3e99f97ff7ef1db9770f7295a596db0ba"
    )
    assert literal["readiness"]["closure_readiness"] == "not_ready"
    assert literal["automatic_continuation"] is False
    assert review["terminal"] is None
    assert review["remaining_call_budget"] == 36
    assert review["remaining_serialized_token_budget"] == 1294601
