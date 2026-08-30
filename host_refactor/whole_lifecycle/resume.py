from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from host_refactor.checkpoint import RuntimeCounters
from host_refactor.effect_lifecycle import EffectLifecycleInteractionOrchestrator
from host_refactor.kernel import HostKernel
from host_refactor.lifecycle_scout.adapter import LifecycleScoutAdapter
from host_refactor.whole_lifecycle.system import build_resumed_system
from reactive_runtime.canonical import load_json


def hydrate_checkpoint(
    *,
    repository_root: Path,
    checkpoint_path: Path,
    trajectory_root: Path,
    count_messages: Callable[[list[dict[str, str]]], int],
    count_text: Callable[[str], int],
    maintenance_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> tuple[
    EffectLifecycleInteractionOrchestrator,
    LifecycleScoutAdapter,
    HostKernel,
    RuntimeCounters,
]:
    checkpoint = load_json(checkpoint_path)
    domain = checkpoint.get("domain_state")
    if not isinstance(domain, Mapping):
        raise ValueError("checkpoint lacks domain state")
    trellis = domain.get("trellis")
    interaction = domain.get("interaction")
    if not isinstance(trellis, Mapping) or not isinstance(interaction, Mapping):
        raise ValueError("checkpoint lacks Trellis interaction snapshots")
    host, adapter, _unused, orchestrator = build_resumed_system(
        repository_root=repository_root,
        trajectory_root=trajectory_root,
        count_messages=count_messages,
        count_text=count_text,
        maintenance_complete=maintenance_complete,
        domain_snapshot=trellis,
        lifecycle_snapshot=interaction,
    )
    kernel, counters, hydrated_domain = host.checkpoint.hydrate_with_domain(
        checkpoint,
        host.configuration,
    )
    expected = {
        "interaction": orchestrator.lifecycle.as_dict(),
        "trellis": adapter.snapshot(),
    }
    if hydrated_domain != expected:
        raise ValueError("hydrated domain differs from exact checkpoint")
    return orchestrator, adapter, kernel, counters
