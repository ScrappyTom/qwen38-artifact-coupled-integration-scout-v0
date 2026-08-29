from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable, Mapping, Any

from host_refactor.capacity import CapacityManager, CountMessages
from host_refactor.checkpoint import CheckpointController
from host_refactor.kernel import HostKernel
from host_refactor.packet import PacketComposer
from host_refactor.runner import HostRunner
from host_refactor.trellis_adapter import (
    TrellisDomainAdapter,
    TrellisRuntimeSpec,
    initial_trellis_kernel,
    trellis_execution_manifest,
    trellis_spec,
)
from reactive_runtime.canonical import canonical_json_bytes, sha256_bytes, sha256_file
from interaction_scout.lifecycle import (
    BASELINE_CONFIGURATION,
    TREATMENT_CONFIGURATION,
    InteractionLifecycle,
    InteractionOrchestrator,
)


RUN_ID = "2026-08-29-trellis-refactored-interaction-tranche-v0"
SCOPE = "trellis_refactored_interaction_tranche_v0"
CONFIGURATION_ORDER = (BASELINE_CONFIGURATION, TREATMENT_CONFIGURATION)
MAXIMUM_ACTOR_CALLS = 24
MAXIMUM_MAINTENANCE_CALLS = 12
MAXIMUM_PROVIDER_CALLS = 36
MAXIMUM_SERIALIZED_TOKENS = 900_000


def interaction_execution_manifest(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    base = trellis_execution_manifest(root)
    declared = (
        root / "TRELLIS_REFACTORED_INTERACTION_CONTRACT.json",
        root / "TRELLIS_REFACTORED_INTERACTION_AUTHORIZATION_REQUEST.json",
        root / "MODEL_PROFILE_LOCK.json",
        root / "RUNTIME_ASSET_MANIFEST.json",
        root / "interaction_scout" / "__init__.py",
        root / "interaction_scout" / "lifecycle.py",
        root / "interaction_scout" / "live_path.py",
        root / "interaction_scout" / "system.py",
        root / "reactive_runtime" / "anchored_provenance.py",
        root / "tools" / "run_refactored_interaction_tranche.py",
        root / "tools" / "verify_runtime_assets.py",
    )
    payload = {
        "base_execution_manifest_sha256": base["execution_manifest_sha256"],
        "files": {
            path.relative_to(root).as_posix(): sha256_file(path)
            for path in sorted(declared)
        },
        "schema": "trellis-refactored-interaction-execution-manifest-v0",
    }
    return {
        **payload,
        "execution_manifest_sha256": sha256_bytes(canonical_json_bytes(payload)),
    }


def interaction_spec(
    repository_root: Path,
    *,
    configuration_id: str,
    run_id: str,
) -> TrellisRuntimeSpec:
    base = trellis_spec(repository_root)
    manifest = interaction_execution_manifest(repository_root)
    adapter_configuration = {
        BASELINE_CONFIGURATION: "A0_MATRIX_AND_DECISION",
        TREATMENT_CONFIGURATION: "A1_SCAFFOLD_MATRIX_DECISION",
    }[configuration_id]
    return replace(
        base,
        configuration=replace(
            base.configuration,
            run_id=run_id,
            execution_manifest_sha256=str(manifest["execution_manifest_sha256"]),
            tranche_calls=12,
            maximum_calls=60,
            maximum_serialized_tokens=450_000,
        ),
        configuration_id=adapter_configuration,
        execution_manifest=manifest,
    )


def build_interaction_system(
    *,
    repository_root: Path,
    trajectory_root: Path,
    configuration_id: str,
    run_id: str,
    count_messages: CountMessages,
    count_text: Callable[[str], int],
    maintenance_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None,
) -> tuple[
    HostRunner,
    TrellisDomainAdapter,
    HostKernel,
    InteractionOrchestrator,
]:
    spec = interaction_spec(
        repository_root,
        configuration_id=configuration_id,
        run_id=run_id,
    )
    adapter = TrellisDomainAdapter(
        spec=spec,
        trajectory_root=trajectory_root,
        count_text=count_text,
    )
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
    orchestrator = InteractionOrchestrator(
        host=host,
        adapter=adapter,
        lifecycle=InteractionLifecycle(configuration_id=configuration_id),
        count_messages=count_messages,
        count_text=count_text,
        maintenance_complete=maintenance_complete,
        maximum_maintenance_calls=MAXIMUM_MAINTENANCE_CALLS,
    )
    return host, adapter, initial_trellis_kernel(adapter), orchestrator
