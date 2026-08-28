from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Mapping

from host_refactor.capacity import CapacityManager
from host_refactor.checkpoint import CheckpointController, RuntimeCounters
from host_refactor.kernel import HostKernel
from host_refactor.live_path import run_tranche
from host_refactor.model import RunConfiguration, TerminalCode, TranscriptEntry
from host_refactor.packet import PacketComposer
from host_refactor.runner import DomainOutcome, HostRunner, default_payload_builder


class Domain:
    def __init__(self) -> None:
        self.calls = 0

    def handle(
        self, content: str, *, call_index: int, kernel: HostKernel
    ) -> DomainOutcome:
        self.calls += 1
        return DomainOutcome()

    def snapshot(self) -> Mapping[str, Any]:
        return {"calls": self.calls, "schema": "test-domain-v0"}


def count(messages: list[dict[str, str]]) -> int:
    return sum(len(row["content"]) for row in messages)


def complete(_: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "content": "{}",
        "finish_reason": "stop",
        "usage": {"completion_tokens": 1, "prompt_tokens": 9, "total_tokens": 10},
    }


def test_live_style_tranche_pauses_writes_custody_and_remains_resumable() -> None:
    config = RunConfiguration(
        run_id="live-style-test",
        task_id="task",
        seed=42,
        context_window=11_000,
        response_reserve=1_000,
        execution_manifest_sha256="a" * 64,
        tranche_calls=2,
        maximum_calls=6,
        maximum_serialized_tokens=10_000,
    )
    composer = PacketComposer()
    host = HostRunner(
        configuration=config,
        composer=composer,
        capacity=CapacityManager(
            composer=composer,
            count_messages=count,
            prompt_limit=config.prompt_limit,
        ),
        checkpoint=CheckpointController(config),
        payload_builder=default_payload_builder,
    )
    kernel = HostKernel().append_transcript(
        TranscriptEntry("SYSTEM", "system", "system")
    )
    domain = Domain()
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "run"
        result = run_tranche(
            host=host,
            kernel=kernel,
            counters=RuntimeCounters(),
            domain=domain,
            provider_complete=complete,
            run_root=root,
        )
        self_files = (
            root / "actor" / "call-001" / "provider_attempt" / "REQUEST.json",
            root / "actor" / "call-001" / "provider_attempt" / "RESPONSE.json",
            root / "actor" / "call-002" / "provider_attempt" / "ATTEMPT.json",
            root / "CHECKPOINT.json",
            root / "MECHANICAL_REVIEW.json",
            root / "TRANCHE_RESULT.json",
        )
        assert all(path.is_file() for path in self_files)
        resumed_kernel, resumed_counters, domain_state = (
            CheckpointController.hydrate_with_domain(
                json.loads(result.checkpoint_path.read_text(encoding="utf-8")),
                config,
            )
        )
    assert result.disposition is TerminalCode.CHECKPOINT_PAUSE
    assert result.provider_attempts == 2
    assert result.completed_invocations == 2
    assert result.failed_invocations == 0
    assert resumed_kernel.as_dict() == result.kernel.as_dict()
    assert resumed_counters == result.counters
    assert domain_state == {"calls": 2, "schema": "test-domain-v0"}
    assert result.kernel.project().terminal is None
