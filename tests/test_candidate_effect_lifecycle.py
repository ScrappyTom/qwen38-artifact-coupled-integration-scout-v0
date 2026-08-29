from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from host_refactor.capacity import CapacityManager
from host_refactor.checkpoint import CheckpointController, RuntimeCounters
from host_refactor.effect_lifecycle import (
    CURRENT_EFFECT_SLOT,
    CandidateEffectLifecycle,
    EffectLifecycleInteractionOrchestrator,
)
from host_refactor.kernel import HostKernel, InvalidTransition
from host_refactor.model import (
    DeliveryState,
    ExactStateObject,
    HostEvent,
    RunConfiguration,
)
from host_refactor.packet import PacketComposer
from host_refactor.runner import HostRunner
from host_refactor.trellis_adapter import TrellisDomainAdapter, initial_trellis_kernel
from interaction_scout.fixtures import ScriptedActorProvider
from interaction_scout.lifecycle import (
    BASELINE_CONFIGURATION,
    InteractionLifecycle,
    TREATMENT_CONFIGURATION,
)
from interaction_scout.system import interaction_spec
from reactive_runtime.canonical import load_json
from tools.offline_tokenizer import OfflineTokenizer
from tools.audit_candidate_effect_lifecycle import audit


ROOT = Path(__file__).resolve().parents[1]
E96_CHECKPOINT = (
    ROOT
    / "qualification_runs"
    / "2026-08-29-trellis-refactored-interaction-continuation-v0"
    / "cells"
    / TREATMENT_CONFIGURATION
    / "tranche-002"
    / "CHECKPOINT.json"
)
EFFECT_IDS = tuple(f"RESULT-{index:03d}" for index in range(13, 19))


def _e96_preterminal() -> tuple[dict[str, object], HostKernel]:
    checkpoint = load_json(E96_CHECKPOINT)
    rows = checkpoint["event_log"]["events"]
    assert rows[-1]["kind"] == "terminal_recorded"
    assert rows[-1]["data"]["code"] == "capacity_blocked"
    events = tuple(HostEvent.from_dict(row) for row in rows[:-1])
    return checkpoint, HostKernel(events)


def _configuration(checkpoint: dict[str, object]) -> RunConfiguration:
    raw = checkpoint["configuration"]
    assert isinstance(raw, dict)
    return RunConfiguration(
        run_id=str(raw["run_id"]),
        task_id=str(raw["task_id"]),
        seed=int(raw["seed"]),
        context_window=int(raw["context_window"]),
        response_reserve=int(raw["response_reserve"]),
        execution_manifest_sha256=str(raw["execution_manifest_sha256"]),
        accepted_finish_reasons=tuple(raw["accepted_finish_reasons"]),
        tranche_calls=int(raw["tranche_calls"]),
        maximum_calls=int(raw["maximum_calls"]),
        maximum_serialized_tokens=raw["maximum_serialized_tokens"],
    )


def test_published_offline_audit_reproduces() -> None:
    assert load_json(ROOT / "TRELLIS_CANDIDATE_EFFECT_LIFECYCLE_AUDIT.json") == audit()


def test_e96_replay_retires_only_delivered_effects_and_restores_capacity() -> None:
    _, kernel = _e96_preterminal()
    before = {
        result_id: kernel.project().results[result_id].result.exact_content_sha256
        for result_id in EFFECT_IDS
    }

    outcome = CandidateEffectLifecycle().reconcile(kernel)
    state = outcome.kernel.project()

    assert outcome.externalized_result_ids == EFFECT_IDS[:-1]
    assert state.results[EFFECT_IDS[-1]].delivery_state is DeliveryState.PENDING
    assert all(
        state.results[result_id].delivery_state is DeliveryState.DELIVERED_EXTERNAL
        for result_id in EFFECT_IDS[:-1]
    )
    assert {
        result_id: state.results[result_id].result.exact_content_sha256
        for result_id in EFFECT_IDS
    } == before
    current_effect = json.loads(state.state_slots[CURRENT_EFFECT_SLOT].exact_content)
    assert current_effect["result_id"] == "RESULT-018"
    assert current_effect["delivery_state"] == "pending"
    assert current_effect["current_candidate_contains_effect"] is True
    assert current_effect["semantic_uptake"] == "not_inferred_from_delivery"

    tokenizer = OfflineTokenizer()
    packet = PacketComposer().compose(outcome.kernel)
    assert tokenizer.count_messages(packet.message_list()) == 19_116
    assert tokenizer.count_messages(packet.message_list()) <= 20_992
    representations = {
        row.result_id: row.representation
        for row in packet.manifest
        if row.result_id in EFFECT_IDS
    }
    assert set(representations.values()) == {
        "applied_candidate_effect_receipt",
        "pending_exact_body",
    }
    action_representations = {
        row.transcript_entry_id: row.representation
        for row in packet.manifest
        if row.transcript_entry_id.startswith("CALL-00001")
        and row.role == "assistant"
    }
    assert all(
        action_representations[f"CALL-{index:06d}-ASSISTANT"]
        == "applied_candidate_action_receipt"
        for index in range(13, 18)
    )
    assert action_representations["CALL-000018-ASSISTANT"] == "ordinary"

    tampered = deepcopy(outcome.kernel.as_dict())
    tampered["events_sha256"] = None
    event = next(
        row
        for row in tampered["events"]
        if row["kind"] == "candidate_effect_externalized"
    )
    event["data"]["action_sha256"] = "0" * 64
    with pytest.raises(InvalidTransition, match="causal action hash mismatch"):
        HostKernel.from_dict(tampered)


def test_pending_failure_wrong_hash_and_broken_lineage_fail_closed() -> None:
    _, kernel = _e96_preterminal()
    current_sha = str(
        kernel.project().state_slots["current_candidate"].metadata[
            "candidate_sha256"
        ]
    )
    with pytest.raises(InvalidTransition, match="pending"):
        kernel.externalize_applied_candidate_effect(
            "RESULT-018", current_candidate_sha256=current_sha
        )
    with pytest.raises(InvalidTransition, match="hash mismatch"):
        kernel.externalize_applied_candidate_effect(
            "RESULT-013", current_candidate_sha256="0" * 64
        )

    failed = kernel.fail_provider(
        call_index=19,
        request_sha256="request-19",
        error_type="TimeoutError",
        error_message="offline fixture",
    )
    failed_outcome = CandidateEffectLifecycle().reconcile(failed)
    assert (
        failed_outcome.kernel.project().results["RESULT-018"].delivery_state
        is DeliveryState.PENDING
    )

    candidate = kernel.project().state_slots["current_candidate"]
    broken = kernel.set_state_object(
        ExactStateObject(
            slot_id=candidate.slot_id,
            object_id=candidate.object_id,
            object_version="tampered",
            exact_content=candidate.exact_content,
            metadata={**candidate.metadata, "candidate_sha256": "f" * 64},
        )
    )
    with pytest.raises(InvalidTransition, match="does not produce current candidate"):
        CandidateEffectLifecycle().reconcile(broken)


def test_effect_reopen_checkpoint_round_trip_is_exact() -> None:
    checkpoint, kernel = _e96_preterminal()
    bounded = CandidateEffectLifecycle().reconcile(kernel).kernel
    delivered = bounded.complete_invocation(
        call_index=19,
        included_result_ids=("RESULT-018",),
        request_sha256="request-19",
        response_sha256="response-19",
    )
    delivered = CandidateEffectLifecycle().reconcile(delivered).kernel
    reopened = delivered.request_reopen(
        "RESULT-013",
        call_index=20,
        transcript_entry_id="TEST-REOPEN-RESULT-013",
    )
    packet = PacketComposer().compose(reopened)
    entries = [row for row in packet.manifest if row.result_id == "RESULT-013"]
    assert any(row.representation == "pending_exact_body" for row in entries)

    configuration = _configuration(checkpoint)
    counters_raw = checkpoint["counters"]
    assert isinstance(counters_raw, dict)
    counters = RuntimeCounters(
        serialized_tokens=int(counters_raw["serialized_tokens"]),
        provider_attempts=int(counters_raw["provider_attempts"]),
    )
    controller = CheckpointController(configuration)
    snapshot = controller.snapshot(reopened, counters)
    hydrated, hydrated_counters = controller.hydrate(snapshot, configuration)
    assert hydrated.as_dict() == reopened.as_dict()
    assert hydrated_counters == counters
    assert PacketComposer().compose(hydrated).canonical_bytes == packet.canonical_bytes


def test_provider_free_construction_to_verification_lifecycle_completes(
    tmp_path: Path,
) -> None:
    tokenizer = OfflineTokenizer()
    base_spec = interaction_spec(
        ROOT,
        configuration_id=BASELINE_CONFIGURATION,
        run_id="offline-candidate-effect-lifecycle",
    )
    configuration = replace(
        base_spec.configuration,
        run_id="offline-candidate-effect-lifecycle",
        tranche_calls=60,
        maximum_serialized_tokens=650_000,
    )
    spec = replace(base_spec, configuration=configuration)
    adapter = TrellisDomainAdapter(
        spec=spec,
        trajectory_root=tmp_path / "trajectory",
        count_text=tokenizer.count_text,
    )
    composer = PacketComposer()
    host = HostRunner(
        configuration=configuration,
        composer=composer,
        capacity=CapacityManager(
            composer=composer,
            count_messages=tokenizer.count_messages,
            prompt_limit=configuration.prompt_limit,
        ),
        checkpoint=CheckpointController(configuration),
        payload_builder=adapter.payload,
    )
    lifecycle = InteractionLifecycle(configuration_id=BASELINE_CONFIGURATION)
    orchestrator = EffectLifecycleInteractionOrchestrator(
        host=host,
        adapter=adapter,
        lifecycle=lifecycle,
        count_messages=tokenizer.count_messages,
        count_text=tokenizer.count_text,
        maintenance_complete=None,
        maximum_maintenance_calls=18,
    )
    actor = ScriptedActorProvider(
        adapter,
        tokenizer.count_messages,
        tokenizer.count_text,
    )
    actor.calls = 12
    kernel = initial_trellis_kernel(adapter)
    counters = RuntimeCounters()

    dispositions = []
    prompt_tokens = []
    for _ in range(7):
        step = orchestrator.step(
            kernel=kernel,
            counters=counters,
            actor_complete=actor,
        )
        kernel = step.runner_step.kernel
        counters = step.runner_step.counters
        dispositions.append(step.runner_step.disposition)
        prompt_tokens.append(step.runner_step.capacity.prompt_tokens)
        if kernel.project().terminal is not None:
            break

    assert adapter.world.submitted is True, {
        "actions": [
            event.data
            for event in kernel.events
            if event.kind.value == "action_disposition"
        ][-6:],
        "dispositions": [
            None if value is None else value.value for value in dispositions
        ],
        "terminal": (
            None
            if kernel.project().terminal is None
            else kernel.project().terminal.value
        ),
    }
    assert adapter.world.last_check_projection is not None
    assert adapter.world.last_check_projection["passed"] is True
    assert kernel.project().terminal is not None
    assert kernel.project().terminal.value == "completed"
    assert len(kernel.project().completed_calls) == 7
    assert max(prompt_tokens) <= configuration.prompt_limit
    assert dispositions[-1] is not None
    candidate_effects = [
        row
        for row in kernel.project().results.values()
        if row.result.result_kind == "candidate_effect"
    ]
    assert all(
        row.delivery_state is DeliveryState.DELIVERED_EXTERNAL
        for row in candidate_effects
    )
    current_effect = json.loads(
        kernel.project().state_slots[CURRENT_EFFECT_SLOT].exact_content
    )
    assert current_effect["semantic_uptake"] == "not_inferred_from_delivery"
