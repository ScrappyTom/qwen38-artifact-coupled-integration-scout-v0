from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from host_refactor.checkpoint import CheckpointController, RuntimeCounters
from host_refactor.trellis_adapter import TrellisDomainAdapter
from interaction_scout.fixtures import GroundedMaintenanceFixture, ScriptedActorProvider
from interaction_scout.lifecycle import (
    TREATMENT_CONFIGURATION,
    InteractionLifecycle,
    InteractionOrchestrator,
)
from interaction_scout.live_path import run_interaction_tranche
from interaction_scout.system import build_interaction_system
from tools.offline_tokenizer import OfflineTokenizer


def run_provider_free_lifecycle(
    repository_root: Path,
    *,
    configuration_id: str,
    output_root: Path,
) -> dict[str, Any]:
    tokenizer = OfflineTokenizer()
    maintenance = GroundedMaintenanceFixture(
        repository_root / "task_trellis",
        tokenizer.count_messages,
        tokenizer.count_text,
    )
    host, adapter, kernel, orchestrator = build_interaction_system(
        repository_root=repository_root,
        trajectory_root=output_root / "trajectory",
        configuration_id=configuration_id,
        run_id=f"provider-free-{configuration_id.lower()}",
        count_messages=tokenizer.count_messages,
        count_text=tokenizer.count_text,
        maintenance_complete=(
            maintenance if configuration_id == TREATMENT_CONFIGURATION else None
        ),
    )
    actor = ScriptedActorProvider(
        adapter,
        tokenizer.count_messages,
        tokenizer.count_text,
    )
    first = run_interaction_tranche(
        orchestrator=orchestrator,
        kernel=kernel,
        counters=RuntimeCounters(),
        actor_complete=actor,
        run_root=output_root / "tranche-001",
    )
    if first.disposition.value != "checkpoint_pause":
        raise RuntimeError("provider-free first tranche did not pause at checkpoint")
    checkpoint_value = json.loads(first.checkpoint_path.read_text(encoding="utf-8"))
    hydrated, restored_counters, domain = CheckpointController.hydrate_with_domain(
        checkpoint_value,
        host.configuration,
    )
    if domain is None:
        raise RuntimeError("provider-free checkpoint lacks domain state")
    restored_adapter = TrellisDomainAdapter.from_snapshot(
        spec=adapter.spec,
        trajectory_root=output_root / "resumed",
        snapshot=domain["trellis"],
        count_text=tokenizer.count_text,
    )
    restored_lifecycle = InteractionLifecycle.from_dict(domain["interaction"])
    resumed_maintenance = GroundedMaintenanceFixture(
        repository_root / "task_trellis",
        tokenizer.count_messages,
        tokenizer.count_text,
    )
    orchestrator = InteractionOrchestrator(
        host=host,
        adapter=restored_adapter,
        lifecycle=restored_lifecycle,
        count_messages=tokenizer.count_messages,
        count_text=tokenizer.count_text,
        maintenance_complete=(
            resumed_maintenance
            if configuration_id == TREATMENT_CONFIGURATION
            else None
        ),
    )
    actor.adapter = restored_adapter
    second = run_interaction_tranche(
        orchestrator=orchestrator,
        kernel=hydrated,
        counters=restored_counters,
        actor_complete=actor,
        run_root=output_root / "tranche-002",
        parent_checkpoint_path=first.checkpoint_path,
    )
    state = second.kernel.project()
    bindings = [
        dict(event.data["request_binding"])
        for event in second.kernel.events
        if event.kind.value == "invocation_completed"
    ]
    return {
        "adapter": restored_adapter,
        "checkpoint": first.checkpoint_path,
        "counters": second.counters,
        "dispositions": (first.disposition, second.disposition),
        "kernel": second.kernel,
        "lifecycle": orchestrator.lifecycle,
        "request_bindings": bindings,
        "summary": {
            "actor_calls": len(state.completed_calls),
            "candidate_state_versions": sum(
                event.kind.value == "state_slot_set"
                and event.data["state_object"]["slot_id"] == "current_candidate"
                for event in second.kernel.events
            ),
            "final_check_passed": bool(
                restored_adapter.world.last_check_projection
                and restored_adapter.world.last_check_projection.get("passed")
            ),
            "maintenance_calls": orchestrator.lifecycle.maintenance_calls,
            "relief_events": len(orchestrator.lifecycle.relief_events),
            "submitted": restored_adapter.world.submitted,
            "terminal": None if state.terminal is None else state.terminal.value,
            "total_provider_attempts": second.counters.provider_attempts,
            "total_serialized_tokens": second.counters.serialized_tokens,
        },
    }
