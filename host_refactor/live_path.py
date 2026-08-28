from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from reactive_runtime.canonical import load_json, write_json

from host_refactor.checkpoint import RuntimeCounters
from host_refactor.kernel import HostKernel
from host_refactor.model import TerminalCode
from host_refactor.runner import DomainAdapter, HostRunner


class SnapshotDomain(DomainAdapter, Protocol):
    def snapshot(self) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class TrancheResult:
    kernel: HostKernel
    counters: RuntimeCounters
    disposition: TerminalCode
    provider_attempts: int
    completed_invocations: int
    failed_invocations: int
    checkpoint_path: Path
    review_path: Path


def _next_call(kernel: HostKernel) -> int:
    state = kernel.project()
    return max((*state.completed_calls, *state.failed_calls), default=0) + 1


def run_tranche(
    *,
    host: HostRunner,
    kernel: HostKernel,
    counters: RuntimeCounters,
    domain: SnapshotDomain,
    provider_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    run_root: Path,
    parent_checkpoint_path: Path | None = None,
) -> TrancheResult:
    """Run until a mechanical pause or terminal disposition.

    This function owns no model server, authorization, task semantics, or
    qualitative loop judgment. A future authorized launcher supplies the
    provider callback and an empty run root.
    """

    if run_root.exists():
        raise FileExistsError(f"tranche run root already exists: {run_root}")
    run_root.mkdir(parents=True)
    start_calls = len(kernel.project().completed_calls)
    start_failures = len(kernel.project().failed_calls)
    start_attempts = counters.provider_attempts
    parent_checkpoint_sha256: str | None = None
    if parent_checkpoint_path is not None:
        parent_value = load_json(parent_checkpoint_path)
        parent_kernel, parent_counters, parent_domain = (
            host.checkpoint.hydrate_with_domain(
                parent_value,
                host.configuration,
            )
        )
        if parent_kernel.as_dict() != kernel.as_dict():
            raise ValueError("parent checkpoint event state differs from resume state")
        if parent_counters != counters:
            raise ValueError("parent checkpoint counters differ from resume counters")
        if parent_domain != dict(domain.snapshot()):
            raise ValueError("parent checkpoint domain state differs from resume state")
        parent_checkpoint_sha256 = str(parent_value["checkpoint_sha256"])
    elif start_calls or start_failures or start_attempts:
        raise ValueError("resumed tranche requires a verified parent checkpoint")
    disposition: TerminalCode | None = None
    provider_timing: list[dict[str, Any]] = []
    while disposition is None:
        call_index = _next_call(kernel)
        call_root = run_root / "actor" / f"call-{call_index:03d}"
        step = host.step(
            kernel=kernel,
            counters=counters,
            provider_complete=provider_complete,
            domain=domain,
            provider_custody_root=call_root / "provider_attempt",
        )
        kernel, counters = step.kernel, step.counters
        provider_timing.append(
            {
                "call_index": call_index,
                "elapsed_ms": step.provider_elapsed_ms,
                "provider_attempts": step.provider_attempts,
            }
        )
        write_json(
            call_root / "HOST_STEP.json",
            {
                "capacity_blocker": step.capacity.blocker,
                "disposition": (
                    None if step.disposition is None else step.disposition.value
                ),
                "events_sha256": kernel.project().events_sha256,
                "feasible": step.capacity.feasible,
                "prompt_tokens": step.capacity.prompt_tokens,
                "provider_attempts": step.provider_attempts,
                "provider_elapsed_ms": step.provider_elapsed_ms,
                "relief_audits": [
                    {
                        "before_tokens": row.before_tokens,
                        "prospective_tokens": row.prospective_tokens,
                        "reason": row.reason,
                        "result_id": row.result_id,
                        "savings": row.savings,
                        "selected": row.selected,
                    }
                    for row in step.capacity.audits
                ],
                "selected_relief_result_ids": list(step.capacity.selected_result_ids),
            },
        )
        disposition = step.disposition
    if disposition is None:  # pragma: no cover - loop invariant
        raise AssertionError("tranche exited without a disposition")
    checkpoint_path = run_root / "CHECKPOINT.json"
    host.checkpoint.write(
        checkpoint_path,
        kernel,
        counters,
        parent_checkpoint_sha256=parent_checkpoint_sha256,
        domain_state=domain.snapshot(),
    )
    review = dict(
        host.checkpoint.review_packet(
            kernel,
            counters,
            host.composer,
        )
    )
    review["provider_timing"] = provider_timing
    review_path = run_root / "MECHANICAL_REVIEW.json"
    write_json(review_path, review)
    write_json(
        run_root / "TRANCHE_RESULT.json",
        {
            "completed_invocations": (
                len(kernel.project().completed_calls) - start_calls
            ),
            "checkpoint_path": checkpoint_path.name,
            "disposition": disposition.value,
            "events_sha256": kernel.project().events_sha256,
            "failed_invocations": len(kernel.project().failed_calls) - start_failures,
            "parent_checkpoint_sha256": parent_checkpoint_sha256,
            "provider_attempts": counters.provider_attempts - start_attempts,
            "review_path": review_path.name,
            "schema": "bounded-host-tranche-result-v0",
        },
    )
    return TrancheResult(
        kernel=kernel,
        counters=counters,
        disposition=disposition,
        provider_attempts=counters.provider_attempts - start_attempts,
        completed_invocations=len(kernel.project().completed_calls) - start_calls,
        failed_invocations=len(kernel.project().failed_calls) - start_failures,
        checkpoint_path=checkpoint_path,
        review_path=review_path,
    )
