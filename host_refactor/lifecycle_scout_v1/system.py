from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Mapping, cast

from host_refactor.capacity import CapacityManager, CountMessages
from host_refactor.checkpoint import CheckpointController
from host_refactor.effect_lifecycle import EffectLifecycleInteractionOrchestrator
from host_refactor.lifecycle_scout.adapter import LifecycleScoutAdapter
from host_refactor.packet import PacketComposer
from host_refactor.runner import HostRunner
from host_refactor.trellis_adapter import (
    TrellisRuntimeSpec,
    trellis_execution_manifest,
    trellis_spec,
)
from interaction_scout.lifecycle import InteractionLifecycle, TREATMENT_CONFIGURATION
from reactive_runtime.canonical import canonical_json_bytes, sha256_bytes, sha256_file


RUN_ID = "2026-08-29-trellis-e99-verification-lifecycle-scout-v1"
SCOPE = "trellis_e99_verification_lifecycle_scout_v1"
SCOUT_CONFIGURATION_ID = "V1_E97_REPAIRED_DONOR_DERIVED_LIFECYCLE"
MAXIMUM_ADDITIONAL_ACTOR_CALLS = 18
MAXIMUM_ADDITIONAL_MAINTENANCE_CALLS = 1
MAXIMUM_ADDITIONAL_PROVIDER_CALLS = 19
MAXIMUM_ADDITIONAL_SERIALIZED_TOKENS = 450_000
DONOR_SERIALIZED_TOKENS = 350_510
DONOR_PROVIDER_ATTEMPTS = 29
MAXIMUM_CUMULATIVE_SERIALIZED_TOKENS = (
    DONOR_SERIALIZED_TOKENS + MAXIMUM_ADDITIONAL_SERIALIZED_TOKENS
)
CHECKPOINT_EVERY_ADDITIONAL_ACTOR_CALLS = 6
MAXIMUM_CUMULATIVE_ACTOR_CALLS = 36
MAXIMUM_CUMULATIVE_MAINTENANCE_CALLS = 12
CONFIGURATION_ID = TREATMENT_CONFIGURATION


def execution_manifest(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    base = trellis_execution_manifest(root)
    declared = (
        root / "TRELLIS_E99_VERIFICATION_LIFECYCLE_SCOUT_CONTRACT.json",
        root / "TRELLIS_E99_VERIFICATION_LIFECYCLE_SCOUT_AUTHORIZATION_REQUEST.json",
        root / "MODEL_PROFILE_LOCK.json",
        root / "RUNTIME_ASSET_MANIFEST.json",
        root / "host_refactor" / "effect_lifecycle" / "orchestrator.py",
        root / "host_refactor" / "effect_lifecycle" / "policy.py",
        root / "host_refactor" / "effect_lifecycle" / "verification.py",
        root / "host_refactor" / "lifecycle_scout" / "adapter.py",
        root / "host_refactor" / "lifecycle_scout" / "fixtures.py",
        root / "host_refactor" / "lifecycle_scout" / "migration.py",
        root / "host_refactor" / "lifecycle_scout_v1" / "__init__.py",
        root / "host_refactor" / "lifecycle_scout_v1" / "migration.py",
        root / "host_refactor" / "lifecycle_scout_v1" / "system.py",
        root / "interaction_scout" / "lifecycle.py",
        root / "interaction_scout" / "fixtures.py",
        root / "interaction_scout" / "live_path.py",
        root / "reactive_runtime" / "anchored_provenance.py",
        root / "reactive_runtime" / "task_decision_evaluator.py",
        root / "tools" / "run_e99_verification_lifecycle_scout.py",
        root / "tools" / "build_e99_verification_lifecycle_stage0.py",
    )
    payload = {
        "base_execution_manifest_sha256": base["execution_manifest_sha256"],
        "files": {
            path.relative_to(root).as_posix(): sha256_file(path)
            for path in sorted(declared)
        },
        "schema": "trellis-e99-verification-lifecycle-execution-manifest-v1",
    }
    return {
        **payload,
        "execution_manifest_sha256": sha256_bytes(canonical_json_bytes(payload)),
    }


def lifecycle_scout_spec(repository_root: Path) -> TrellisRuntimeSpec:
    base = trellis_spec(repository_root)
    manifest = execution_manifest(repository_root)
    return replace(
        base,
        configuration=replace(
            base.configuration,
            run_id=RUN_ID,
            execution_manifest_sha256=str(manifest["execution_manifest_sha256"]),
            tranche_calls=CHECKPOINT_EVERY_ADDITIONAL_ACTOR_CALLS,
            maximum_calls=MAXIMUM_CUMULATIVE_ACTOR_CALLS,
            maximum_serialized_tokens=MAXIMUM_CUMULATIVE_SERIALIZED_TOKENS,
        ),
        configuration_id="A1_SCAFFOLD_MATRIX_DECISION",
        execution_manifest=manifest,
        paths=replace(
            base.paths,
            contract_path=(
                repository_root
                / "TRELLIS_E99_VERIFICATION_LIFECYCLE_SCOUT_CONTRACT.json"
            ),
            model_lock_path=repository_root / "MODEL_PROFILE_LOCK.json",
        ),
    )


def build_system(
    *,
    repository_root: Path,
    trajectory_root: Path,
    domain_snapshot: Mapping[str, Any],
    lifecycle_snapshot: Mapping[str, Any],
    count_messages: CountMessages,
    count_text: Callable[[str], int],
    maintenance_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> tuple[
    HostRunner,
    LifecycleScoutAdapter,
    EffectLifecycleInteractionOrchestrator,
]:
    spec = lifecycle_scout_spec(repository_root)
    adapter = cast(
        LifecycleScoutAdapter,
        LifecycleScoutAdapter.from_snapshot(
            spec=spec,
            trajectory_root=trajectory_root,
            snapshot=domain_snapshot,
            count_text=count_text,
        ),
    )
    lifecycle = InteractionLifecycle.from_dict(lifecycle_snapshot)
    if lifecycle.configuration_id != CONFIGURATION_ID:
        raise ValueError("donor lifecycle is not the frozen treatment configuration")
    composer = PacketComposer()
    host = HostRunner(
        configuration=spec.configuration,
        composer=composer,
        capacity=CapacityManager(
            composer=composer,
            count_messages=count_messages,
            prompt_limit=spec.configuration.prompt_limit,
        ),
        checkpoint=CheckpointController(spec.configuration),
        payload_builder=adapter.payload,
    )
    orchestrator = EffectLifecycleInteractionOrchestrator(
        host=host,
        adapter=adapter,
        lifecycle=lifecycle,
        count_messages=count_messages,
        count_text=count_text,
        maintenance_complete=maintenance_complete,
        maximum_maintenance_calls=MAXIMUM_CUMULATIVE_MAINTENANCE_CALLS,
    )
    return host, adapter, orchestrator
