from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable

from reactive_runtime.canonical import canonical_json_bytes, sha256_bytes, sha256_file

from host_refactor.capacity import CapacityManager, CountMessages
from host_refactor.checkpoint import CheckpointController, RuntimeCounters
from host_refactor.kernel import HostKernel
from host_refactor.model import TerminalCode
from host_refactor.packet import PacketComposer
from host_refactor.runner import HostRunner
from host_refactor.trellis_adapter import (
    TrellisDomainAdapter,
    TrellisRuntimeSpec,
    trellis_execution_manifest,
    trellis_spec,
)
from host_refactor.trellis_fixture import build_e83_kernel


RUN_ID = "2026-08-28-host-refactor-live-smoke-v0"
SCOPE = "host_refactor_live_smoke_v0"
MAXIMUM_NEW_MODEL_CALLS = 1
MAXIMUM_SERIALIZED_TOKENS = 30_000
EXPECTED_ORDINARY_TOKENS = 21_401
EXPECTED_RELIEF_TOKENS = 18_785
EXPECTED_RELIEF_RESULT_IDS = ("RESULT-001",)
EXPECTED_PENDING_RESULT_ID = "RESULT-007"


def live_smoke_execution_manifest(repository_root: Path) -> dict[str, object]:
    root = repository_root.resolve()
    base = trellis_execution_manifest(root)
    declared = (
        root / "HOST_LIVE_SMOKE_CONTRACT.json",
        root / "MODEL_PROFILE_LOCK.json",
        root / "RUNTIME_ASSET_MANIFEST.json",
        root / "MEASURED_RUNTIME_COMMAND.json",
        root / "host_refactor" / "live_smoke.py",
        root / "tools" / "run_host_refactor_live_smoke.py",
        root / "tools" / "verify_runtime_assets.py",
    )
    payload = {
        "base_execution_manifest_sha256": base["execution_manifest_sha256"],
        "files": {
            path.relative_to(root).as_posix(): sha256_file(path)
            for path in sorted(declared)
        },
        "schema": "host-refactor-live-smoke-execution-manifest-v0",
    }
    return {
        **payload,
        "execution_manifest_sha256": sha256_bytes(canonical_json_bytes(payload)),
    }


def smoke_spec(repository_root: Path) -> TrellisRuntimeSpec:
    base = trellis_spec(repository_root)
    manifest = live_smoke_execution_manifest(repository_root)
    configuration = replace(
        base.configuration,
        run_id=RUN_ID,
        execution_manifest_sha256=str(manifest["execution_manifest_sha256"]),
        tranche_calls=8,
        maximum_calls=60,
        maximum_serialized_tokens=MAXIMUM_SERIALIZED_TOKENS,
    )
    return replace(base, configuration=configuration, execution_manifest=manifest)


def build_live_smoke_system(
    *,
    repository_root: Path,
    trajectory_root: Path,
    count_messages: CountMessages,
    count_text: Callable[[str], int] | None = None,
) -> tuple[HostRunner, TrellisDomainAdapter, HostKernel, RuntimeCounters]:
    spec = smoke_spec(repository_root)
    adapter = TrellisDomainAdapter(
        spec=spec,
        trajectory_root=trajectory_root,
        count_text=count_text,
    )
    adapter.next_result_index = 8
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
    return host, adapter, build_e83_kernel(repository_root), RuntimeCounters()


def assert_pressure_preflight(host: HostRunner, kernel: HostKernel) -> None:
    ordinary = host.composer.compose(kernel)
    ordinary_tokens = host.capacity.count_messages(ordinary.message_list())
    if ordinary_tokens != EXPECTED_ORDINARY_TOKENS:
        raise RuntimeError(
            f"E83 ordinary token mismatch: {ordinary_tokens} != {EXPECTED_ORDINARY_TOKENS}"
        )
    outcome = host.capacity.ensure_feasible(
        kernel,
        protected_result_ids=(EXPECTED_PENDING_RESULT_ID,),
    )
    if not outcome.feasible:
        raise RuntimeError("E83 live-smoke relief is not feasible")
    if outcome.selected_result_ids != EXPECTED_RELIEF_RESULT_IDS:
        raise RuntimeError(
            "E83 live-smoke relief selection mismatch: "
            f"{outcome.selected_result_ids} != {EXPECTED_RELIEF_RESULT_IDS}"
        )
    if outcome.prompt_tokens != EXPECTED_RELIEF_TOKENS:
        raise RuntimeError(
            f"E83 relief token mismatch: {outcome.prompt_tokens} != {EXPECTED_RELIEF_TOKENS}"
        )
    state = kernel.project()
    if state.pending_result_ids != (EXPECTED_PENDING_RESULT_ID,):
        raise RuntimeError(f"unexpected E83 pending results: {state.pending_result_ids}")


def qualifying_disposition(value: TerminalCode) -> bool:
    return value in {TerminalCode.CHECKPOINT_PAUSE, TerminalCode.COMPLETED}
