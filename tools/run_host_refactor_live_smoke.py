from __future__ import annotations

# ruff: noqa: E402

import argparse
import sys
import traceback
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import load_json, sha256_file, write_json
from reactive_runtime.seal import seal_tree

from host_refactor.live_path import run_tranche
from host_refactor.live_smoke import (
    EXPECTED_PENDING_RESULT_ID,
    MAXIMUM_NEW_MODEL_CALLS,
    MAXIMUM_SERIALIZED_TOKENS,
    RUN_ID,
    SCOPE,
    assert_pressure_preflight,
    build_live_smoke_system,
    live_smoke_execution_manifest,
    qualifying_disposition,
)
from tools.live_common import (
    LiveTokenizer,
    complete_custodied,
    git_commit,
    require_clean_tree,
    start_server,
    stop_server,
)
from tools.verify_runtime_assets import verify as verify_runtime_assets
from host_refactor.model import EventKind


CONTRACT = ROOT / "HOST_LIVE_SMOKE_CONTRACT.json"
SELECTED_ASSETS = {"model_gguf", "llama_server_cuda", "llama_tokenize_cpu"}


def authorize(path: Path) -> dict[str, object]:
    resolved = path.resolve()
    receipt = load_json(resolved)
    failures: list[str] = []
    if resolved.is_relative_to(ROOT.resolve()):
        failures.append("authorization_must_remain_outside_repository")
    expected: dict[str, object] = {
        "authorized": True,
        "authorized_freeze_commit": git_commit(),
        "authorized_scopes": [SCOPE],
        "authorized_run_id": RUN_ID,
        "maximum_model_calls": MAXIMUM_NEW_MODEL_CALLS,
        "maximum_serialized_tokens": MAXIMUM_SERIALIZED_TOKENS,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            failures.append(f"{key}_mismatch")
    if failures:
        raise RuntimeError(f"authorization failed: {failures}")
    return dict(receipt)


def provider_callback(run_root: Path):
    def complete(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        response = complete_custodied(
            dict(payload),
            run_root / "http_provider_attempt",
        )
        return {
            "content": response["content"],
            "finish_reason": response["finish_reason"],
            "usage": response["usage"],
        }

    return complete


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization-receipt", required=True, type=Path)
    args = parser.parse_args()
    require_clean_tree()
    authorization = authorize(args.authorization_receipt)
    run_root = ROOT / "qualification_runs" / RUN_ID
    if run_root.exists():
        raise FileExistsError(f"live-smoke run root already exists: {run_root}")
    run_root.mkdir(parents=True)
    write_json(run_root / "AUTHORIZATION_RECEIPT.json", authorization)
    manifest = live_smoke_execution_manifest(ROOT)
    write_json(
        run_root / "FREEZE_BINDING.json",
        {
            "commit": git_commit(),
            "contract_sha256": sha256_file(CONTRACT),
            "execution_manifest": manifest,
            "model_profile_lock_sha256": sha256_file(ROOT / "MODEL_PROFILE_LOCK.json"),
            "run_id": RUN_ID,
            "schema": "host-refactor-live-smoke-freeze-binding-v0",
        },
    )
    assets = verify_runtime_assets(SELECTED_ASSETS)
    write_json(run_root / "RUNTIME_ASSET_VERIFICATION.json", assets)
    if assets["passed"] is not True:
        raise RuntimeError(f"runtime assets failed: {assets['failures']}")

    process = stdout = stderr = None
    release = failure = None
    result = None
    try:
        process, stdout, stderr, runtime_gate = start_server(run_root / "model")
        tokenizer = LiveTokenizer()
        host, domain, kernel, counters = build_live_smoke_system(
            repository_root=ROOT,
            trajectory_root=run_root / "trajectory",
            count_messages=lambda messages: tokenizer.count_messages(messages)[0],
            count_text=lambda text: len(tokenizer.tokenize(text)),
        )
        assert_pressure_preflight(host, kernel)
        parent_checkpoint_path = run_root / "PARENT_CHECKPOINT.json"
        host.checkpoint.write(
            parent_checkpoint_path,
            kernel,
            counters,
            domain_state=domain.snapshot(),
        )
        tranche = run_tranche(
            host=host,
            kernel=kernel,
            counters=counters,
            domain=domain,
            provider_complete=provider_callback(run_root),
            run_root=run_root / "tranche-001",
            parent_checkpoint_path=parent_checkpoint_path,
        )
        state = tranche.kernel.project()
        pending = state.results[EXPECTED_PENDING_RESULT_ID]
        request = next(
            event.data
            for event in tranche.kernel.events
            if event.kind is EventKind.INVOCATION_COMPLETED
            and int(event.data["call_index"]) == 8
        )
        qualification_failures: list[str] = []
        if tranche.provider_attempts != 1:
            qualification_failures.append("provider_attempt_count_mismatch")
        if tranche.completed_invocations != 1:
            qualification_failures.append("completed_invocation_count_mismatch")
        if tranche.failed_invocations != 0:
            qualification_failures.append("unexpected_failed_invocation")
        if not qualifying_disposition(tranche.disposition):
            qualification_failures.append("nonqualifying_disposition")
        if pending.first_delivered_call != 8:
            qualification_failures.append("pending_result_not_delivered_on_call_8")
        if EXPECTED_PENDING_RESULT_ID not in request["included_result_ids"]:
            qualification_failures.append("pending_result_absent_from_request_binding")
        if not (run_root / "http_provider_attempt" / "response.body.bin").is_file():
            qualification_failures.append("raw_http_response_not_custodied")
        result = {
            "completed_invocations": tranche.completed_invocations,
            "disposition": tranche.disposition.value,
            "events_sha256": state.events_sha256,
            "failed_invocations": tranche.failed_invocations,
            "freeze_commit": git_commit(),
            "pending_result_first_delivered_call": pending.first_delivered_call,
            "provider_attempts": tranche.provider_attempts,
            "qualification_failures": qualification_failures,
            "qualified": not qualification_failures,
            "run_id": RUN_ID,
            "runtime_gate_passed": runtime_gate["passed"],
            "schema": "host-refactor-live-smoke-result-v0",
        }
        write_json(run_root / "LIVE_SMOKE_RESULT.json", result)
        if qualification_failures:
            raise RuntimeError(f"live smoke did not qualify: {qualification_failures}")
    except BaseException as exc:
        failure = {
            "error_message": str(exc),
            "error_type": type(exc).__name__,
            "no_retry": True,
            "traceback": traceback.format_exc(),
        }
        write_json(run_root / "RUN_FAILURE.json", failure)
        raise
    finally:
        if process is not None:
            release = stop_server(process, stdout, stderr, run_root / "model")
        write_json(
            run_root / "FINALIZATION.json",
            {"failure": failure, "release": release, "result": result},
        )
        seal_tree(run_root, run_root / "RUN_SEAL.json")
    if release is None or release.get("released") is not True:
        raise RuntimeError("runtime release did not qualify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
