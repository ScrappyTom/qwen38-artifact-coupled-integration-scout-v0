from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Mapping

from host_refactor.checkpoint import RuntimeCounters
from host_refactor.lifecycle_scout.fixtures import NoOpMaintenanceFixture
from host_refactor.lifecycle_scout.migration import migrate_e96_donor
from host_refactor.model import EventKind
from tools.offline_tokenizer import OfflineTokenizer


ROOT = Path(__file__).resolve().parents[1]
SEALED_RUN = (
    ROOT
    / "qualification_runs"
    / "2026-08-29-trellis-e97-verification-lifecycle-scout-v0"
    / "tranche-001"
)


def response(call_index: int) -> dict[str, Any]:
    return json.loads(
        (
            SEALED_RUN
            / f"call-{call_index:03d}"
            / "actor"
            / "RESPONSE.json"
        ).read_text(encoding="utf-8")
    )


class SealedResponseReplay:
    def __init__(self, tokenizer: OfflineTokenizer) -> None:
        self.tokenizer = tokenizer
        self.call_index = 19

    def __call__(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        row = response(self.call_index)
        self.call_index += 1
        content = str(row["content"])
        messages = payload.get("messages")
        if not isinstance(messages, list):
            raise ValueError("replay payload lacks messages")
        prompt_tokens = self.tokenizer.count_messages(messages)
        completion_tokens = self.tokenizer.count_text(content)
        return {
            "content": content,
            "finish_reason": str(row["finish_reason"]),
            "usage": {
                "completion_tokens": completion_tokens,
                "prompt_tokens": prompt_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }


def test_sealed_e98_sequence_now_has_phase_guidance_and_bounded_rejections() -> None:
    tokenizer = OfflineTokenizer()
    with tempfile.TemporaryDirectory() as temp:
        migration = migrate_e96_donor(
            repository_root=ROOT,
            trajectory_root=Path(temp) / "trajectory",
            count_messages=tokenizer.count_messages,
            count_text=tokenizer.count_text,
            maintenance_complete=NoOpMaintenanceFixture(),
        )
        kernel = migration.kernel
        counters = RuntimeCounters(
            serialized_tokens=migration.counters.serialized_tokens,
            provider_attempts=migration.counters.provider_attempts,
        )
        replay = SealedResponseReplay(tokenizer)
        for _ in range(4):
            step = migration.orchestrator.step(
                kernel=kernel,
                counters=counters,
                actor_complete=replay,
            )
            kernel = step.runner_step.kernel
            counters = step.runner_step.counters
            assert step.runner_step.disposition is None

    state = kernel.project()
    assert "current_action_contract" in state.state_slots
    contract = state.state_slots["current_action_contract"].exact_content
    assert '"action":"run_check"' in contract
    assert "Run a current candidate-bound check before repair" in contract
    receipts = [
        row
        for row in state.transcript
        if row.entry_kind == "rejected_assistant_response_receipt"
    ]
    assert len(receipts) == 2
    assert sum(
        event.kind is EventKind.REJECTED_RESPONSE_EXTERNALIZED
        for event in kernel.events
    ) == 2
    packet = migration.host.composer.compose(kernel)
    packet_text = "\n".join(row["content"] for row in packet.messages)
    assert response(21)["content"] not in packet_text
    assert response(22)["content"] not in packet_text
    prompt_tokens = tokenizer.count_messages(packet.message_list())
    assert prompt_tokens <= migration.host.configuration.prompt_limit
