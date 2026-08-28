from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping

from host_refactor.capacity import CapacityManager
from host_refactor.checkpoint import CheckpointController, RuntimeCounters
from host_refactor.kernel import HostKernel
from host_refactor.model import (
    ExactResult,
    RunConfiguration,
    TerminalCode,
    TranscriptEntry,
)
from host_refactor.packet import PacketComposer
from host_refactor.runner import DomainOutcome, HostRunner, default_payload_builder


def count_chars(messages: list[dict[str, str]]) -> int:
    return sum(len(row["content"]) for row in messages)


def configuration(*, tranche: int = 12, maximum: int = 60) -> RunConfiguration:
    return RunConfiguration(
        run_id="refactor-test",
        task_id="task-test",
        seed=42,
        prompt_limit=10_000,
        response_reserve=1_000,
        tranche_calls=tranche,
        maximum_calls=maximum,
        maximum_serialized_tokens=100_000,
    )


class NoResultDomain:
    def handle(
        self, content: str, *, call_index: int, kernel: HostKernel
    ) -> DomainOutcome:
        return DomainOutcome()


class InvalidDomain:
    def handle(
        self, content: str, *, call_index: int, kernel: HostKernel
    ) -> DomainOutcome:
        raise ValueError("invalid action")


class ConstantResultDomain:
    def __init__(self) -> None:
        self.next_result = 1

    def handle(
        self, content: str, *, call_index: int, kernel: HostKernel
    ) -> DomainOutcome:
        result_id = f"RESULT-{self.next_result:03d}"
        self.next_result += 1
        return DomainOutcome(
            result=ExactResult(
                result_id=result_id,
                result_kind="source_observation",
                object_id="SOURCE-A:1-2",
                object_version="v1",
                exact_content=f"wrapper {result_id}\n--- exact result body ---\nalpha",
                payload_content="alpha",
                acquired_call=call_index,
                candidate_sha256_after="candidate-0",
                span_key="SOURCE-A:1-2",
            )
        )


def runner(config: RunConfiguration) -> HostRunner:
    composer = PacketComposer()
    return HostRunner(
        configuration=config,
        composer=composer,
        capacity=CapacityManager(
            composer=composer,
            count_messages=count_chars,
            prompt_limit=config.prompt_limit,
        ),
        checkpoint=CheckpointController(config),
        payload_builder=default_payload_builder,
    )


def success(_: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "content": "{}",
        "finish_reason": "stop",
        "usage": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11},
    }


class CheckpointAndRunnerTests(unittest.TestCase):
    def test_twelve_call_checkpoint_hydrates_identical_next_packet(self) -> None:
        config = configuration()
        kernel = HostKernel().append_transcript(
            TranscriptEntry("SYSTEM", "system", "s")
        )
        counters = RuntimeCounters()
        host = runner(config)
        for _ in range(12):
            step = host.step(
                kernel=kernel,
                counters=counters,
                provider_complete=success,
                domain=NoResultDomain(),
            )
            kernel, counters = step.kernel, step.counters
        self.assertEqual(step.disposition, TerminalCode.CHECKPOINT_PAUSE)
        before = host.composer.compose(kernel).canonical_bytes
        controller = CheckpointController(config)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "checkpoint.json"
            written = controller.write(path, kernel, counters)
            hydrated, hydrated_counters = controller.read(path, config)
        self.assertEqual(hydrated_counters, counters)
        self.assertEqual(host.composer.compose(hydrated).canonical_bytes, before)
        self.assertEqual(
            written["checkpoint_sha256"],
            controller.snapshot(kernel, counters)["checkpoint_sha256"],
        )
        review = controller.review_packet(hydrated, hydrated_counters, host.composer)
        self.assertIsNone(review["semantic_judgment"])
        self.assertEqual(len(review["completed_actor_calls"]), 12)

    def test_resumed_call_thirteen_matches_uninterrupted_provider_free_path(
        self,
    ) -> None:
        config = configuration()
        host = runner(config)
        kernel = HostKernel().append_transcript(
            TranscriptEntry("SYSTEM", "system", "s")
        )
        counters = RuntimeCounters()
        for _ in range(12):
            step = host.step(
                kernel=kernel,
                counters=counters,
                provider_complete=success,
                domain=NoResultDomain(),
            )
            kernel, counters = step.kernel, step.counters
        snapshot = CheckpointController(config).snapshot(kernel, counters)
        resumed_kernel, resumed_counters = CheckpointController.hydrate(
            snapshot, config
        )
        uninterrupted = host.step(
            kernel=kernel,
            counters=counters,
            provider_complete=success,
            domain=NoResultDomain(),
        )
        resumed = host.step(
            kernel=resumed_kernel,
            counters=resumed_counters,
            provider_complete=success,
            domain=NoResultDomain(),
        )
        self.assertEqual(resumed.kernel.as_dict(), uninterrupted.kernel.as_dict())
        self.assertEqual(resumed.counters, uninterrupted.counters)
        self.assertEqual(
            host.composer.compose(resumed.kernel).canonical_bytes,
            host.composer.compose(uninterrupted.kernel).canonical_bytes,
        )

    def test_provider_failure_is_one_attempt_and_distinct(self) -> None:
        attempts = 0

        def fail(_: Mapping[str, Any]) -> Mapping[str, Any]:
            nonlocal attempts
            attempts += 1
            raise TimeoutError("timeout")

        with tempfile.TemporaryDirectory() as temp:
            custody = Path(temp) / "provider"
            step = runner(configuration()).step(
                kernel=HostKernel(),
                counters=RuntimeCounters(),
                provider_complete=fail,
                domain=NoResultDomain(),
                provider_custody_root=custody,
            )
            self.assertTrue((custody / "REQUEST.json").is_file())
            self.assertTrue((custody / "FAILURE.json").is_file())
            self.assertTrue((custody / "ATTEMPT.json").is_file())
            self.assertFalse((custody / "RESPONSE.json").exists())
        self.assertEqual(attempts, 1)
        self.assertEqual(step.provider_attempts, 1)
        self.assertEqual(step.disposition, TerminalCode.PROVIDER_FAILURE)
        self.assertEqual(step.kernel.project().terminal, TerminalCode.PROVIDER_FAILURE)

    def test_invalid_action_is_not_provider_failure(self) -> None:
        step = runner(configuration()).step(
            kernel=HostKernel(),
            counters=RuntimeCounters(),
            provider_complete=success,
            domain=InvalidDomain(),
        )
        self.assertEqual(step.disposition, TerminalCode.INVALID_ACTION)
        self.assertEqual(step.kernel.project().terminal, TerminalCode.INVALID_ACTION)

    def test_runner_deduplicates_repeated_resident_acquisition(self) -> None:
        host = runner(configuration(tranche=10, maximum=20))
        kernel = HostKernel()
        counters = RuntimeCounters()
        domain = ConstantResultDomain()
        first = host.step(
            kernel=kernel,
            counters=counters,
            provider_complete=success,
            domain=domain,
        )
        second = host.step(
            kernel=first.kernel,
            counters=first.counters,
            provider_complete=success,
            domain=domain,
        )
        state = second.kernel.project()
        self.assertIn("RESULT-001", state.results)
        self.assertNotIn("RESULT-002", state.results)
        self.assertEqual(state.results["RESULT-001"].demand_count, 2)
        packet = host.composer.compose(second.kernel)
        self.assertEqual(
            "\n".join(message["content"] for message in packet.messages).count(
                "--- exact result body ---\nalpha"
            ),
            1,
        )

    def test_capacity_and_budget_terminals_are_distinct(self) -> None:
        tiny = configuration(tranche=1, maximum=1)
        exhausted = runner(tiny).step(
            kernel=HostKernel(),
            counters=RuntimeCounters(),
            provider_complete=success,
            domain=NoResultDomain(),
        )
        self.assertEqual(exhausted.disposition, TerminalCode.CALL_BUDGET_EXHAUSTED)
        self.assertEqual(
            exhausted.kernel.project().terminal,
            TerminalCode.CALL_BUDGET_EXHAUSTED,
        )

        config = configuration()
        composer = PacketComposer()
        blocked_host = HostRunner(
            configuration=config,
            composer=composer,
            capacity=CapacityManager(
                composer=composer,
                count_messages=count_chars,
                prompt_limit=1,
            ),
            checkpoint=CheckpointController(config),
            payload_builder=default_payload_builder,
        )
        blocked = blocked_host.step(
            kernel=HostKernel().append_transcript(
                TranscriptEntry("SYSTEM", "system", "too large")
            ),
            counters=RuntimeCounters(),
            provider_complete=success,
            domain=NoResultDomain(),
        )
        self.assertEqual(blocked.disposition, TerminalCode.CAPACITY_BLOCKED)
        self.assertEqual(
            blocked.kernel.project().terminal,
            TerminalCode.CAPACITY_BLOCKED,
        )
        self.assertNotEqual(blocked.disposition, exhausted.disposition)


if __name__ == "__main__":
    unittest.main()
