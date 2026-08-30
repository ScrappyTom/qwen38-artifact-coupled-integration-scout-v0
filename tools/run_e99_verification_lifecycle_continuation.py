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

from host_refactor.lifecycle_scout_v1.continuation import hydrate_checkpoint
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


RUN_ID = "2026-08-30-trellis-e99-verification-lifecycle-continuation-v1"
SCOPE = "trellis_e99_verification_lifecycle_continuation_v1"
CONFIGURATION = "V1_E97_REPAIRED_DONOR_DERIVED_LIFECYCLE"
MAXIMUM_ACTOR_CALLS = 6
MAXIMUM_MAINTENANCE_CALLS = 1
MAXIMUM_PROVIDER_CALLS = 7
MAXIMUM_SERIALIZED_TOKENS = 338_802
PARENT_ROOT = (
    ROOT
    / "qualification_runs"
    / "2026-08-29-trellis-e99-verification-lifecycle-scout-v1"
)
PARENT_CHECKPOINT = PARENT_ROOT / "tranche-001" / "CHECKPOINT.json"
CONTRACT = ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_CONTINUATION_CONTRACT.json"
REQUEST = (
    ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_CONTINUATION_AUTHORIZATION_REQUEST.json"
)
STAGE0 = ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_CONTINUATION_STAGE0.json"
READINESS = ROOT / "TRELLIS_E97_DONOR_READINESS_ADJUDICATION.json"
SELECTED_ASSETS = {"model_gguf", "llama_server_cuda", "llama_tokenize_cpu"}


def execution_manifest() -> dict[str, Any]:
    declared = (
        CONTRACT,
        REQUEST,
        STAGE0,
        ROOT / "MODEL_PROFILE_LOCK.json",
        ROOT / "RUNTIME_ASSET_MANIFEST.json",
        ROOT / "host_refactor" / "lifecycle_scout_v1" / "continuation.py",
        ROOT / "host_refactor" / "lifecycle_scout_v1" / "system.py",
        ROOT / "interaction_scout" / "live_path.py",
        ROOT / "tools" / "run_e99_verification_lifecycle_continuation.py",
    )
    payload = {
        "files": {
            path.relative_to(ROOT).as_posix(): sha256_file(path)
            for path in sorted(declared)
        },
        "parent_checkpoint_sha256": load_json(PARENT_CHECKPOINT)["checkpoint_sha256"],
        "parent_run_seal_sha256": sha256_file(PARENT_ROOT / "RUN_SEAL.json"),
        "schema": "trellis-e99-verification-lifecycle-continuation-manifest-v1",
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
        "configuration": CONFIGURATION,
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
    failures = []
    if resolved.is_relative_to(ROOT.resolve()):
        failures.append("authorization_must_remain_outside_repository")
    for key, value in expected.items():
        if receipt.get(key) != value:
            failures.append(f"{key}_mismatch")
    if failures:
        raise RuntimeError(f"authorization failed: {failures}")
    return dict(receipt)


class HttpProvider:
    def __init__(self, root: Path, label: str) -> None:
        self.root = root
        self.label = label
        self.calls = 0

    def __call__(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls += 1
        response = complete_custodied(
            dict(payload), self.root / self.label / f"call-{self.calls:03d}"
        )
        return {
            "content": response["content"],
            "finish_reason": response["finish_reason"],
            "usage": response["usage"],
        }


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
        "frozen_donor_readiness_sha256": sha256_file(READINESS),
        "returncode": process.returncode,
        "schema": "trellis-e99-continuation-external-evaluation-v1",
        "stderr_utf8": process.stderr.decode("utf-8", errors="replace"),
    }
    write_json(output_path, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization-receipt", required=True, type=Path)
    args = parser.parse_args()
    require_clean_tree()
    authorization = authorize(args.authorization_receipt)
    seal_errors = verify_tree_seal(PARENT_ROOT, PARENT_ROOT / "RUN_SEAL.json")
    if seal_errors:
        raise RuntimeError(f"parent run seal failed: {seal_errors}")
    stage0 = load_json(STAGE0)
    if stage0.get("passed") is not True:
        raise RuntimeError("frozen continuation Stage 0 is not qualified")
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
            "execution_manifest": execution_manifest(),
            "model_profile_lock_sha256": sha256_file(ROOT / "MODEL_PROFILE_LOCK.json"),
            "run_id": RUN_ID,
            "schema": "trellis-e99-verification-lifecycle-continuation-freeze-binding-v1",
            "stage0_sha256": sha256_file(STAGE0),
        },
    )
    assets = verify_runtime_assets(SELECTED_ASSETS)
    write_json(run_root / "RUNTIME_ASSET_VERIFICATION.json", assets)
    if assets["passed"] is not True:
        raise RuntimeError(f"runtime assets failed: {assets['failures']}")

    process = stdout = stderr = None
    release = None
    result: dict[str, Any] | None = None
    failure: dict[str, Any] | None = None
    try:
        process, stdout, stderr, runtime_gate = start_server(run_root / "model")
        tokenizer = LiveTokenizer()
        actor_http = HttpProvider(run_root / "http", "actor")
        maintenance_http = HttpProvider(run_root / "http", "maintenance")
        orchestrator, adapter, kernel, counters = hydrate_checkpoint(
            repository_root=ROOT,
            checkpoint_path=PARENT_CHECKPOINT,
            trajectory_root=run_root / "trajectory",
            count_messages=lambda messages: tokenizer.count_messages(messages)[0],
            count_text=lambda value: len(tokenizer.tokenize(value)),
            maintenance_complete=maintenance_http,
        )
        starting_tokens = counters.serialized_tokens
        starting_provider = counters.provider_attempts
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
        additional_provider = tranche.counters.provider_attempts - starting_provider
        additional_tokens = tranche.counters.serialized_tokens - starting_tokens
        if tranche.actor_attempts > MAXIMUM_ACTOR_CALLS:
            raise RuntimeError("actor authorization exceeded")
        if tranche.maintenance_attempts > MAXIMUM_MAINTENANCE_CALLS:
            raise RuntimeError("maintenance authorization exceeded")
        if additional_provider > MAXIMUM_PROVIDER_CALLS:
            raise RuntimeError("provider authorization exceeded")
        if additional_tokens > MAXIMUM_SERIALIZED_TOKENS:
            raise RuntimeError("serialized-token authorization exceeded")
        result = {
            "actor_calls": tranche.actor_attempts,
            "maintenance_calls": tranche.maintenance_attempts,
            "provider_calls": additional_provider,
            "serialized_tokens": additional_tokens,
            "candidate_sha256": adapter.world.candidate_sha256,
            "disposition": tranche.disposition.value,
            "evaluation_passed": evaluation["evaluation"].get("passed"),
            "freeze_commit": git_commit(),
            "run_id": RUN_ID,
            "runtime_gate_passed": runtime_gate["passed"],
            "schema": "trellis-e99-verification-lifecycle-continuation-result-v1",
            "submitted": adapter.world.submitted,
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
            {"failure": failure, "result": result, "runtime_release": release},
        )
        seal_tree(run_root, run_root / "RUN_SEAL.json")
        if process is not None and (
            release is None or release.get("released") is not True
        ):
            raise RuntimeError("runtime release failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
