from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Mapping

import pytest

from host_refactor.capacity import CapacityManager
from host_refactor.checkpoint import CheckpointController, RuntimeCounters
from host_refactor.kernel import HostKernel
from host_refactor.live_path import run_tranche
from host_refactor.model import (
    DeliveryState,
    EventKind,
    ExactResult,
    ExactStateObject,
    RunConfiguration,
    TerminalCode,
    TranscriptEntry,
)
from host_refactor.packet import PacketComposer
from host_refactor.runner import (
    ActionRejection,
    DomainOutcome,
    HostRunner,
    default_payload_builder,
)
from host_refactor.trellis_adapter import (
    build_trellis_host,
    trellis_execution_manifest,
    trellis_spec,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_A = "a" * 64
MANIFEST_B = "b" * 64


def config(
    *,
    tranche: int = 12,
    maximum_calls: int = 60,
    maximum_serialized_tokens: int | None = 100_000,
    execution_manifest_sha256: str = MANIFEST_A,
) -> RunConfiguration:
    return RunConfiguration(
        run_id="live-hardening-test",
        task_id="task",
        seed=42,
        context_window=11_000,
        response_reserve=1_000,
        execution_manifest_sha256=execution_manifest_sha256,
        accepted_finish_reasons=("stop",),
        tranche_calls=tranche,
        maximum_calls=maximum_calls,
        maximum_serialized_tokens=maximum_serialized_tokens,
    )


def count_chars(messages: list[dict[str, str]]) -> int:
    return sum(len(row["content"]) for row in messages)


class NoResultDomain:
    calls = 0

    def handle(
        self, content: str, *, call_index: int, kernel: HostKernel
    ) -> DomainOutcome:
        self.calls += 1
        return DomainOutcome(action={"action": "noop"})

    def snapshot(self) -> Mapping[str, Any]:
        return {"calls": self.calls, "schema": "hardening-test-domain-v0"}


class RejectOnceDomain(NoResultDomain):
    def handle(
        self, content: str, *, call_index: int, kernel: HostKernel
    ) -> DomainOutcome:
        self.calls += 1
        if self.calls == 1:
            return DomainOutcome(
                rejection=ActionRejection(
                    code="no_effect",
                    message="candidate replacement is byte-identical",
                    attempted_action={"action": "replace"},
                )
            )
        return DomainOutcome(action={"action": "noop"})


def make_host(
    configuration: RunConfiguration,
    *,
    payload_builder=default_payload_builder,
) -> HostRunner:
    composer = PacketComposer()
    return HostRunner(
        configuration=configuration,
        composer=composer,
        capacity=CapacityManager(
            composer=composer,
            count_messages=count_chars,
            prompt_limit=configuration.prompt_limit,
        ),
        checkpoint=CheckpointController(configuration),
        payload_builder=payload_builder,
    )


def provider(content: str = "{}", finish_reason: str = "stop"):
    def complete(_: Mapping[str, Any]) -> Mapping[str, Any]:
        return {
            "content": content,
            "finish_reason": finish_reason,
            "usage": {
                "cached_tokens": 3,
                "completion_tokens": 1,
                "prompt_tokens": 9,
                "total_tokens": 10,
            },
        }

    return complete


def pending_kernel() -> HostKernel:
    result = ExactResult(
        result_id="RESULT-001",
        result_kind="source_observation",
        object_id="SOURCE:1-1",
        object_version="v1",
        exact_content="exact wrapper\n--- exact result body ---\nalpha",
        payload_content="alpha",
        acquired_call=0,
        candidate_sha256_after="candidate-0",
        span_key="SOURCE:1-1",
    )
    return (
        HostKernel()
        .acquire(result)
        .schedule(
            result.result_id,
            call_index=1,
            transcript_entry_id="RESULT-001-ENTRY",
        )
    )


def test_payload_builder_cannot_drop_pending_result_and_commit_delivery() -> None:
    attempted = 0

    def faulty_builder(packet, configuration, state):
        del packet, configuration, state
        return {"messages": []}

    def should_not_run(_: Mapping[str, Any]) -> Mapping[str, Any]:
        nonlocal attempted
        attempted += 1
        return provider()( {})

    step = make_host(config(), payload_builder=faulty_builder).step(
        kernel=pending_kernel(),
        counters=RuntimeCounters(),
        provider_complete=should_not_run,
        domain=NoResultDomain(),
    )
    assert attempted == 0
    assert step.disposition is TerminalCode.REQUEST_BINDING_FAILURE
    assert (
        step.kernel.project().results["RESULT-001"].delivery_state
        is DeliveryState.PENDING
    )


def test_length_response_is_custodied_rejected_and_never_executed() -> None:
    domain = NoResultDomain()
    raw_content = '{"action":"noop","padding":"' + ("x" * 8_000) + '"}'
    host = make_host(config())
    with tempfile.TemporaryDirectory() as temp:
        custody = Path(temp) / "provider"
        step = host.step(
            kernel=HostKernel(),
            counters=RuntimeCounters(),
            provider_complete=provider(raw_content, "length"),
            domain=domain,
            provider_custody_root=custody,
        )
        assert (custody / "RESPONSE.json").is_file()
        custodied_response = json.loads(
            (custody / "RESPONSE.json").read_text(encoding="utf-8")
        )
        assert custodied_response["content"] == raw_content
    state = step.kernel.project()
    assert domain.calls == 0
    assert state.terminal is None
    assert state.completed_calls == (1,)
    assert len(state.pending_result_ids) == 1
    rejection = state.results[state.pending_result_ids[0]].result
    assert rejection.result_kind == "response_rejection"
    assert any(event.kind is EventKind.RESPONSE_REJECTED for event in step.kernel.events)
    assert any(
        event.kind is EventKind.REJECTED_RESPONSE_EXTERNALIZED
        for event in step.kernel.events
    )
    assistant = next(
        row for row in state.transcript if row.entry_id == "CALL-000001-ASSISTANT"
    )
    assert assistant.entry_kind == "rejected_assistant_response_receipt"
    assert raw_content not in assistant.content
    receipt = json.loads(assistant.content)
    assert receipt["admitted_action"] is False
    assert receipt["world_transition_applied"] is False
    assert receipt["exact_response_retained_externally"] is True
    raw_append = next(
        event
        for event in step.kernel.events
        if event.kind is EventKind.TRANSCRIPT_APPENDED
        and event.data["entry"]["entry_id"] == "CALL-000001-ASSISTANT"
    )
    assert raw_append.data["entry"]["content"] == raw_content
    assert len(assistant.content) < len(raw_content) // 10

    second = host.step(
        kernel=step.kernel,
        counters=step.counters,
        provider_complete=provider(raw_content, "length"),
        domain=domain,
    )
    second_state = second.kernel.project()
    assert second_state.completed_calls == (1, 2)
    assert domain.calls == 0
    receipts = [
        row
        for row in second_state.transcript
        if row.entry_kind == "rejected_assistant_response_receipt"
    ]
    assert len(receipts) == 2
    packet_text = "\n".join(
        row["content"] for row in host.composer.compose(second.kernel).messages
    )
    assert raw_content not in packet_text


def test_ordinary_action_rejection_is_exact_nonterminal_and_continuable() -> None:
    candidate = ExactStateObject(
        slot_id="current_candidate",
        object_id="candidate:task",
        object_version="v0",
        exact_content="candidate zero",
        metadata={"candidate_sha256": "candidate-0"},
    )
    kernel = HostKernel().set_state_object(candidate).append_transcript(
        TranscriptEntry(
            "CURRENT",
            "user",
            candidate.exact_content,
            state_slot_id="current_candidate",
        )
    )
    host = make_host(config())
    domain = RejectOnceDomain()
    first = host.step(
        kernel=kernel,
        counters=RuntimeCounters(),
        provider_complete=provider(),
        domain=domain,
    )
    assert first.disposition is None
    assert first.kernel.project().terminal is None
    assert first.kernel.project().state_slots["current_candidate"] == candidate
    pending_id = first.kernel.project().pending_result_ids[0]
    assert first.kernel.project().results[pending_id].result.result_kind == "action_rejection"
    second = host.step(
        kernel=first.kernel,
        counters=first.counters,
        provider_complete=provider(),
        domain=domain,
    )
    assert second.kernel.project().completed_calls == (1, 2)
    assert (
        second.kernel.project().results[pending_id].delivery_state
        is DeliveryState.DELIVERED_RESIDENT
    )
    assert second.kernel.project().terminal is None


def test_trellis_reopen_uses_original_kernel_result_and_current_state_schema() -> None:
    read = json.dumps(
        {
            "action": "read_batch",
            "requests": [{"end_line": 20, "source_id": "COUNCIL", "start_line": 1}],
        }
    )
    noop_read = json.dumps(
        {
            "action": "read_batch",
            "requests": [{"end_line": 20, "source_id": "CLIMATE", "start_line": 1}],
        }
    )
    with tempfile.TemporaryDirectory() as temp:
        host, domain, kernel = build_trellis_host(
            repository_root=ROOT,
            trajectory_root=Path(temp) / "trajectory",
            count_messages=count_chars,
            count_text=len,
        )
        first = host.step(
            kernel=kernel,
            counters=RuntimeCounters(),
            provider_complete=provider(read),
            domain=domain,
        )
        second = host.step(
            kernel=first.kernel,
            counters=first.counters,
            provider_complete=provider(noop_read),
            domain=domain,
        )
        external = second.kernel.externalize("RESULT-001", reason="test")
        seen_payloads: list[Mapping[str, Any]] = []

        def reopen_complete(payload: Mapping[str, Any]) -> Mapping[str, Any]:
            seen_payloads.append(payload)
            return provider(json.dumps({"action": "reopen_exact", "result_id": "RESULT-001"}))(payload)

        reopened = host.step(
            kernel=external,
            counters=second.counters,
            provider_complete=reopen_complete,
            domain=domain,
        )
        pending_state = reopened.kernel.project()
        assert tuple(pending_state.results) == ("RESULT-001", "RESULT-002")
        assert pending_state.results["RESULT-001"].delivery_state is DeliveryState.PENDING
        assert pending_state.results["RESULT-001"].reopen_count == 1
        assert sum(event.kind is EventKind.REOPEN_REQUESTED for event in reopened.kernel.events) == 1

        # The next request delivers the reopen. Its schema must not advertise a
        # currently pending/resident result as reopenable because an old receipt exists.
        next_payloads: list[Mapping[str, Any]] = []

        def next_complete(payload: Mapping[str, Any]) -> Mapping[str, Any]:
            next_payloads.append(payload)
            return provider(noop_read)(payload)

        delivered = host.step(
            kernel=reopened.kernel,
            counters=reopened.counters,
            provider_complete=next_complete,
            domain=domain,
        )
        response_format = next_payloads[0]["response_format"]
        assert "RESULT-001" not in json.dumps(response_format, sort_keys=True)
        packet = host.composer.compose(delivered.kernel)
        body = delivered.kernel.project().results["RESULT-001"].result.payload_content
        assert "\n".join(row["content"] for row in packet.messages).count(body) == 1


def test_trellis_parse_rejection_is_nonterminal_and_next_call_continues() -> None:
    valid = json.dumps(
        {
            "action": "read_batch",
            "requests": [{"end_line": 10, "source_id": "CLIMATE", "start_line": 1}],
        }
    )
    with tempfile.TemporaryDirectory() as temp:
        host, domain, kernel = build_trellis_host(
            repository_root=ROOT,
            trajectory_root=Path(temp) / "trajectory",
            count_messages=count_chars,
            count_text=len,
        )
        rejected = host.step(
            kernel=kernel,
            counters=RuntimeCounters(),
            provider_complete=provider("not one action object"),
            domain=domain,
        )
        rejection_id = rejected.kernel.project().pending_result_ids[0]
        assert rejected.kernel.project().results[rejection_id].result.result_kind == "action_rejection"
        assert rejected.kernel.project().terminal is None
        continued = host.step(
            kernel=rejected.kernel,
            counters=rejected.counters,
            provider_complete=provider(valid),
            domain=domain,
        )
    assert continued.kernel.project().completed_calls == (1, 2)
    assert continued.kernel.project().terminal is None
    assert any(
        row.result.result_kind == "source_observation"
        for row in continued.kernel.project().results.values()
    )


def test_trellis_execution_manifest_binds_task_model_schema_adapter_and_evaluator() -> None:
    manifest = trellis_execution_manifest(ROOT)
    files = manifest["files"]
    assert "TRELLIS_MODEL_PROFILE_LOCK.json" in files
    assert "task_trellis/TASK_SOURCE_LOCK.json" in files
    assert "task_trellis/evaluator/evaluate.py" in files
    assert "reactive_runtime/actions.py" in files
    assert "host_refactor/trellis_adapter.py" in files
    assert (
        trellis_spec(ROOT).configuration.execution_manifest_sha256
        == manifest["execution_manifest_sha256"]
    )


def test_failed_request_records_attempt_not_completed_state_exposure() -> None:
    candidate = ExactStateObject(
        slot_id="current_candidate",
        object_id="candidate:task",
        object_version="v2",
        exact_content="new candidate",
        metadata={"candidate_sha256": "candidate-2"},
    )
    kernel = HostKernel().set_state_object(candidate).append_transcript(
        TranscriptEntry(
            "CURRENT",
            "user",
            candidate.exact_content,
            state_slot_id="current_candidate",
        )
    )

    def fail(_: Mapping[str, Any]) -> Mapping[str, Any]:
        raise TimeoutError("offline failure")

    step = make_host(config()).step(
        kernel=kernel,
        counters=RuntimeCounters(),
        provider_complete=fail,
        domain=NoResultDomain(),
    )
    failed = [event for event in step.kernel.events if event.kind is EventKind.PROVIDER_FAILED]
    completed = [event for event in step.kernel.events if event.kind is EventKind.INVOCATION_COMPLETED]
    assert len(failed) == 1
    assert completed == []
    assert failed[0].data["request_binding"]["state_slot_exposures"][0]["object_version"] == "v2"


def test_execution_manifest_and_prompt_allowance_are_configuration_authority() -> None:
    first = config(execution_manifest_sha256=MANIFEST_A)
    second = config(execution_manifest_sha256=MANIFEST_B)
    assert first.prompt_limit == first.context_window - first.response_reserve == 10_000
    snapshot = CheckpointController(first).snapshot(HostKernel(), RuntimeCounters())
    with pytest.raises(ValueError, match="configuration mismatch"):
        CheckpointController.hydrate(snapshot, second)


def test_prospective_serialized_budget_blocks_before_provider_attempt() -> None:
    calls = 0

    def should_not_run(_: Mapping[str, Any]) -> Mapping[str, Any]:
        nonlocal calls
        calls += 1
        return provider()( {})

    configuration = config(maximum_serialized_tokens=1_005)
    step = make_host(configuration).step(
        kernel=HostKernel().append_transcript(TranscriptEntry("S", "system", "1234567890")),
        counters=RuntimeCounters(serialized_tokens=1_000),
        provider_complete=should_not_run,
        domain=NoResultDomain(),
    )
    assert calls == 0
    assert step.disposition is TerminalCode.TOKEN_BUDGET_EXHAUSTED
    assert step.kernel.project().failed_calls == ()


def test_review_contains_exposure_action_provider_and_candidate_transition_evidence() -> None:
    candidate = ExactStateObject(
        slot_id="current_candidate",
        object_id="candidate:task",
        object_version="v0",
        exact_content="old\n",
        metadata={"candidate_sha256": "candidate-0"},
    )
    updated = ExactStateObject(
        slot_id="current_candidate",
        object_id="candidate:task",
        object_version="v1",
        exact_content="new\n",
        metadata={"candidate_sha256": "candidate-1"},
    )

    class MutationDomain(NoResultDomain):
        def handle(self, content: str, *, call_index: int, kernel: HostKernel) -> DomainOutcome:
            self.calls += 1
            return DomainOutcome(
                action={"action": "replace"},
                state_updates=(updated,),
            )

    kernel = HostKernel().set_state_object(candidate).append_transcript(
        TranscriptEntry("CURRENT", "user", "old\n", state_slot_id="current_candidate")
    )
    host = make_host(config())
    with tempfile.TemporaryDirectory() as temp:
        step = host.step(
            kernel=kernel,
            counters=RuntimeCounters(),
            provider_complete=provider(),
            domain=MutationDomain(),
            provider_custody_root=Path(temp) / "call-001" / "provider_attempt",
        )
        review = host.checkpoint.review_packet(step.kernel, step.counters, host.composer)
    assert review["semantic_judgment"] is None
    assert review["invocations"][0]["finish_reason"] == "stop"
    assert review["invocations"][0]["request_binding"]["state_slot_exposures"][0]["object_version"] == "v0"
    assert review["action_dispositions"][0]["status"] == "accepted"
    assert review["candidate_transitions"][0]["from_object_version"] == "v0"
    assert review["candidate_transitions"][0]["to_object_version"] == "v1"
    assert review["candidate_transitions"][0]["unified_diff"]
    assert review["provider_custody"][0]["request_path"].endswith("REQUEST.json")
    assert review["provider_usage"]["cached_tokens"] == 3


def test_second_tranche_chains_parent_and_reports_attempts_completions_failures() -> None:
    configuration = config(tranche=1, maximum_calls=4)
    host = make_host(configuration)
    domain = NoResultDomain()
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        first = run_tranche(
            host=host,
            kernel=HostKernel(),
            counters=RuntimeCounters(),
            domain=domain,
            provider_complete=provider(),
            run_root=root / "tranche-001",
        )
        first_checkpoint = json.loads(first.checkpoint_path.read_text(encoding="utf-8"))
        second = run_tranche(
            host=host,
            kernel=first.kernel,
            counters=first.counters,
            domain=domain,
            provider_complete=provider(),
            run_root=root / "tranche-002",
            parent_checkpoint_path=first.checkpoint_path,
        )
        second_checkpoint = json.loads(second.checkpoint_path.read_text(encoding="utf-8"))
        tranche_result = json.loads(
            (root / "tranche-002" / "TRANCHE_RESULT.json").read_text(encoding="utf-8")
        )
    assert second_checkpoint["parent_checkpoint_sha256"] == first_checkpoint["checkpoint_sha256"]
    assert second.provider_attempts == 1
    assert second.completed_invocations == 1
    assert second.failed_invocations == 0
    assert tranche_result["provider_attempts"] == 1
    assert tranche_result["completed_invocations"] == 1
