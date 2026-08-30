from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from host_refactor.checkpoint import RuntimeCounters
from host_refactor.model import DeliveryState, EventKind, TerminalCode
from host_refactor.whole_lifecycle.resume import hydrate_checkpoint
from host_refactor.whole_lifecycle.readiness import adjudicate_readiness
from host_refactor.whole_lifecycle.system import (
    MAXIMUM_CUMULATIVE_ACTOR_CALLS,
    MAXIMUM_CUMULATIVE_MAINTENANCE_CALLS,
    MAXIMUM_CUMULATIVE_PROVIDER_CALLS,
    MAXIMUM_CUMULATIVE_SERIALIZED_TOKENS,
    build_fresh_system,
)
from interaction_scout.fixtures import GroundedMaintenanceFixture, ScriptedActorProvider
from interaction_scout.live_path import run_interaction_tranche
from reactive_runtime.task_decision_evaluator import evaluate
from reactive_runtime.verification_causal_frame import section_spans
from tools.offline_tokenizer import OfflineTokenizer


def _check_rows(kernel: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for projected in kernel.project().results.values():
        if projected.result.result_kind != "check_observation":
            continue
        projection = projected.result.metadata.get("check_projection")
        if isinstance(projection, Mapping):
            rows.append(
                {
                    **dict(projection),
                    "delivery_state": projected.delivery_state.value,
                    "result_id": projected.result.result_id,
                }
            )
    return rows


def run_provider_free_complete_lifecycle(
    repository_root: Path,
    *,
    output_root: Path,
) -> dict[str, Any]:
    tokenizer = OfflineTokenizer()
    maintenance = GroundedMaintenanceFixture(
        repository_root / "task_trellis",
        tokenizer.count_messages,
        tokenizer.count_text,
    )
    host, adapter, kernel, orchestrator = build_fresh_system(
        repository_root=repository_root,
        trajectory_root=output_root / "trajectory-001",
        count_messages=tokenizer.count_messages,
        count_text=tokenizer.count_text,
        maintenance_complete=maintenance,
    )
    actor = ScriptedActorProvider(
        adapter,
        tokenizer.count_messages,
        tokenizer.count_text,
    )
    counters = RuntimeCounters()
    parent: Path | None = None
    dispositions: list[str] = []
    actor_calls = 0
    maintenance_calls = 0
    for tranche_index in range(1, 6):
        tranche = run_interaction_tranche(
            orchestrator=orchestrator,
            kernel=kernel,
            counters=counters,
            actor_complete=actor,
            run_root=output_root / f"tranche-{tranche_index:03d}",
            parent_checkpoint_path=parent,
        )
        dispositions.append(tranche.disposition.value)
        actor_calls += tranche.actor_attempts
        maintenance_calls += tranche.maintenance_attempts
        kernel = tranche.kernel
        counters = tranche.counters
        parent = tranche.checkpoint_path
        if tranche.disposition is TerminalCode.COMPLETED:
            break
        orchestrator, adapter, kernel, counters = hydrate_checkpoint(
            repository_root=repository_root,
            checkpoint_path=parent,
            trajectory_root=output_root / f"trajectory-{tranche_index + 1:03d}",
            count_messages=tokenizer.count_messages,
            count_text=tokenizer.count_text,
            maintenance_complete=maintenance,
        )
        actor.adapter = adapter
    state = kernel.project()
    final = evaluate(repository_root / "task_trellis", adapter.world.candidate_root)
    readiness = adjudicate_readiness(
        repository_root,
        final,
        current_candidate_sha256=adapter.world.candidate_sha256,
    )
    decision_path = (
        adapter.world.candidate_root / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
    )
    decision_text = decision_path.read_text(encoding="utf-8")
    sections = section_spans(decision_text)
    checks = _check_rows(kernel)
    exposed_slots = {
        str(row["state_slot_id"])
        for event in kernel.events
        if event.kind is EventKind.INVOCATION_COMPLETED
        for row in event.data.get("request_binding", {}).get(
            "state_slot_exposures", []
        )
    }
    external_check_ids = [
        result_id
        for result_id, projected in state.results.items()
        if projected.result.result_kind == "check_observation"
        and projected.delivery_state is DeliveryState.DELIVERED_EXTERNAL
    ]
    candidate_effect_receipts = [
        result_id
        for result_id, projected in state.results.items()
        if projected.result.result_kind == "candidate_effect"
        and projected.delivery_state is DeliveryState.DELIVERED_EXTERNAL
    ]
    return {
        "actor_calls": actor_calls,
        "candidate_effect_receipt_ids": candidate_effect_receipts,
        "check_sequence": [
            {
                "candidate_sha256": row["evaluated_candidate_sha256"],
                "delivery_state": row["delivery_state"],
                "passed": row["passed"],
                "result_id": row["result_id"],
            }
            for row in checks
        ],
        "decision_heading_count": len(sections),
        "decision_headings": [row["heading"] for row in sections],
        "dispositions": dispositions,
        "external_check_result_ids": external_check_ids,
        "final_evaluation": final,
        "final_candidate_sha256": adapter.world.candidate_sha256,
        "glued_heading_present": ".## " in decision_text,
        "maintenance_calls": maintenance_calls,
        "maintenance_register_claims": len(orchestrator.lifecycle.register.claims),
        "maximums": {
            "actor_calls": MAXIMUM_CUMULATIVE_ACTOR_CALLS,
            "maintenance_calls": MAXIMUM_CUMULATIVE_MAINTENANCE_CALLS,
            "provider_calls": MAXIMUM_CUMULATIVE_PROVIDER_CALLS,
            "serialized_tokens": MAXIMUM_CUMULATIVE_SERIALIZED_TOKENS,
        },
        "provider_calls": counters.provider_attempts,
        "relief_events": len(orchestrator.lifecycle.relief_events),
        "readiness_adjudication": readiness,
        "scaffold_active_at_end": orchestrator.lifecycle.scaffold_active,
        "scaffold_ever_exposed": orchestrator.lifecycle.scaffold_ever_exposed,
        "serialized_tokens": counters.serialized_tokens,
        "state_slots_exposed": sorted(exposed_slots),
        "submitted": adapter.world.submitted,
        "terminal": None if state.terminal is None else state.terminal.value,
    }
