from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from reactive_runtime.canonical import load_json

from host_refactor.checkpoint import RuntimeCounters
from host_refactor.kernel import HostKernel
from host_refactor.trellis_adapter import TrellisDomainAdapter
from interaction_scout.lifecycle import InteractionLifecycle, InteractionOrchestrator
from interaction_scout.system import build_interaction_system


PARENT_RUN_ID = "2026-08-29-trellis-refactored-interaction-tranche-v0"


def hydrate_continuation(
    *,
    repository_root: Path,
    checkpoint_path: Path,
    trajectory_root: Path,
    configuration_id: str,
    count_messages: Callable[[list[dict[str, str]]], int],
    count_text: Callable[[str], int],
    maintenance_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None,
) -> tuple[
    InteractionOrchestrator,
    TrellisDomainAdapter,
    HostKernel,
    RuntimeCounters,
]:
    """Hydrate one exact E94 checkpoint without changing its frozen runtime policy."""

    host, template_adapter, _, _ = build_interaction_system(
        repository_root=repository_root,
        trajectory_root=trajectory_root / "template",
        configuration_id=configuration_id,
        run_id=f"{PARENT_RUN_ID}:{configuration_id}",
        count_messages=count_messages,
        count_text=count_text,
        maintenance_complete=maintenance_complete,
    )
    checkpoint = load_json(checkpoint_path)
    kernel, counters, domain = host.checkpoint.hydrate_with_domain(
        checkpoint,
        host.configuration,
    )
    if domain is None:
        raise ValueError("parent checkpoint lacks interaction domain state")
    adapter = TrellisDomainAdapter.from_snapshot(
        spec=template_adapter.spec,
        trajectory_root=trajectory_root / "resumed",
        snapshot=domain["trellis"],
        count_text=count_text,
    )
    lifecycle = InteractionLifecycle.from_dict(domain["interaction"])
    orchestrator = InteractionOrchestrator(
        host=host,
        adapter=adapter,
        lifecycle=lifecycle,
        count_messages=count_messages,
        count_text=count_text,
        maintenance_complete=maintenance_complete,
        maximum_maintenance_calls=12,
    )
    return orchestrator, adapter, kernel, counters
