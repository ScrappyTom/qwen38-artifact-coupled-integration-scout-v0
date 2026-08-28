from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from reactive_runtime.canonical import canonical_json_bytes, sha256_bytes

from host_refactor.capacity import CapacityManager, CapacityOutcome
from host_refactor.checkpoint import (
    CheckpointController,
    RuntimeCounters,
)
from host_refactor.kernel import HostKernel
from host_refactor.model import (
    ExactResult,
    ExactStateObject,
    RunConfiguration,
    TerminalCode,
    TranscriptEntry,
)
from host_refactor.packet import ModelPacket, PacketComposer
from host_refactor.provider import OneShotProvider, ProviderFailure, ProviderSuccess


@dataclass(frozen=True)
class DomainOutcome:
    result: ExactResult | None = None
    state_updates: tuple[ExactStateObject, ...] = ()
    terminal: TerminalCode | None = None


class DomainAdapter(Protocol):
    def handle(
        self, content: str, *, call_index: int, kernel: HostKernel
    ) -> DomainOutcome: ...


PayloadBuilder = Callable[[ModelPacket, RunConfiguration], Mapping[str, Any]]


@dataclass(frozen=True)
class RunnerStep:
    kernel: HostKernel
    counters: RuntimeCounters
    capacity: CapacityOutcome
    disposition: TerminalCode | None
    provider_attempts: int


class HostRunner:
    """Thin coordinator over the single host transition kernel."""

    def __init__(
        self,
        *,
        configuration: RunConfiguration,
        composer: PacketComposer,
        capacity: CapacityManager,
        checkpoint: CheckpointController,
        payload_builder: PayloadBuilder,
    ) -> None:
        if checkpoint.configuration != configuration:
            raise ValueError("checkpoint/configuration mismatch")
        if capacity.composer is not composer:
            raise ValueError("runner must share one packet composer")
        self.configuration = configuration
        self.composer = composer
        self.capacity = capacity
        self.checkpoint = checkpoint
        self.payload_builder = payload_builder

    def step(
        self,
        *,
        kernel: HostKernel,
        counters: RuntimeCounters,
        provider_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        domain: DomainAdapter,
        provider_custody_root: Path | None = None,
    ) -> RunnerStep:
        state = kernel.project()
        if state.terminal is not None:
            raise RuntimeError(f"cannot step terminal kernel: {state.terminal.value}")
        next_call = max((*state.completed_calls, *state.failed_calls), default=0) + 1
        if next_call > self.configuration.maximum_calls:
            stopped = kernel.record_terminal(TerminalCode.CALL_BUDGET_EXHAUSTED)
            capacity = self.capacity.ensure_feasible(stopped)
            return RunnerStep(
                stopped,
                counters,
                capacity,
                TerminalCode.CALL_BUDGET_EXHAUSTED,
                0,
            )
        pending = tuple(
            result_id
            for result_id, row in state.results.items()
            if row.pending_call == next_call
        )
        capacity = self.capacity.ensure_feasible(
            kernel,
            protected_result_ids=pending,
        )
        kernel = capacity.kernel
        if not capacity.feasible:
            stopped = kernel.record_terminal(TerminalCode.CAPACITY_BLOCKED)
            return RunnerStep(
                stopped,
                counters,
                capacity,
                TerminalCode.CAPACITY_BLOCKED,
                0,
            )
        payload = self.payload_builder(capacity.packet, self.configuration)
        request_sha256 = sha256_bytes(canonical_json_bytes(payload))
        provider = OneShotProvider(provider_complete)
        provider_outcome = provider.invoke(payload, custody_root=provider_custody_root)
        next_counters = RuntimeCounters(
            serialized_tokens=counters.serialized_tokens,
            provider_attempts=counters.provider_attempts + provider.attempts,
        )
        if isinstance(provider_outcome, ProviderFailure):
            failed = kernel.fail_provider(
                call_index=next_call,
                request_sha256=request_sha256,
                error_type=provider_outcome.error_type,
                error_message=provider_outcome.error_message,
            )
            return RunnerStep(
                failed,
                next_counters,
                capacity,
                TerminalCode.PROVIDER_FAILURE,
                provider.attempts,
            )
        if not isinstance(provider_outcome, ProviderSuccess):  # pragma: no cover
            raise AssertionError("unknown provider outcome")
        usage_total = provider_outcome.usage.get("total_tokens", 0)
        if not isinstance(usage_total, int) or usage_total < 0:
            raise ValueError("provider total_tokens must be a non-negative integer")
        next_counters = RuntimeCounters(
            serialized_tokens=counters.serialized_tokens + usage_total,
            provider_attempts=next_counters.provider_attempts,
        )
        response_sha256 = sha256_bytes(provider_outcome.content.encode("utf-8"))
        completed = kernel.complete_invocation(
            call_index=next_call,
            included_result_ids=pending,
            request_sha256=request_sha256,
            response_sha256=response_sha256,
            usage=provider_outcome.usage,
        )
        completed = completed.append_transcript(
            TranscriptEntry(
                entry_id=f"CALL-{next_call:06d}-ASSISTANT",
                role="assistant",
                content=provider_outcome.content,
            )
        )
        try:
            domain_outcome = domain.handle(
                provider_outcome.content,
                call_index=next_call,
                kernel=completed,
            )
        except Exception:
            stopped = completed.record_terminal(TerminalCode.INVALID_ACTION)
            return RunnerStep(
                stopped,
                next_counters,
                capacity,
                TerminalCode.INVALID_ACTION,
                provider.attempts,
            )
        if domain_outcome.result is not None:
            result = domain_outcome.result
            resident_result_id = completed.resident_match(result)
            if resident_result_id is not None:
                completed = completed.record_repeat_demand(
                    requested_result=result,
                    resident_result_id=resident_result_id,
                    feedback_entry_id=f"CALL-{next_call:06d}-ALREADY-RESIDENT",
                )
            else:
                completed = completed.acquire(result)
                completed = completed.schedule(
                    result.result_id,
                    call_index=next_call + 1,
                    transcript_entry_id=f"CALL-{next_call:06d}-RESULT",
                )
        for state_object in domain_outcome.state_updates:
            current = completed.project().state_slots.get(state_object.slot_id)
            if current is None or current.as_dict() != state_object.as_dict():
                completed = completed.set_state_object(state_object)
        disposition = domain_outcome.terminal
        if disposition is not None:
            completed = completed.record_terminal(disposition)
        else:
            checkpoint = self.checkpoint.decision(completed, next_counters)
            if checkpoint.reason == "maximum_call_budget":
                disposition = TerminalCode.CALL_BUDGET_EXHAUSTED
                completed = completed.record_terminal(disposition)
            elif checkpoint.reason == "maximum_serialized_token_budget":
                disposition = TerminalCode.TOKEN_BUDGET_EXHAUSTED
                completed = completed.record_terminal(disposition)
            elif checkpoint.pause:
                disposition = TerminalCode.CHECKPOINT_PAUSE
        return RunnerStep(
            completed,
            next_counters,
            capacity,
            disposition,
            provider.attempts,
        )


def default_payload_builder(
    packet: ModelPacket, configuration: RunConfiguration
) -> Mapping[str, Any]:
    return {
        "messages": packet.message_list(),
        "run_id": configuration.run_id,
        "seed": configuration.seed,
    }
