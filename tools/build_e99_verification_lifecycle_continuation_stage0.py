from __future__ import annotations

# ruff: noqa: E402

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from host_refactor.lifecycle_scout.fixtures import NoOpMaintenanceFixture
from host_refactor.lifecycle_scout_v1.continuation import hydrate_checkpoint
from host_refactor.model import EventKind
from reactive_runtime.canonical import (
    canonical_json_text,
    load_json,
    sha256_file,
    write_json,
)
from reactive_runtime.seal import verify_tree_seal
from tools.offline_tokenizer import OfflineTokenizer


PARENT_ROOT = (
    ROOT
    / "qualification_runs"
    / "2026-08-29-trellis-e99-verification-lifecycle-scout-v1"
)
PARENT_CHECKPOINT = PARENT_ROOT / "tranche-001" / "CHECKPOINT.json"
PARENT_RESULT = PARENT_ROOT / "LIFECYCLE_SCOUT_RESULT.json"
CONTRACT = ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_CONTINUATION_CONTRACT.json"
REQUEST = (
    ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_CONTINUATION_AUTHORIZATION_REQUEST.json"
)
OUTPUT = ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_CONTINUATION_STAGE0.json"


class CheckpointProbeActor:
    """One provider-free current-check action; transport proof, not a policy claim."""

    def __init__(self, tokenizer: OfflineTokenizer) -> None:
        self.tokenizer = tokenizer

    def __call__(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        messages = payload.get("messages")
        if not isinstance(messages, list):
            raise ValueError("probe payload lacks messages")
        response_format = json.dumps(payload.get("response_format"), sort_keys=True)
        readable = "\n".join(
            str(row.get("content", "")) for row in messages if isinstance(row, Mapping)
        )
        if '"run_check"' not in response_format:
            raise ValueError("run_check absent from response schema")
        if '"action":"run_check"' not in readable:
            raise ValueError("run_check absent from readable verification contract")
        content = canonical_json_text({"action": "run_check"})
        prompt_tokens = self.tokenizer.count_messages(messages)
        completion_tokens = self.tokenizer.count_text(content)
        return {
            "content": content,
            "finish_reason": "stop",
            "usage": {
                "completion_tokens": completion_tokens,
                "prompt_tokens": prompt_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }


def build() -> dict[str, Any]:
    tokenizer = OfflineTokenizer()
    failures: list[str] = []
    seal_errors = verify_tree_seal(PARENT_ROOT, PARENT_ROOT / "RUN_SEAL.json")
    parent_result = load_json(PARENT_RESULT)
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        orchestrator, adapter, kernel, counters = hydrate_checkpoint(
            repository_root=ROOT,
            checkpoint_path=PARENT_CHECKPOINT,
            trajectory_root=temp_root / "trajectory",
            count_messages=tokenizer.count_messages,
            count_text=tokenizer.count_text,
            maintenance_complete=NoOpMaintenanceFixture(),
        )
        before_candidate = adapter.world.candidate_sha256
        before_provider = counters.provider_attempts
        before_tokens = counters.serialized_tokens
        step = orchestrator.step(
            kernel=kernel,
            counters=counters,
            actor_complete=CheckpointProbeActor(tokenizer),
        )
        invocation = next(
            event
            for event in reversed(step.runner_step.kernel.events)
            if event.kind is EventKind.INVOCATION_COMPLETED
        )
        action = next(
            event
            for event in reversed(step.runner_step.kernel.events)
            if event.kind is EventKind.ACTION_DISPOSITION
        )
        included = list(
            invocation.data.get("request_binding", {}).get("included_result_ids", [])
        )
        if seal_errors:
            failures.append("parent_seal_failed")
        if parent_result.get("disposition") != "checkpoint_pause":
            failures.append("parent_not_checkpoint_pause")
        if parent_result.get("candidate_sha256") != before_candidate:
            failures.append("parent_candidate_mismatch")
        if "RESULT-024" not in included:
            failures.append("pending_current_check_not_delivered")
        if action.data.get("status") != "accepted":
            failures.append("provider_free_probe_action_rejected")
        if action.data.get("action", {}).get("action") != "run_check":
            failures.append("provider_free_probe_action_changed")
        if adapter.world.candidate_sha256 != before_candidate:
            failures.append("provider_free_probe_mutated_candidate")
        if step.runner_step.capacity.feasible is not True:
            failures.append("provider_free_probe_packet_infeasible")
        result = {
            "schema": "trellis-e99-verification-lifecycle-continuation-stage0-v1",
            "passed": not failures,
            "failures": failures,
            "parent": {
                "run_id": parent_result["run_id"],
                "checkpoint_sha256": load_json(PARENT_CHECKPOINT)["checkpoint_sha256"],
                "run_seal_sha256": sha256_file(PARENT_ROOT / "RUN_SEAL.json"),
                "candidate_sha256": before_candidate,
                "cumulative_provider_calls": before_provider,
                "cumulative_serialized_tokens": before_tokens,
            },
            "probe": {
                "action": "run_check",
                "accepted": action.data.get("status") == "accepted",
                "included_result_ids": included,
                "prompt_tokens": step.runner_step.capacity.prompt_tokens,
                "prompt_limit": orchestrator.host.configuration.prompt_limit,
                "selected_relief_result_ids": list(
                    step.runner_step.capacity.selected_result_ids
                ),
                "candidate_unchanged": adapter.world.candidate_sha256
                == before_candidate,
                "provider_calls": step.runner_step.counters.provider_attempts
                - before_provider,
                "serialized_tokens": step.runner_step.counters.serialized_tokens
                - before_tokens,
            },
            "contract_sha256": sha256_file(CONTRACT),
            "request_sha256": sha256_file(REQUEST),
            "gpu_provider_calls": 0,
            "live_authorized": False,
        }
    return result


def main() -> int:
    value = build()
    write_json(OUTPUT, value)
    if not value["passed"]:
        raise RuntimeError(f"continuation Stage 0 failed: {value['failures']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
