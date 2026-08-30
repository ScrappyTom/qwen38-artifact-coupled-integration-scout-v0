from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from host_refactor.checkpoint import RuntimeCounters
from host_refactor.kernel import HostKernel
from host_refactor.lifecycle_scout.adapter import LifecycleScoutAdapter
from host_refactor.lifecycle_scout_v1.system import build_system
from host_refactor.effect_lifecycle import EffectLifecycleInteractionOrchestrator
from reactive_runtime.canonical import load_json


PARENT_RUN_ID = "2026-08-29-trellis-e99-verification-lifecycle-scout-v1"


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
    """Hydrate the exact sealed E99 live checkpoint under unchanged host policy."""

    checkpoint = load_json(checkpoint_path)
    domain = checkpoint.get("domain_state")
    if not isinstance(domain, Mapping):
        raise ValueError("parent checkpoint lacks domain state")
    trellis = domain.get("trellis")
    interaction = domain.get("interaction")
    if not isinstance(trellis, Mapping) or not isinstance(interaction, Mapping):
        raise ValueError("parent checkpoint lacks Trellis interaction snapshots")
    host, adapter, orchestrator = build_system(
        repository_root=repository_root,
        trajectory_root=trajectory_root,
        domain_snapshot=trellis,
        lifecycle_snapshot=interaction,
        count_messages=count_messages,
        count_text=count_text,
        maintenance_complete=maintenance_complete,
    )
    kernel, counters, hydrated_domain = host.checkpoint.hydrate_with_domain(
        checkpoint,
        host.configuration,
    )
    expected_domain = {
        "interaction": orchestrator.lifecycle.as_dict(),
        "trellis": adapter.snapshot(),
    }
    if hydrated_domain != expected_domain:
        raise ValueError("hydrated domain differs from exact parent checkpoint")
    return orchestrator, adapter, kernel, counters
