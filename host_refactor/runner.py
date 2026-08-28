from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from reactive_runtime.canonical import canonical_json_text, sha256_bytes

from host_refactor.binding import RequestBinding, RequestBindingError
from host_refactor.capacity import CapacityManager, CapacityOutcome
from host_refactor.checkpoint import (
    CheckpointController,
    RuntimeCounters,
)
from host_refactor.kernel import HostKernel
from host_refactor.model import (
    ExactResult,
    ExactStateObject,
    ProjectedHostState,
    RunConfiguration,
    TerminalCode,
    TranscriptEntry,
)
from host_refactor.packet import ModelPacket, PacketComposer
from host_refactor.provider import OneShotProvider, ProviderFailure, ProviderSuccess


@dataclass(frozen=True)
class ActionRejection:
    code: str
    message: str
    attempted_action: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class DomainOutcome:
    result: ExactResult | None = None
    state_updates: tuple[ExactStateObject, ...] = ()
    terminal: TerminalCode | None = None
    action: Mapping[str, Any] | None = None
    rejection: ActionRejection | None = None
    reopen_result_id: str | None = None

    def __post_init__(self) -> None:
        if self.rejection is not None and self.terminal is not None:
            raise ValueError("ordinary rejection cannot also be terminal")
        if self.reopen_result_id is not None and self.result is not None:
            raise ValueError("reopen cannot also create a new exact result")


class DomainAdapter(Protocol):
    def handle(
        self, content: str, *, call_index: int, kernel: HostKernel
    ) -> DomainOutcome: ...


PayloadBuilder = Callable[
    [ModelPacket, RunConfiguration, ProjectedHostState], Mapping[str, Any]
]


@dataclass(frozen=True)
class RunnerStep:
    kernel: HostKernel
    counters: RuntimeCounters
    capacity: CapacityOutcome
    disposition: TerminalCode | None
    provider_attempts: int
    provider_elapsed_ms: float | None = None


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
        if capacity.prompt_limit != configuration.prompt_limit:
            raise ValueError(
                "capacity prompt allowance differs from context minus reserve"
            )
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
        if (
            self.configuration.maximum_serialized_tokens is not None
            and counters.serialized_tokens
            + capacity.prompt_tokens
            + self.configuration.response_reserve
            > self.configuration.maximum_serialized_tokens
        ):
            stopped = kernel.record_terminal(TerminalCode.TOKEN_BUDGET_EXHAUSTED)
            return RunnerStep(
                stopped,
                counters,
                capacity,
                TerminalCode.TOKEN_BUDGET_EXHAUSTED,
                0,
            )
        payload = self.payload_builder(
            capacity.packet,
            self.configuration,
            kernel.project(),
        )
        try:
            request_binding = RequestBinding.bind(
                capacity.packet,
                payload,
                expected_max_tokens=self.configuration.response_reserve,
            )
        except RequestBindingError as exc:
            stopped = kernel.record_request_binding_rejection(
                call_index=next_call,
                packet_sha256=capacity.packet.sha256,
                packet_manifest_sha256=capacity.packet.manifest_sha256,
                error_message=str(exc),
            ).record_terminal(TerminalCode.REQUEST_BINDING_FAILURE)
            return RunnerStep(
                stopped,
                counters,
                capacity,
                TerminalCode.REQUEST_BINDING_FAILURE,
                0,
            )
        request_sha256 = request_binding.final_request_sha256
        provider = OneShotProvider(provider_complete)
        provider_outcome = provider.invoke(payload, custody_root=provider_custody_root)
        provider_custody = self._provider_custody(provider_custody_root)
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
                request_binding=request_binding.as_dict(),
                provider_custody=provider_custody,
            )
            return RunnerStep(
                failed,
                next_counters,
                capacity,
                TerminalCode.PROVIDER_FAILURE,
                provider.attempts,
                provider_outcome.elapsed_ms,
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
            included_result_ids=request_binding.included_result_ids,
            request_sha256=request_sha256,
            response_sha256=response_sha256,
            usage=provider_outcome.usage,
            request_binding=request_binding.as_dict(),
            finish_reason=provider_outcome.finish_reason,
            provider_custody=provider_custody,
        )
        completed = completed.append_transcript(
            TranscriptEntry(
                entry_id=f"CALL-{next_call:06d}-ASSISTANT",
                role="assistant",
                content=provider_outcome.content,
            )
        )
        candidate_before = self._candidate_sha256(completed)
        if provider_outcome.finish_reason not in set(
            self.configuration.accepted_finish_reasons
        ):
            rejection_id = f"HOST-RESPONSE-REJECTION-{next_call:06d}"
            rejection = self._rejection_result(
                result_id=rejection_id,
                result_kind="response_rejection",
                call_index=next_call,
                code="finish_reason_not_accepted",
                message=(
                    "provider finish reason is not eligible for action processing: "
                    f"{provider_outcome.finish_reason}"
                ),
                candidate_sha256=candidate_before,
            )
            completed = completed.record_response_rejection(
                call_index=next_call,
                finish_reason=provider_outcome.finish_reason,
                response_sha256=response_sha256,
                rejection_result_id=rejection_id,
            )
            completed = completed.record_action_disposition(
                call_index=next_call,
                status="response_rejected",
                response_sha256=response_sha256,
                candidate_sha256_before=candidate_before,
                candidate_sha256_after=candidate_before,
                rejection_code="finish_reason_not_accepted",
                rejection_message=rejection.payload_content,
                result_id=rejection_id,
            )
            completed = completed.acquire(rejection).schedule(
                rejection_id,
                call_index=next_call + 1,
                transcript_entry_id=f"CALL-{next_call:06d}-RESPONSE-REJECTION",
            )
            return self._finish_step(
                completed,
                next_counters,
                capacity,
                provider.attempts,
                provider_outcome.elapsed_ms,
            )
        try:
            domain_outcome = domain.handle(
                provider_outcome.content,
                call_index=next_call,
                kernel=completed,
            )
        except Exception:
            stopped = completed.record_terminal(TerminalCode.DOMAIN_FAILURE)
            return RunnerStep(
                stopped,
                next_counters,
                capacity,
                TerminalCode.DOMAIN_FAILURE,
                provider.attempts,
                provider_outcome.elapsed_ms,
            )
        if domain_outcome.rejection is not None:
            rejection_id = f"HOST-ACTION-REJECTION-{next_call:06d}"
            rejection = self._rejection_result(
                result_id=rejection_id,
                result_kind="action_rejection",
                call_index=next_call,
                code=domain_outcome.rejection.code,
                message=domain_outcome.rejection.message,
                candidate_sha256=candidate_before,
            )
            completed = completed.acquire(rejection).schedule(
                rejection_id,
                call_index=next_call + 1,
                transcript_entry_id=f"CALL-{next_call:06d}-ACTION-REJECTION",
            )
        elif domain_outcome.reopen_result_id is not None:
            completed = completed.request_reopen(
                domain_outcome.reopen_result_id,
                call_index=next_call + 1,
                transcript_entry_id=f"CALL-{next_call:06d}-REOPEN",
            )
        elif domain_outcome.result is not None:
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
        candidate_after = self._candidate_sha256(completed)
        completed = completed.record_action_disposition(
            call_index=next_call,
            status=(
                "rejected" if domain_outcome.rejection is not None else "accepted"
            ),
            response_sha256=response_sha256,
            candidate_sha256_before=candidate_before,
            candidate_sha256_after=candidate_after,
            action=(
                domain_outcome.action
                if domain_outcome.action is not None
                else (
                    None
                    if domain_outcome.rejection is None
                    else domain_outcome.rejection.attempted_action
                )
            ),
            rejection_code=(
                None
                if domain_outcome.rejection is None
                else domain_outcome.rejection.code
            ),
            rejection_message=(
                None
                if domain_outcome.rejection is None
                else domain_outcome.rejection.message
            ),
            result_id=(
                f"HOST-ACTION-REJECTION-{next_call:06d}"
                if domain_outcome.rejection is not None
                else (
                    domain_outcome.reopen_result_id
                    if domain_outcome.reopen_result_id is not None
                    else (
                        None
                        if domain_outcome.result is None
                        else domain_outcome.result.result_id
                    )
                )
            ),
        )
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
            provider_outcome.elapsed_ms,
        )

    def _finish_step(
        self,
        kernel: HostKernel,
        counters: RuntimeCounters,
        capacity: CapacityOutcome,
        provider_attempts: int,
        provider_elapsed_ms: float | None = None,
    ) -> RunnerStep:
        disposition: TerminalCode | None = None
        checkpoint = self.checkpoint.decision(kernel, counters)
        if checkpoint.reason == "maximum_call_budget":
            disposition = TerminalCode.CALL_BUDGET_EXHAUSTED
            kernel = kernel.record_terminal(disposition)
        elif checkpoint.reason == "maximum_serialized_token_budget":
            disposition = TerminalCode.TOKEN_BUDGET_EXHAUSTED
            kernel = kernel.record_terminal(disposition)
        elif checkpoint.pause:
            disposition = TerminalCode.CHECKPOINT_PAUSE
        return RunnerStep(
            kernel,
            counters,
            capacity,
            disposition,
            provider_attempts,
            provider_elapsed_ms,
        )

    @staticmethod
    def _candidate_sha256(kernel: HostKernel) -> str | None:
        candidate = kernel.project().state_slots.get("current_candidate")
        if candidate is None:
            return None
        value = candidate.metadata.get("candidate_sha256")
        return None if value is None else str(value)

    @staticmethod
    def _rejection_result(
        *,
        result_id: str,
        result_kind: str,
        call_index: int,
        code: str,
        message: str,
        candidate_sha256: str | None,
    ) -> ExactResult:
        payload = canonical_json_text(
            {
                "call_index": call_index,
                "candidate_sha256": candidate_sha256,
                "code": code,
                "message": message,
                "repaired": False,
                "schema": "bounded-host-action-rejection-v0",
            }
        )
        return ExactResult(
            result_id=result_id,
            result_kind=result_kind,
            object_id=f"rejection:call-{call_index:06d}",
            object_version=str(candidate_sha256 or "no-candidate"),
            exact_content=payload,
            payload_content=payload,
            acquired_call=call_index,
            candidate_sha256_after=str(candidate_sha256 or ""),
            relief_eligible=False,
            metadata={"code": code},
        )

    @staticmethod
    def _provider_custody(root: Path | None) -> Mapping[str, str]:
        if root is None:
            return {}
        paths = {
            "attempt_path": str(root / "ATTEMPT.json"),
            "failure_path": str(root / "FAILURE.json"),
            "request_path": str(root / "REQUEST.json"),
            "response_path": str(root / "RESPONSE.json"),
        }
        return {
            key: value for key, value in paths.items() if Path(value).is_file()
        }


def default_payload_builder(
    packet: ModelPacket,
    configuration: RunConfiguration,
    state: ProjectedHostState,
) -> Mapping[str, Any]:
    del state
    return {
        "messages": packet.message_list(),
        "max_tokens": configuration.response_reserve,
        "run_id": configuration.run_id,
        "seed": configuration.seed,
    }
