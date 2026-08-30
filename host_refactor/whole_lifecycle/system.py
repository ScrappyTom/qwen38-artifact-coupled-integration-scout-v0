from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Mapping, cast

from host_refactor.capacity import CapacityManager, CountMessages
from host_refactor.checkpoint import CheckpointController
from host_refactor.effect_lifecycle import EffectLifecycleInteractionOrchestrator
from host_refactor.kernel import HostKernel
from host_refactor.lifecycle_scout.adapter import LifecycleScoutAdapter
from host_refactor.packet import PacketComposer
from host_refactor.runner import HostRunner
from host_refactor.trellis_adapter import (
    TrellisRuntimeSpec,
    initial_trellis_kernel,
    trellis_execution_manifest,
    trellis_spec,
)
from interaction_scout.lifecycle import InteractionLifecycle, TREATMENT_CONFIGURATION
from reactive_runtime.canonical import canonical_json_bytes, sha256_bytes, sha256_file


RUN_ID = "2026-08-30-trellis-clean-whole-lifecycle-v0"
SCOPE = "trellis_clean_whole_lifecycle_v0"
CONFIGURATION_LABEL = "V1_CLEAN_PROSPECTIVE_LIFECYCLE"
TRANCHE_ACTOR_CALLS = 12
MAXIMUM_CUMULATIVE_ACTOR_CALLS = 48
MAXIMUM_CUMULATIVE_MAINTENANCE_CALLS = 18
MAXIMUM_CUMULATIVE_PROVIDER_CALLS = 66
MAXIMUM_CUMULATIVE_SERIALIZED_TOKENS = 1_500_000
INITIAL_MAXIMUM_ACTOR_CALLS = 12
INITIAL_MAXIMUM_MAINTENANCE_CALLS = 6
INITIAL_MAXIMUM_PROVIDER_CALLS = 18
INITIAL_MAXIMUM_SERIALIZED_TOKENS = 400_000


def execution_manifest(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    base = trellis_execution_manifest(root)
    declared = (
        root / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CONTRACT.json",
        root / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_AUTHORIZATION_REQUEST.json",
        root / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_READINESS_RULE.json",
        root / "MODEL_PROFILE_LOCK.json",
        root / "RUNTIME_ASSET_MANIFEST.json",
        root / "host_refactor" / "effect_lifecycle" / "orchestrator.py",
        root / "host_refactor" / "effect_lifecycle" / "policy.py",
        root / "host_refactor" / "effect_lifecycle" / "verification.py",
        root / "host_refactor" / "lifecycle_scout" / "adapter.py",
        root / "host_refactor" / "whole_lifecycle" / "__init__.py",
        root / "host_refactor" / "whole_lifecycle" / "provider_free.py",
        root / "host_refactor" / "whole_lifecycle" / "readiness.py",
        root / "host_refactor" / "whole_lifecycle" / "resume.py",
        root / "host_refactor" / "whole_lifecycle" / "system.py",
        root / "interaction_scout" / "fixtures.py",
        root / "interaction_scout" / "lifecycle.py",
        root / "interaction_scout" / "live_path.py",
        root / "reactive_runtime" / "anchored_provenance.py",
        root / "reactive_runtime" / "verification_causal_frame.py",
        root / "tools" / "build_e105_clean_whole_lifecycle_stage0.py",
        root / "tools" / "run_e105_clean_whole_lifecycle_tranche.py",
        root / "tools" / "verify_runtime_assets.py",
    )
    payload = {
        "base_execution_manifest_sha256": base["execution_manifest_sha256"],
        "files": {
            path.relative_to(root).as_posix(): sha256_file(path)
            for path in sorted(declared)
        },
        "schema": "trellis-clean-whole-lifecycle-execution-manifest-v0",
    }
    return {
        **payload,
        "execution_manifest_sha256": sha256_bytes(canonical_json_bytes(payload)),
    }


def lifecycle_spec(repository_root: Path) -> TrellisRuntimeSpec:
    base = trellis_spec(repository_root)
    manifest = execution_manifest(repository_root)
    return replace(
        base,
        configuration=replace(
            base.configuration,
            run_id=RUN_ID,
            execution_manifest_sha256=str(manifest["execution_manifest_sha256"]),
            tranche_calls=TRANCHE_ACTOR_CALLS,
            maximum_calls=MAXIMUM_CUMULATIVE_ACTOR_CALLS,
            maximum_serialized_tokens=MAXIMUM_CUMULATIVE_SERIALIZED_TOKENS,
        ),
        configuration_id="A1_SCAFFOLD_MATRIX_DECISION",
        execution_manifest=manifest,
        paths=replace(
            base.paths,
            contract_path=(
                repository_root / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CONTRACT.json"
            ),
            model_lock_path=repository_root / "MODEL_PROFILE_LOCK.json",
        ),
    )


def _assemble(
    *,
    repository_root: Path,
    trajectory_root: Path,
    count_messages: CountMessages,
    count_text: Callable[[str], int],
    maintenance_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    domain_snapshot: Mapping[str, Any] | None = None,
    lifecycle_snapshot: Mapping[str, Any] | None = None,
) -> tuple[
    HostRunner,
    LifecycleScoutAdapter,
    HostKernel,
    EffectLifecycleInteractionOrchestrator,
]:
    spec = lifecycle_spec(repository_root)
    if domain_snapshot is None:
        adapter = LifecycleScoutAdapter(
            spec=spec,
            trajectory_root=trajectory_root,
            count_text=count_text,
        )
    else:
        adapter = cast(
            LifecycleScoutAdapter,
            LifecycleScoutAdapter.from_snapshot(
                spec=spec,
                trajectory_root=trajectory_root,
                snapshot=domain_snapshot,
                count_text=count_text,
            ),
        )
    lifecycle = (
        InteractionLifecycle(configuration_id=TREATMENT_CONFIGURATION)
        if lifecycle_snapshot is None
        else InteractionLifecycle.from_dict(lifecycle_snapshot)
    )
    if lifecycle.configuration_id != TREATMENT_CONFIGURATION:
        raise ValueError("clean lifecycle requires the frozen treatment lifecycle")
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
    kernel = initial_trellis_kernel(adapter)
    return host, adapter, kernel, orchestrator


def build_fresh_system(
    *,
    repository_root: Path,
    trajectory_root: Path,
    count_messages: CountMessages,
    count_text: Callable[[str], int],
    maintenance_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> tuple[
    HostRunner,
    LifecycleScoutAdapter,
    HostKernel,
    EffectLifecycleInteractionOrchestrator,
]:
    return _assemble(
        repository_root=repository_root,
        trajectory_root=trajectory_root,
        count_messages=count_messages,
        count_text=count_text,
        maintenance_complete=maintenance_complete,
    )


def build_resumed_system(
    *,
    repository_root: Path,
    trajectory_root: Path,
    count_messages: CountMessages,
    count_text: Callable[[str], int],
    maintenance_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    domain_snapshot: Mapping[str, Any],
    lifecycle_snapshot: Mapping[str, Any],
) -> tuple[
    HostRunner,
    LifecycleScoutAdapter,
    HostKernel,
    EffectLifecycleInteractionOrchestrator,
]:
    return _assemble(
        repository_root=repository_root,
        trajectory_root=trajectory_root,
        count_messages=count_messages,
        count_text=count_text,
        maintenance_complete=maintenance_complete,
        domain_snapshot=domain_snapshot,
        lifecycle_snapshot=lifecycle_snapshot,
    )
