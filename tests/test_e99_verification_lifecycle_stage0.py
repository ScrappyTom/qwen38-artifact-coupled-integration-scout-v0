from __future__ import annotations

from pathlib import Path

from host_refactor.lifecycle_scout_v1.system import (
    RUN_ID,
    SCOUT_CONFIGURATION_ID,
    execution_manifest,
)
from reactive_runtime.canonical import load_json


ROOT = Path(__file__).resolve().parents[1]


def test_repaired_historical_stage0_remains_frozen_and_qualified() -> None:
    frozen = load_json(ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_STAGE0.json")
    assert frozen["passed"] is True
    assert frozen["failures"] == []
    assert frozen["run_id"] == RUN_ID
    assert frozen["disposition"] == "completed"
    assert frozen["additional_actor_calls"] == 11
    assert frozen["additional_maintenance_calls"] == 0
    assert "current_action_contract" in frozen["state_slots_exposed"]
    regression = frozen["rejected_response_regression"]
    assert regression["rejected_response_receipts"] == 2
    assert regression["raw_rejected_bodies_model_resident"] is False
    assert regression["next_packet_feasible"] is True
    assert regression["next_prompt_tokens"] == 16_335


def test_repaired_route_manifest_and_authorization_are_frozen() -> None:
    stage0 = load_json(ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_STAGE0.json")
    request = load_json(
        ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_SCOUT_AUTHORIZATION_REQUEST.json"
    )
    contract = load_json(
        ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_SCOUT_CONTRACT.json"
    )
    # E104 prospectively changes the host kernel and verification lifecycle.
    # Historical E99 remains bound to its frozen manifest rather than being
    # silently rebuilt under current-head code.
    assert stage0["execution_manifest"] != execution_manifest(ROOT)
    assert (
        "host_refactor/effect_lifecycle/verification.py"
        in execution_manifest(ROOT)["files"]
    )
    assert request["run_id"] == contract["run_id"] == RUN_ID
    assert request["configuration"] == SCOUT_CONFIGURATION_ID
    assert request["first_checkpoint_after_at_most_actor_calls"] == 6
    assert request["attempts_per_call"] == 1
    assert request["retries"] == 0
    assert contract["runtime"]["automatic_continuation"] is False
