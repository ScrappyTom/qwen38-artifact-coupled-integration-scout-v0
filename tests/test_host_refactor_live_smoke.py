from __future__ import annotations

import json
import tempfile
from pathlib import Path

from host_refactor.live_path import run_tranche
from host_refactor.live_smoke import (
    EXPECTED_LIVE_RELIEF_TOKENS,
    EXPECTED_PENDING_RESULT_ID,
    EXPECTED_RELIEF_RESULT_IDS,
    EXPECTED_RELIEF_TOKENS,
    assert_pressure_preflight,
    build_live_smoke_system,
    live_smoke_execution_manifest,
    qualifying_disposition,
    RUN_ID,
    SCOPE,
)
from host_refactor.model import DeliveryState
from tools.offline_tokenizer import OfflineTokenizer


ROOT = Path(__file__).resolve().parents[1]


def provider_response(payload):
    return {
        "content": json.dumps(
            {
                "action": "read_batch",
                "requests": [
                    {"source_id": "TRANSIT", "start_line": 61, "end_line": 94},
                    {"source_id": "COMMS", "start_line": 61, "end_line": 94},
                ],
            },
            separators=(",", ":"),
        ),
        "finish_reason": "stop",
        "usage": {
            "completion_tokens": 40,
            "prompt_tokens": EXPECTED_RELIEF_TOKENS,
            "total_tokens": EXPECTED_RELIEF_TOKENS + 40,
        },
    }


def test_live_smoke_manifest_binds_runner_contract_and_base_host() -> None:
    manifest = live_smoke_execution_manifest(ROOT)
    assert manifest["schema"] == "host-refactor-live-smoke-execution-manifest-v0"
    assert "HOST_LIVE_SMOKE_CONTRACT.json" in manifest["files"]
    assert "tools/run_host_refactor_live_smoke.py" in manifest["files"]
    assert len(str(manifest["execution_manifest_sha256"])) == 64
    assert RUN_ID == "2026-08-28-host-refactor-live-smoke-v2"
    assert SCOPE == "host_refactor_live_smoke_v2"
    assert EXPECTED_RELIEF_TOKENS == 18_785
    assert EXPECTED_LIVE_RELIEF_TOKENS == 18_786


def test_v2_result_records_qualified_single_call_checkpoint() -> None:
    result = json.loads(
        (ROOT / "HOST_LIVE_SMOKE_V2_RESULT.json").read_text(encoding="utf-8")
    )
    assert result["apparatus_commit"] == "3afd9e269abb437512ea961772b43f4a12ea0f30"
    assert result["run_id"] == "2026-08-28-host-refactor-live-smoke-v2"
    assert result["qualified"] is True
    assert result["model_calls"] == 1
    assert result["provider_attempts"] == 1
    assert result["retries"] == 0
    assert result["live_prompt_tokens"] == EXPECTED_LIVE_RELIEF_TOKENS
    assert result["pending_result_first_delivered_call"] == 8
    assert result["next_pending_result_id"] == "RESULT-008"
    assert result["candidate_changed"] is False
    assert result["runtime_released"] is True


def test_one_call_smoke_crosses_pressure_delivery_action_and_checkpoint() -> None:
    tokenizer = OfflineTokenizer()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        host, domain, kernel, counters = build_live_smoke_system(
            repository_root=ROOT,
            trajectory_root=root / "trajectory",
            count_messages=tokenizer.count_messages,
            count_text=tokenizer.count_text,
        )
        assert_pressure_preflight(host, kernel)
        parent_checkpoint = root / "PARENT_CHECKPOINT.json"
        host.checkpoint.write(
            parent_checkpoint,
            kernel,
            counters,
            domain_state=domain.snapshot(),
        )
        result = run_tranche(
            host=host,
            kernel=kernel,
            counters=counters,
            domain=domain,
            provider_complete=provider_response,
            run_root=root / "tranche",
            parent_checkpoint_path=parent_checkpoint,
        )
        state = result.kernel.project()
        assert result.provider_attempts == 1
        assert result.completed_invocations == 1
        assert result.failed_invocations == 0
        assert qualifying_disposition(result.disposition)
        assert state.results["RESULT-001"].delivery_state is DeliveryState.DELIVERED_EXTERNAL
        assert state.results[EXPECTED_PENDING_RESULT_ID].first_delivered_call == 8
        assert state.results["RESULT-008"].delivery_state is DeliveryState.PENDING
        assert result.checkpoint_path.is_file()
        assert result.review_path.is_file()
        step = json.loads(
            (root / "tranche" / "actor" / "call-008" / "HOST_STEP.json").read_text(
                encoding="utf-8"
            )
        )
        assert step["selected_relief_result_ids"] == list(EXPECTED_RELIEF_RESULT_IDS)
        assert step["prompt_tokens"] == EXPECTED_RELIEF_TOKENS
