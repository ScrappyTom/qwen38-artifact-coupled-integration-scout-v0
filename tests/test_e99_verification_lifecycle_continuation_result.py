from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = (
    ROOT
    / "qualification_runs"
    / "2026-08-30-trellis-e99-verification-lifecycle-continuation-v1"
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_continuation_result_matches_sealed_literal_outcome() -> None:
    result = load(ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_CONTINUATION_RESULT.json")
    literal = load(RUN / "CONTINUATION_RESULT.json")
    tranche = load(RUN / "tranche-002" / "TRANCHE_RESULT.json")
    timing = load(RUN / "tranche-002" / "TRANCHE_TIMING.json")

    assert result["freeze_commit"] == literal["freeze_commit"]
    assert result["candidate"]["sha256"] == literal["candidate_sha256"]
    assert result["actual"] == {
        "actor_calls": literal["actor_calls"],
        "maintenance_calls": literal["maintenance_calls"],
        "provider_calls": literal["provider_calls"],
        "serialized_tokens": literal["serialized_tokens"],
    }
    assert tranche["disposition"] == "capacity_blocked"
    assert timing[-1] == {
        "actor_call": 27,
        "actor_elapsed_ms": None,
        "actor_provider_attempts": 0,
        "cumulative_maintenance_calls": 11,
        "disposition": "capacity_blocked",
        "prompt_tokens": 21318,
    }


def test_continuation_preserves_frozen_evaluation_and_prospective_correction() -> None:
    frozen = load(RUN / "EXTERNAL_CHECKPOINT_EVALUATION.json")["evaluation"]
    result = load(ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_CONTINUATION_RESULT.json")
    decision = (
        RUN
        / "trajectory"
        / "world"
        / "candidate"
        / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
    ).read_text(encoding="utf-8")

    assert frozen["passed"] is False
    assert frozen["closure_readiness"] == "not_ready"
    assert result["candidate"]["corrected_offline_t08_status"] == "pass"
    assert "independent authorized acceptance is required" in decision
    assert "[REVIEW].## Power, water" in decision
