from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from reactive_runtime.canonical import write_json

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
    calls_attempted: int
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
    disposition: TerminalCode | None = None
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
        domain_state=domain.snapshot(),
    )
    review = host.checkpoint.review_packet(
        kernel,
        counters,
        host.composer,
    )
    review_path = run_root / "MECHANICAL_REVIEW.json"
    write_json(review_path, review)
    write_json(
        run_root / "TRANCHE_RESULT.json",
        {
            "calls_attempted": len(kernel.project().completed_calls) - start_calls,
            "checkpoint_path": checkpoint_path.name,
            "disposition": disposition.value,
            "events_sha256": kernel.project().events_sha256,
            "review_path": review_path.name,
            "schema": "bounded-host-tranche-result-v0",
        },
    )
    return TrancheResult(
        kernel=kernel,
        counters=counters,
        disposition=disposition,
        calls_attempted=len(kernel.project().completed_calls) - start_calls,
        checkpoint_path=checkpoint_path,
        review_path=review_path,
    )
