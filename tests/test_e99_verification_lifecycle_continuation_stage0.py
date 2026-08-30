from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_live_checkpoint_result_preserves_literal_quality_and_review() -> None:
    value = json.loads(
        (ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_CHECKPOINT_RESULT.json").read_text(
            encoding="utf-8"
        )
    )
    assert value["freeze_commit"] == "76091fc5885d25d31becccbb0edb8fc6a3681bac"
    assert value["actual_additional"]["actor_calls"] == 6
    assert value["actual_additional"]["serialized_tokens"] == 111_198
    assert value["candidate"]["closure_readiness"] == "not_ready"
    assert value["candidate"]["substantive_groups_met"] == ["T01_authority"]
    assert value["checkpoint"]["pending_result_id"] == "RESULT-024"
    assert value["qualitative_review"]["section_version_rejection_recovered"] is True
    assert value["qualitative_review"]["changed_candidate_rechecked"] is True
    assert value["qualitative_review"]["looping_observed"] is False
    assert value["qualitative_review"][
        "unchanged_policy_continuation_scientifically_eligible"
    ] is True


def test_continuation_stage0_hydrates_exact_checkpoint_without_gpu() -> None:
    value = json.loads(
        (ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_CONTINUATION_STAGE0.json").read_text(
            encoding="utf-8"
        )
    )
    assert value["passed"] is True
    assert value["failures"] == []
    assert value["parent"]["checkpoint_sha256"] == (
        "4395a0bfa3de1d676040373e35944b93fb7d2b326bd23f9ae4eb8faed3b5d4a6"
    )
    assert value["parent"]["candidate_sha256"] == (
        "d927aeecd8f1de60e9848f7f536dcdc31dbebbf83f3c79124f5d8306f609a633"
    )
    assert value["probe"]["included_result_ids"] == ["RESULT-024"]
    assert value["probe"]["accepted"] is True
    assert value["probe"]["candidate_unchanged"] is True
    assert value["probe"]["prompt_tokens"] == 19_247
    assert value["gpu_provider_calls"] == 0
    assert value["live_authorized"] is False


def test_continuation_contract_does_not_expand_original_envelope() -> None:
    contract = json.loads(
        (ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_CONTINUATION_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    remaining = contract["remaining_authorization_envelope"]
    tranche = contract["this_tranche"]
    assert tranche["maximum_actor_calls"] <= remaining["maximum_actor_calls"]
    assert tranche["maximum_maintenance_calls"] <= remaining["maximum_maintenance_calls"]
    assert tranche["maximum_provider_calls"] <= remaining["maximum_provider_calls"]
    assert tranche["maximum_serialized_tokens"] <= remaining["maximum_serialized_tokens"]
    assert tranche["automatic_continuation"] is False
