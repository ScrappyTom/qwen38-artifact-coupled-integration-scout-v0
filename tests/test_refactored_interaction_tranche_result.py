from __future__ import annotations

import json
from pathlib import Path

from reactive_runtime.seal import verify_tree_seal


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "2026-08-29-trellis-refactored-interaction-tranche-v0"
RUN_ROOT = ROOT / "qualification_runs" / RUN_ID


def test_live_interaction_run_is_sealed_and_within_authorization() -> None:
    assert verify_tree_seal(RUN_ROOT, RUN_ROOT / "RUN_SEAL.json") == ()
    result = json.loads(
        (RUN_ROOT / "INTERACTION_TRANCHE_RESULT.json").read_text(encoding="utf-8")
    )
    assert result["freeze_commit"] == "381e44c9eb3c3c10a793903155c2482f5f8c570f"
    assert result["actor_calls"] == 24
    assert result["maintenance_calls"] == 6
    assert result["provider_calls"] == 30
    assert result["serialized_tokens"] == 379972
    assert [cell["disposition"] for cell in result["cells"]] == [
        "checkpoint_pause",
        "checkpoint_pause",
    ]


def test_audit_preserves_the_joint_negative_checkpoint_result() -> None:
    audit = json.loads(
        (ROOT / "TRELLIS_REFACTORED_INTERACTION_TRANCHE_AUDIT.json").read_text(
            encoding="utf-8"
        )
    )
    assert audit["passed"] is True
    assert audit["actor_action_sequences_identical"] is True
    assert audit["candidate_hashes_identical_and_unchanged"] is True
    v0 = audit["cells"]["V0_EXACT_ARTIFACT"]
    v1 = audit["cells"]["V1_TEMPORARY_PROVENANCE_SCAFFOLD"]
    assert v0["maintenance_calls"] == 0
    assert v1["maintenance_calls"] == 6
    assert v1["maintenance_admitted_claim_count"] == 20
    assert v1["final_claim_count"] == 10
    assert v1["shed_admitted_claim_count"] == 10
    assert v0["candidate_transitions"] == v1["candidate_transitions"] == 0
    assert v0["pending_result_ids"] == v1["pending_result_ids"] == ["RESULT-012"]
