from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from reactive_runtime.canonical import load_json, write_json

from host_refactor.checkpoint import RuntimeCounters
from host_refactor.kernel import HostKernel
from host_refactor.model import TerminalCode
from interaction_scout.lifecycle import InteractionLifecycle, InteractionOrchestrator


@dataclass(frozen=True)
class InteractionTrancheResult:
    kernel: HostKernel
    counters: RuntimeCounters
    lifecycle: InteractionLifecycle
    disposition: TerminalCode
    actor_attempts: int
    maintenance_attempts: int
    completed_actor_invocations: int
    failed_actor_invocations: int
    checkpoint_path: Path
    review_path: Path


def _next_call(kernel: HostKernel) -> int:
    state = kernel.project()
    return max((*state.completed_calls, *state.failed_calls), default=0) + 1


def run_interaction_tranche(
    *,
    orchestrator: InteractionOrchestrator,
    kernel: HostKernel,
    counters: RuntimeCounters,
    actor_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    run_root: Path,
    parent_checkpoint_path: Path | None = None,
) -> InteractionTrancheResult:
    if run_root.exists():
        raise FileExistsError(f"interaction tranche root already exists: {run_root}")
    run_root.mkdir(parents=True)
    host = orchestrator.host
    adapter = orchestrator.adapter
    start_calls = len(kernel.project().completed_calls)
    start_failures = len(kernel.project().failed_calls)
    start_attempts = counters.provider_attempts
    start_maintenance = orchestrator.lifecycle.maintenance_calls
    parent_checkpoint_sha256: str | None = None
    if parent_checkpoint_path is not None:
        value = load_json(parent_checkpoint_path)
        parent_kernel, parent_counters, domain = host.checkpoint.hydrate_with_domain(
            value,
            host.configuration,
        )
        expected_domain = {
            "interaction": orchestrator.lifecycle.as_dict(),
            "trellis": adapter.snapshot(),
        }
        if parent_kernel.as_dict() != kernel.as_dict():
            raise ValueError("parent checkpoint event state differs from resume state")
        if parent_counters != counters:
            raise ValueError("parent checkpoint counters differ from resume counters")
        if domain != expected_domain:
            raise ValueError("parent checkpoint interaction state differs from resume state")
        parent_checkpoint_sha256 = str(value["checkpoint_sha256"])
    elif start_calls or start_failures or start_attempts:
        raise ValueError("resumed interaction tranche requires a verified parent checkpoint")

    disposition: TerminalCode | None = None
    timing: list[dict[str, Any]] = []
    while disposition is None:
        call_index = _next_call(kernel)
        step = orchestrator.step(
            kernel=kernel,
            counters=counters,
            actor_complete=actor_complete,
            custody_root=run_root / f"call-{call_index:03d}",
        )
        kernel = step.runner_step.kernel
        counters = step.runner_step.counters
        disposition = step.runner_step.disposition
        timing.append(
            {
                "actor_call": call_index,
                "actor_elapsed_ms": step.runner_step.provider_elapsed_ms,
                "actor_provider_attempts": step.runner_step.provider_attempts,
                "cumulative_maintenance_calls": step.lifecycle.maintenance_calls,
                "disposition": None if disposition is None else disposition.value,
                "prompt_tokens": step.runner_step.capacity.prompt_tokens,
            }
        )
        write_json(run_root / "TRANCHE_TIMING.json", timing)
    if disposition is None:  # pragma: no cover
        raise AssertionError("interaction tranche exited without disposition")

    checkpoint_path = run_root / "CHECKPOINT.json"
    host.checkpoint.write(
        checkpoint_path,
        kernel,
        counters,
        parent_checkpoint_sha256=parent_checkpoint_sha256,
        domain_state={
            "interaction": orchestrator.lifecycle.as_dict(),
            "trellis": adapter.snapshot(),
        },
    )
    review = host.checkpoint.review_packet(kernel, counters, host.composer)
    review["interaction_lifecycle"] = orchestrator.lifecycle.as_dict()
    review["tranche_timing"] = timing
    review_path = run_root / "MECHANICAL_REVIEW.json"
    write_json(review_path, review)
    actor_attempts = len(kernel.project().completed_calls) - start_calls + (
        len(kernel.project().failed_calls) - start_failures
    )
    maintenance_attempts = orchestrator.lifecycle.maintenance_calls - start_maintenance
    write_json(
        run_root / "TRANCHE_RESULT.json",
        {
            "actor_attempts": actor_attempts,
            "checkpoint_path": checkpoint_path.name,
            "completed_actor_invocations": len(kernel.project().completed_calls)
            - start_calls,
            "disposition": disposition.value,
            "events_sha256": kernel.project().events_sha256,
            "failed_actor_invocations": len(kernel.project().failed_calls)
            - start_failures,
            "maintenance_attempts": maintenance_attempts,
            "parent_checkpoint_sha256": parent_checkpoint_sha256,
            "provider_attempts": counters.provider_attempts - start_attempts,
            "review_path": review_path.name,
            "schema": "trellis-interaction-tranche-result-v0",
        },
    )
    return InteractionTrancheResult(
        kernel=kernel,
        counters=counters,
        lifecycle=orchestrator.lifecycle,
        disposition=disposition,
        actor_attempts=actor_attempts,
        maintenance_attempts=maintenance_attempts,
        completed_actor_invocations=len(kernel.project().completed_calls) - start_calls,
        failed_actor_invocations=len(kernel.project().failed_calls) - start_failures,
        checkpoint_path=checkpoint_path,
        review_path=review_path,
    )
