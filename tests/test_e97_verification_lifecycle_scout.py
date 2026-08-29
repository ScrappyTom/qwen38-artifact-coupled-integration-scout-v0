from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from host_refactor.lifecycle_scout.fixtures import NoOpMaintenanceFixture
from host_refactor.lifecycle_scout.migration import (
    DONOR_CANDIDATE_SHA256,
    DONOR_CHECKPOINT_SHA256,
    EXPECTED_EXTERNALIZED_EFFECTS,
    EXPECTED_PENDING_EFFECT,
    _verify_checkpoint,
    migrate_e96_donor,
)
from host_refactor.model import DeliveryState
from reactive_runtime.canonical import load_json
from tools.build_e97_verification_lifecycle_stage0 import build
from tools.offline_tokenizer import OfflineTokenizer


ROOT = Path(__file__).resolve().parents[1]


def test_donor_migration_is_exact_feasible_and_new_manifest_bound(
    tmp_path: Path,
) -> None:
    tokenizer = OfflineTokenizer()
    outcome = migrate_e96_donor(
        repository_root=ROOT,
        trajectory_root=tmp_path / "trajectory",
        count_messages=tokenizer.count_messages,
        count_text=tokenizer.count_text,
        maintenance_complete=NoOpMaintenanceFixture(),
        checkpoint_output=tmp_path / "CHECKPOINT.json",
        receipt_output=tmp_path / "MIGRATION.json",
    )
    state = outcome.kernel.project()
    assert outcome.receipt["donor_checkpoint_sha256"] == DONOR_CHECKPOINT_SHA256
    assert outcome.receipt["candidate_sha256"] == DONOR_CANDIDATE_SHA256
    assert outcome.receipt["externalized_applied_effect_ids"] == list(
        EXPECTED_EXTERNALIZED_EFFECTS
    )
    assert outcome.receipt["pending_effect_id"] == EXPECTED_PENDING_EFFECT
    assert outcome.receipt["prompt_tokens"] == 19_116
    assert outcome.receipt["prompt_tokens"] <= outcome.host.configuration.prompt_limit
    assert all(
        state.results[result_id].delivery_state
        is DeliveryState.DELIVERED_EXTERNAL
        for result_id in EXPECTED_EXTERNALIZED_EFFECTS
    )
    assert (
        state.results[EXPECTED_PENDING_EFFECT].delivery_state
        is DeliveryState.PENDING
    )
    hydrated, counters, domain = outcome.host.checkpoint.hydrate_with_domain(
        load_json(tmp_path / "CHECKPOINT.json"), outcome.host.configuration
    )
    assert hydrated.as_dict() == outcome.kernel.as_dict()
    assert counters == outcome.counters
    assert domain == {
        "interaction": outcome.orchestrator.lifecycle.as_dict(),
        "trellis": outcome.adapter.snapshot(),
    }


def test_donor_checkpoint_tampering_fails_closed() -> None:
    source = load_json(
        ROOT
        / "qualification_runs"
        / "2026-08-29-trellis-refactored-interaction-continuation-v0"
        / "cells"
        / "V1_TEMPORARY_PROVENANCE_SCAFFOLD"
        / "tranche-002"
        / "CHECKPOINT.json"
    )
    tampered = deepcopy(source)
    tampered["counters"]["serialized_tokens"] += 1
    with pytest.raises(ValueError, match="checkpoint hash mismatch"):
        _verify_checkpoint(tampered)


def test_stage0_provider_free_lifecycle_qualifies() -> None:
    result = build()
    assert result["passed"] is True, result["failures"]
    assert result["donor_evaluation"]["closure_readiness"] == "not_ready"
    assert result["candidate_changed"] is True
    assert result["check_sequence"][0]["passed"] is False
    assert result["check_sequence"][1]["passed"] is True
    assert result["final_evaluation"]["passed"] is True
    assert result["disposition"] == "completed"
    assert result["additional_actor_calls"] == 11
    assert result["additional_maintenance_calls"] == 0
    assert result["tranche_dispositions"] == ["checkpoint_pause", "completed"]
    assert "current_action_contract" in result["state_slots_exposed"]


def test_authorization_contract_has_checkpoint_and_no_retry() -> None:
    contract = load_json(
        ROOT / "TRELLIS_E97_VERIFICATION_LIFECYCLE_SCOUT_CONTRACT.json"
    )
    request = load_json(
        ROOT
        / "TRELLIS_E97_VERIFICATION_LIFECYCLE_SCOUT_AUTHORIZATION_REQUEST.json"
    )
    assert contract["runtime"]["checkpoint_every_additional_actor_calls"] == 6
    assert contract["runtime"]["automatic_continuation"] is False
    assert request["first_checkpoint_after_at_most_actor_calls"] == 6
    assert request["attempts_per_call"] == 1
    assert request["retries"] == 0
