from __future__ import annotations

import json
from pathlib import Path

from reactive_runtime.seal import verify_tree_seal


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "2026-08-29-trellis-refactored-interaction-continuation-v0"
RUN_ROOT = ROOT / "qualification_runs" / RUN_ID


def test_live_continuation_is_sealed_and_within_authorization() -> None:
    assert verify_tree_seal(RUN_ROOT, RUN_ROOT / "RUN_SEAL.json") == ()
    audit = json.loads(
        (ROOT / "TRELLIS_REFACTORED_INTERACTION_CONTINUATION_AUDIT.json").read_text(
            encoding="utf-8"
        )
    )
    assert audit["passed"] is True
    assert audit["freeze_commit"] == "18e17806e906d57943ab9b7461def708084d69b1"
    assert audit["actual_additional"] == {
        "actor_calls": 18,
        "maintenance_calls": 5,
        "provider_calls": 23,
        "serialized_tokens": 383176,
    }
    limits = audit["authorization_limits"]
    assert limits["maximum_actor_calls"] == 24
    assert limits["maximum_maintenance_calls"] == 6
    assert limits["maximum_provider_calls"] == 30
    assert limits["maximum_serialized_tokens"] == 520028
    assert limits["attempts_per_call"] == 1
    assert limits["retries"] == 0


def test_audit_preserves_recurrence_construction_and_capacity_migration() -> None:
    audit = json.loads(
        (ROOT / "TRELLIS_REFACTORED_INTERACTION_CONTINUATION_AUDIT.json").read_text(
            encoding="utf-8"
        )
    )
    v0 = audit["cells"]["V0_EXACT_ARTIFACT"]
    v1 = audit["cells"]["V1_TEMPORARY_PROVENANCE_SCAFFOLD"]

    assert v0["disposition"] == "checkpoint_pause"
    assert v0["catalog_replay_actions"] == 12
    assert v0["candidate_transitions"] == 0
    assert v0["cumulative_actor_calls"] == 24

    assert v1["disposition"] == "capacity_blocked"
    assert v1["candidate_transitions"] == 6
    assert v1["candidate_sha256"] == (
        "d133a537f9aef2b3635359316743f39196095c0be3dc6a4b5c86444cdc8a52d9"
    )
    assert v1["closure_readiness"] == "not_ready"
    assert v1["next_prompt_tokens"] == 21041
    effects = v1["candidate_effects"]
    assert all(effect["relief_eligible"] is False for effect in effects)
    assert [
        effect["result_id"]
        for effect in effects
        if effect["delivery_state"] == "delivered_resident"
    ] == [
        "RESULT-013",
        "RESULT-014",
        "RESULT-015",
        "RESULT-016",
        "RESULT-017",
    ]
    assert [
        effect["result_id"]
        for effect in effects
        if effect["delivery_state"] == "pending"
    ] == ["RESULT-018"]


def test_result_and_qualitative_appendix_state_the_claim_limits() -> None:
    result = (ROOT / "TRELLIS_REFACTORED_INTERACTION_CONTINUATION_RESULT.md").read_text(
        encoding="utf-8"
    )
    appendix = (
        ROOT / "TRELLIS_REFACTORED_INTERACTION_CONTINUATION_QUALITATIVE_APPENDIX.md"
    ).read_text(encoding="utf-8")
    assert "Neither achieved useful completion" in result
    assert "whole evolving configuration" in result
    assert "append-only candidate effects" in result
    assert "not to the register in isolation" in result
    assert "V0 calls 13–24" in appendix
    assert "Attempted call 19 — no provider call" in appendix
    assert "does not expose hidden model reasoning" in appendix
