from __future__ import annotations

# ruff: noqa: E402

import argparse
import json
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from host_refactor.model import TerminalCode
from host_refactor.whole_lifecycle.readiness import adjudicate_readiness
from host_refactor.whole_lifecycle.resume import hydrate_checkpoint
from host_refactor.whole_lifecycle.system import (
    CONFIGURATION_LABEL,
    execution_manifest,
)
from interaction_scout.live_path import run_interaction_tranche
from reactive_runtime.canonical import (
    canonical_json_bytes,
    load_json,
    sha256_bytes,
    sha256_file,
    write_json,
)
from reactive_runtime.seal import seal_tree, verify_tree_seal
from tools.live_common import (
    LiveTokenizer,
    complete_custodied,
    git_commit,
    require_clean_tree,
    start_server,
    stop_server,
)
from tools.verify_runtime_assets import verify as verify_runtime_assets


RUN_ID = "2026-08-30-trellis-clean-whole-lifecycle-continuation-v0"
SCOPE = "trellis_clean_whole_lifecycle_continuation_v0"
PARENT_RUN_ID = "2026-08-30-trellis-clean-whole-lifecycle-v0"
PARENT_RESULT_COMMIT = "fa67aecdf833b72f282a03819a3fbc35e263c320"
MAXIMUM_ACTOR_CALLS = 12
MAXIMUM_MAINTENANCE_CALLS = 6
MAXIMUM_PROVIDER_CALLS = 18
MAXIMUM_SERIALIZED_TOKENS = 400_000
CONTRACT = ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CONTINUATION_CONTRACT.json"
REQUEST = ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CONTINUATION_AUTHORIZATION_REQUEST.json"
STAGE0 = ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CONTINUATION_STAGE0.json"
PARENT_ROOT = ROOT / "qualification_runs" / PARENT_RUN_ID
PARENT_CHECKPOINT = PARENT_ROOT / "tranche-001" / "CHECKPOINT.json"
SELECTED_ASSETS = {"model_gguf", "llama_server_cuda", "llama_tokenize_cpu"}


class HttpProvider:
    def __init__(self, root: Path, label: str) -> None:
        self.root = root
        self.label = label
        self.calls = 0

    def __call__(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls += 1
        response = complete_custodied(
            dict(payload),
            self.root / self.label / f"call-{self.calls:03d}",
        )
        return {
            "content": response["content"],
            "finish_reason": response["finish_reason"],
            "usage": response["usage"],
        }


def continuation_execution_manifest() -> dict[str, Any]:
    base = execution_manifest(ROOT)
    declared = (
        CONTRACT,
        REQUEST,
        ROOT / "host_refactor" / "whole_lifecycle" / "resume.py",
        ROOT / "tools" / "build_e107_clean_whole_lifecycle_continuation_stage0.py",
        ROOT / "tools" / "run_e107_clean_whole_lifecycle_continuation.py",
        ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CHECKPOINT_RESULT.json",
        PARENT_ROOT / "TRANCHE_RESULT.json",
        PARENT_ROOT / "RUN_SEAL.json",
        PARENT_CHECKPOINT,
    )
    payload = {
        "base_execution_manifest_sha256": base["execution_manifest_sha256"],
        "files": {
            path.relative_to(ROOT).as_posix(): sha256_file(path)
            for path in sorted(declared)
        },
        "parent_result_commit": PARENT_RESULT_COMMIT,
        "schema": "trellis-clean-whole-lifecycle-continuation-manifest-v0",
    }
    return {
        **payload,
        "execution_manifest_sha256": sha256_bytes(canonical_json_bytes(payload)),
    }


def authorize(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    receipt = load_json(resolved)
    request = load_json(REQUEST)
    expected = {
        "authorized": True,
        "authorized_freeze_commit": git_commit(),
        "authorized_scopes": [SCOPE],
        "authorized_run_id": RUN_ID,
        "configuration": CONFIGURATION_LABEL,
        "maximum_actor_calls": MAXIMUM_ACTOR_CALLS,
        "maximum_maintenance_calls": MAXIMUM_MAINTENANCE_CALLS,
        "maximum_provider_calls": MAXIMUM_PROVIDER_CALLS,
        "maximum_serialized_tokens": MAXIMUM_SERIALIZED_TOKENS,
        "attempts_per_call": 1,
        "retries": 0,
        "authorization_text": str(request["expected_user_quote_template"]).replace(
            "{commit}", git_commit()
        ),
    }
    failures: list[str] = []
    if resolved.is_relative_to(ROOT.resolve()):
        failures.append("authorization_must_remain_outside_repository")
    for key, value in expected.items():
        if receipt.get(key) != value:
            failures.append(f"{key}_mismatch")
    if failures:
        raise RuntimeError(f"authorization failed: {failures}")
    return dict(receipt)


def external_evaluation(candidate_root: Path, output_path: Path) -> dict[str, Any]:
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "task_trellis" / "evaluator" / "evaluate.py"),
            str(candidate_root),
        ],
        cwd=ROOT / "task_trellis",
        capture_output=True,
        check=False,
        timeout=180,
    )
    value = json.loads(process.stdout)
    if not isinstance(value, dict):
        raise RuntimeError("external evaluator did not return an object")
    receipt = {
        "actor_visible": False,
        "candidate_sha256": value.get("candidate_sha256"),
        "evaluation": value,
        "returncode": process.returncode,
        "schema": "trellis-clean-lifecycle-continuation-evaluation-v0",
        "stderr_utf8": process.stderr.decode("utf-8", errors="replace"),
    }
    write_json(output_path, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization-receipt", required=True, type=Path)
    args = parser.parse_args()
    require_clean_tree()
    stage0 = load_json(STAGE0)
    if stage0.get("passed") is not True or stage0.get("live_authorized") is not False:
        raise RuntimeError("frozen continuation Stage 0 is not qualified and unauthorized")
    authorization = authorize(args.authorization_receipt)
    seal_errors = verify_tree_seal(PARENT_ROOT, PARENT_ROOT / "RUN_SEAL.json")
    if seal_errors:
        raise RuntimeError(f"parent run seal failed: {seal_errors}")
    run_root = ROOT / "qualification_runs" / RUN_ID
    if run_root.exists():
        raise FileExistsError(f"continuation run root already exists: {run_root}")
    run_root.mkdir(parents=True)
    write_json(run_root / "AUTHORIZATION_RECEIPT.json", authorization)
    write_json(
        run_root / "FREEZE_BINDING.json",
        {
            "authorization_request_sha256": sha256_file(REQUEST),
            "commit": git_commit(),
            "contract_sha256": sha256_file(CONTRACT),
            "execution_manifest": continuation_execution_manifest(),
            "model_profile_lock_sha256": sha256_file(ROOT / "MODEL_PROFILE_LOCK.json"),
            "parent_checkpoint_sha256": sha256_file(PARENT_CHECKPOINT),
            "parent_result_commit": PARENT_RESULT_COMMIT,
            "parent_run_seal_sha256": sha256_file(PARENT_ROOT / "RUN_SEAL.json"),
            "run_id": RUN_ID,
            "schema": "trellis-clean-whole-lifecycle-continuation-freeze-binding-v0",
            "stage0_sha256": sha256_file(STAGE0),
        },
    )
    assets = verify_runtime_assets(SELECTED_ASSETS)
    write_json(run_root / "RUNTIME_ASSET_VERIFICATION.json", assets)
    if assets["passed"] is not True:
        raise RuntimeError(f"runtime assets failed: {assets['failures']}")

    process = stdout = stderr = None
    release = None
    failure: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    try:
        process, stdout, stderr, runtime_gate = start_server(run_root / "model")
        tokenizer = LiveTokenizer()
        maintenance_http = HttpProvider(run_root / "http", "maintenance")
        orchestrator, adapter, kernel, counters = hydrate_checkpoint(
            repository_root=ROOT,
            checkpoint_path=PARENT_CHECKPOINT,
            trajectory_root=run_root / "trajectory",
            count_messages=lambda messages: tokenizer.count_messages(messages)[0],
            count_text=lambda text: len(tokenizer.tokenize(text)),
            maintenance_complete=maintenance_http,
        )
        starting_provider = counters.provider_attempts
        starting_tokens = counters.serialized_tokens
        actor_http = HttpProvider(run_root / "http", "actor")
        tranche = run_interaction_tranche(
            orchestrator=orchestrator,
            kernel=kernel,
            counters=counters,
            actor_complete=actor_http,
            run_root=run_root / "tranche-002",
            parent_checkpoint_path=PARENT_CHECKPOINT,
        )
        evaluation = external_evaluation(
            adapter.world.candidate_root,
            run_root / "EXTERNAL_CHECKPOINT_EVALUATION.json",
        )
        readiness = adjudicate_readiness(
            ROOT,
            evaluation["evaluation"],
            current_candidate_sha256=adapter.world.candidate_sha256,
        )
        write_json(run_root / "EXTERNAL_READINESS_ADJUDICATION.json", readiness)
        allowed = {
            TerminalCode.CHECKPOINT_PAUSE,
            TerminalCode.COMPLETED,
            TerminalCode.CAPACITY_BLOCKED,
            TerminalCode.CALL_BUDGET_EXHAUSTED,
            TerminalCode.TOKEN_BUDGET_EXHAUSTED,
        }
        if tranche.disposition not in allowed:
            raise RuntimeError(
                f"nonqualifying tranche disposition: {tranche.disposition.value}"
            )
        additional_provider = tranche.counters.provider_attempts - starting_provider
        additional_tokens = tranche.counters.serialized_tokens - starting_tokens
        if tranche.actor_attempts > MAXIMUM_ACTOR_CALLS:
            raise RuntimeError("additional actor call authorization exceeded")
        if tranche.maintenance_attempts > MAXIMUM_MAINTENANCE_CALLS:
            raise RuntimeError("additional maintenance call authorization exceeded")
        if additional_provider > MAXIMUM_PROVIDER_CALLS:
            raise RuntimeError("additional provider call authorization exceeded")
        if additional_tokens > MAXIMUM_SERIALIZED_TOKENS:
            raise RuntimeError("additional serialized token authorization exceeded")
        result = {
            "additional_actor_calls": tranche.actor_attempts,
            "additional_maintenance_calls": tranche.maintenance_attempts,
            "additional_provider_calls": additional_provider,
            "additional_serialized_tokens": additional_tokens,
            "automatic_continuation": False,
            "candidate_sha256": adapter.world.candidate_sha256,
            "configuration": CONFIGURATION_LABEL,
            "cumulative_actor_calls": len(tranche.kernel.project().completed_calls),
            "cumulative_maintenance_calls": tranche.lifecycle.maintenance_calls,
            "cumulative_provider_calls": tranche.counters.provider_attempts,
            "cumulative_serialized_tokens": tranche.counters.serialized_tokens,
            "disposition": tranche.disposition.value,
            "evaluation": evaluation["evaluation"],
            "freeze_commit": git_commit(),
            "parent_result_commit": PARENT_RESULT_COMMIT,
            "readiness": readiness,
            "run_id": RUN_ID,
            "runtime_gate_passed": runtime_gate["passed"],
            "schema": "trellis-clean-whole-lifecycle-continuation-result-v0",
        }
        write_json(run_root / "CONTINUATION_RESULT.json", result)
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
        if process is not None and (
            release is None or release.get("released") is not True
        ):
            raise RuntimeError("runtime release failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
