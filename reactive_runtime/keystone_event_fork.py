"""Exact common-prefix snapshot and branch cloning for Keystone.

This module contains no actor policy and performs no model call.  It exists so
the measured runner can execute the pre-treatment trajectory once, freeze one
exact state, and create two independent worlds only after the recorded causal
trigger becomes eligible.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Any

from reactive_runtime.anchored_provenance import AnchoredProvenanceRegister
from reactive_runtime.canonical import canonical_json_text, sha256_bytes
from reactive_runtime.keystone_world import KeystoneWorld
from reactive_runtime.records import ResultLedger


@dataclass(frozen=True)
class CommonForkState:
    messages: list[dict[str, str]]
    ledger: ResultLedger
    trace: list[dict[str, Any]]
    register: AnchoredProvenanceRegister
    phase: str
    pending_result_id: str | None
    next_result_ordinal: int
    latest_effect_result_id: str | None
    actor_calls_completed: int
    model_calls_completed: int
    serialized_tokens: int

    def binding(self, world: KeystoneWorld) -> dict[str, Any]:
        return {
            "schema": "keystone-common-fork-state-v0",
            "actor_calls_completed": self.actor_calls_completed,
            "model_calls_completed": self.model_calls_completed,
            "serialized_tokens": self.serialized_tokens,
            "phase": self.phase,
            "pending_result_id": self.pending_result_id,
            "next_result_ordinal": self.next_result_ordinal,
            "latest_effect_result_id": self.latest_effect_result_id,
            "candidate_sha256": world.candidate_sha256,
            "candidate_version": world.candidate_version,
            "candidate_packet_sha256": sha256_bytes(
                world.candidate_packet().encode("utf-8")
            ),
            "current_check_binding": world.current_check_binding(),
            "messages_sha256": sha256_bytes(
                canonical_json_text(self.messages).encode("utf-8")
            ),
            "ledger_sha256": sha256_bytes(
                canonical_json_text(
                    self.ledger.as_dict(include_exact_content=True)
                ).encode("utf-8")
            ),
            "trace_sha256": sha256_bytes(
                canonical_json_text(self.trace).encode("utf-8")
            ),
            "register_sha256": self.register.sha256,
        }


@dataclass
class BranchState:
    world: KeystoneWorld
    messages: list[dict[str, str]]
    ledger: ResultLedger
    trace: list[dict[str, Any]]
    register: AnchoredProvenanceRegister
    phase: str
    pending_result_id: str | None
    next_result_ordinal: int
    latest_effect_result_id: str | None
    actor_calls_completed: int
    model_calls_completed: int
    serialized_tokens: int


def clone_common_state(
    common: CommonForkState,
    source_world: KeystoneWorld,
    destination_root: Path,
) -> BranchState:
    """Clone one exact common state without sharing mutable authority objects."""

    if source_world.phase != common.phase:
        raise ValueError("common state phase disagrees with source world")
    world = KeystoneWorld(
        source_world.task_root,
        destination_root,
        count_text=source_world._count_text,
        candidate_seed_root=source_world.candidate_root,
        candidate_seed_version_index=source_world.version_index,
        evaluator_config_path=source_world.evaluator_config_path,
        evaluator_script_path=source_world.evaluator_script_path,
    )
    world.phase = source_world.phase
    world.submitted = source_world.submitted
    world.last_check_projection = deepcopy(source_world.last_check_projection)
    world.detached_integration = deepcopy(source_world.detached_integration)
    if world.candidate_sha256 != source_world.candidate_sha256:
        raise RuntimeError("forked candidate bytes disagree with common state")
    if world.candidate_version != source_world.candidate_version:
        raise RuntimeError("forked candidate version disagrees with common state")

    source_versions = source_world.cell_root / "candidate_versions"
    destination_versions = world.cell_root / "candidate_versions"
    if source_versions.is_dir():
        for source in sorted(source_versions.iterdir(), key=lambda item: item.name):
            destination = destination_versions / source.name
            if not destination.exists():
                shutil.copytree(source, destination)
    source_raw = source_world.cell_root / "raw_tool_results"
    destination_raw = world.cell_root / "raw_tool_results"
    if source_raw.is_dir():
        shutil.copytree(source_raw, destination_raw, dirs_exist_ok=True)

    return BranchState(
        world=world,
        messages=deepcopy(common.messages),
        ledger=ResultLedger.from_dict(
            deepcopy(common.ledger.as_dict(include_exact_content=True))
        ),
        trace=deepcopy(common.trace),
        register=common.register,
        phase=common.phase,
        pending_result_id=common.pending_result_id,
        next_result_ordinal=common.next_result_ordinal,
        latest_effect_result_id=common.latest_effect_result_id,
        actor_calls_completed=common.actor_calls_completed,
        model_calls_completed=common.model_calls_completed,
        serialized_tokens=common.serialized_tokens,
    )


def branch_binding(state: BranchState) -> dict[str, Any]:
    common = CommonForkState(
        messages=state.messages,
        ledger=state.ledger,
        trace=state.trace,
        register=state.register,
        phase=state.phase,
        pending_result_id=state.pending_result_id,
        next_result_ordinal=state.next_result_ordinal,
        latest_effect_result_id=state.latest_effect_result_id,
        actor_calls_completed=state.actor_calls_completed,
        model_calls_completed=state.model_calls_completed,
        serialized_tokens=state.serialized_tokens,
    )
    return common.binding(state.world)
