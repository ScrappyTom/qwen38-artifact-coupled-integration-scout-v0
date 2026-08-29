from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

import json

from host_refactor.checkpoint import RuntimeCounters
from interaction_scout.lifecycle import (
    BASELINE_CONFIGURATION,
    SCAFFOLD_SLOT,
    TREATMENT_CONFIGURATION,
    VERIFICATION_SLOT,
    InteractionLifecycle,
)
from interaction_scout.provider_free import run_provider_free_lifecycle
from interaction_scout.system import (
    MAXIMUM_ACTOR_CALLS,
    MAXIMUM_MAINTENANCE_CALLS,
    MAXIMUM_PROVIDER_CALLS,
    MAXIMUM_SERIALIZED_TOKENS,
    RUN_ID,
    build_interaction_system,
    interaction_execution_manifest,
    interaction_spec,
)


ROOT = Path(__file__).resolve().parents[1]


def run_fixture(configuration_id: str, temp_root: Path):
    return run_provider_free_lifecycle(
        ROOT,
        configuration_id=configuration_id,
        output_root=temp_root,
    )


@pytest.fixture(scope="module")
def lifecycle_results():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        yield {
            configuration_id: run_fixture(
                configuration_id,
                root / configuration_id,
            )
            for configuration_id in (
                BASELINE_CONFIGURATION,
                TREATMENT_CONFIGURATION,
            )
        }


@pytest.mark.parametrize(
    "configuration_id",
    [BASELINE_CONFIGURATION, TREATMENT_CONFIGURATION],
)
def test_complete_pressure_to_repair_lifecycle(
    configuration_id: str, lifecycle_results
) -> None:
    result = lifecycle_results[configuration_id]
    state = result["kernel"].project()
    adapter = result["adapter"]
    assert state.terminal is not None and state.terminal.value == "completed"
    assert adapter.world.submitted is True
    assert adapter.world.last_check_projection is not None
    assert adapter.world.last_check_projection["passed"] is True
    assert result["checkpoint"] is not None
    assert any(row.value == "checkpoint_pause" for row in result["dispositions"])
    assert result["lifecycle"].relief_events
    assert all(binding["state_slot_exposures"] for binding in result["request_bindings"])
    assert any(
        row["state_slot_id"] == "current_candidate"
        for binding in result["request_bindings"]
        for row in binding["state_slot_exposures"]
    )
    assert VERIFICATION_SLOT in state.state_slots
    assert state.state_slots[VERIFICATION_SLOT].metadata["check_currency"] == "current"


def test_treatment_scaffold_is_charged_then_demoted_for_verification(
    lifecycle_results,
) -> None:
    result = lifecycle_results[TREATMENT_CONFIGURATION]
    lifecycle = result["lifecycle"]
    state = result["kernel"].project()
    assert lifecycle.maintenance_calls >= 1
    assert lifecycle.maintenance_serialized_tokens > 0
    assert lifecycle.register.claims
    assert lifecycle.scaffold_ever_exposed is True
    assert lifecycle.scaffold_active is False
    assert lifecycle.phase == "verification"
    assert state.state_slots[SCAFFOLD_SLOT].metadata["active"] is False
    assert "construction_scaffold_demoted_at_verification" in state.state_slots[
        SCAFFOLD_SLOT
    ].exact_content


def test_baseline_never_receives_semantic_scaffold_or_maintenance_cost(
    lifecycle_results,
) -> None:
    result = lifecycle_results[BASELINE_CONFIGURATION]
    lifecycle = result["lifecycle"]
    assert lifecycle.maintenance_calls == 0
    assert lifecycle.maintenance_serialized_tokens == 0
    assert lifecycle.register.claims == ()
    assert SCAFFOLD_SLOT not in result["kernel"].project().state_slots


def test_live_contract_manifest_and_budgets_are_frozen_consistently() -> None:
    request = json.loads(
        (ROOT / "TRELLIS_REFACTORED_INTERACTION_AUTHORIZATION_REQUEST.json").read_text(
            encoding="utf-8"
        )
    )
    contract = json.loads(
        (ROOT / "TRELLIS_REFACTORED_INTERACTION_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = interaction_execution_manifest(ROOT)
    assert request["run_id"] == contract["run_id"] == RUN_ID
    assert request["maximum_actor_calls"] == MAXIMUM_ACTOR_CALLS == 24
    assert request["maximum_maintenance_calls"] == MAXIMUM_MAINTENANCE_CALLS == 12
    assert request["maximum_provider_calls"] == MAXIMUM_PROVIDER_CALLS == 36
    assert request["maximum_serialized_tokens"] == MAXIMUM_SERIALIZED_TOKENS
    assert manifest["execution_manifest_sha256"]
    assert "interaction_scout/lifecycle.py" in manifest["files"]
    for configuration_id in (BASELINE_CONFIGURATION, TREATMENT_CONFIGURATION):
        spec = interaction_spec(
            ROOT,
            configuration_id=configuration_id,
            run_id=f"{RUN_ID}:{configuration_id}",
        )
        assert spec.configuration.maximum_serialized_tokens == 450_000
        assert spec.configuration.tranche_calls == 12


def test_lifecycle_snapshot_rejects_register_hash_tampering(lifecycle_results) -> None:
    value = lifecycle_results[TREATMENT_CONFIGURATION]["lifecycle"].as_dict()
    value["register"] = dict(value["register"])
    value["register"]["register_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="register hash mismatch"):
        InteractionLifecycle.from_dict(value)


def test_truncated_maintenance_is_charged_but_never_admitted(tmp_path: Path) -> None:
    def truncated(_payload):
        return {
            "content": "# Anchored provenance-local delta\npartial",
            "finish_reason": "length",
            "usage": {
                "completion_tokens": 5,
                "prompt_tokens": 100,
                "total_tokens": 105,
            },
        }

    _, adapter, kernel, orchestrator = build_interaction_system(
        repository_root=ROOT,
        trajectory_root=tmp_path / "trajectory",
        configuration_id=TREATMENT_CONFIGURATION,
        run_id="provider-free-truncated-maintenance",
        count_messages=lambda _messages: 100,
        count_text=lambda text: len(text.split()),
        maintenance_complete=truncated,
    )
    outcome = adapter.handle(
        json.dumps(
            {
                "action": "read_source",
                "end_line": 20,
                "source_id": "COUNCIL",
                "start_line": 1,
            }
        ),
        call_index=1,
        kernel=kernel,
    )
    assert outcome.result is not None
    kernel = kernel.acquire(outcome.result).schedule(
        outcome.result.result_id,
        call_index=1,
        transcript_entry_id="TEST-RESULT",
    )
    kernel = kernel.complete_invocation(
        call_index=1,
        included_result_ids=(outcome.result.result_id,),
        request_sha256="request",
        response_sha256="response",
    ).externalize(outcome.result.result_id, reason="test")
    kernel, counters = orchestrator._maintenance(
        kernel,
        RuntimeCounters(),
        (outcome.result.result_id,),
        None,
    )
    assert counters.provider_attempts == 1
    assert counters.serialized_tokens == 105
    assert orchestrator.lifecycle.maintenance_calls == 1
    assert orchestrator.lifecycle.register.claims == ()
    assert orchestrator.lifecycle.maintenance_events[-1]["disposition"] == (
        "finish_reason_reject"
    )
