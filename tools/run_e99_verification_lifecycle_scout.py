from __future__ import annotations

# ruff: noqa: E402

import argparse
import json
import subprocess
import traceback
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from host_refactor.lifecycle_scout.migration import (
    DONOR_CHECKPOINT_SHA256,
    donor_checkpoint_path,
)
from host_refactor.lifecycle_scout_v1.migration import migrate_donor
from host_refactor.lifecycle_scout_v1.system import (
    MAXIMUM_ADDITIONAL_ACTOR_CALLS,
    MAXIMUM_ADDITIONAL_MAINTENANCE_CALLS,
    MAXIMUM_ADDITIONAL_PROVIDER_CALLS,
    MAXIMUM_ADDITIONAL_SERIALIZED_TOKENS,
    RUN_ID,
    SCOUT_CONFIGURATION_ID,
    SCOPE,
    execution_manifest,
)
from interaction_scout.live_path import run_interaction_tranche
from reactive_runtime.canonical import load_json, sha256_file, write_json
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


CONTRACT = ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_SCOUT_CONTRACT.json"
REQUEST = ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_SCOUT_AUTHORIZATION_REQUEST.json"
STAGE0 = ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_STAGE0.json"
READINESS = ROOT / "TRELLIS_E97_DONOR_READINESS_ADJUDICATION.json"
DONOR_RUN_ROOT = (
    ROOT
    / "qualification_runs"
    / "2026-08-29-trellis-refactored-interaction-continuation-v0"
)
SELECTED_ASSETS = {"model_gguf", "llama_server_cuda", "llama_tokenize_cpu"}


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
        "schema": "trellis-e99-checkpoint-external-evaluation-v1",
        "stderr_utf8": process.stderr.decode("utf-8", errors="replace"),
    }
    write_json(output_path, receipt)
    return receipt


def authorize(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    receipt = load_json(resolved)
    request = load_json(REQUEST)
    expected = {
        "authorized": True,
        "authorized_freeze_commit": git_commit(),
        "authorized_scopes": [SCOPE],
        "authorized_run_id": RUN_ID,
        "configuration": SCOUT_CONFIGURATION_ID,
        "maximum_actor_calls": MAXIMUM_ADDITIONAL_ACTOR_CALLS,
        "maximum_maintenance_calls": MAXIMUM_ADDITIONAL_MAINTENANCE_CALLS,
        "maximum_provider_calls": MAXIMUM_ADDITIONAL_PROVIDER_CALLS,
        "maximum_serialized_tokens": MAXIMUM_ADDITIONAL_SERIALIZED_TOKENS,
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization-receipt", required=True, type=Path)
    args = parser.parse_args()
    require_clean_tree()
    authorization = authorize(args.authorization_receipt)
    donor_seal_errors = verify_tree_seal(
        DONOR_RUN_ROOT, DONOR_RUN_ROOT / "RUN_SEAL.json"
    )
    if donor_seal_errors:
        raise RuntimeError(f"donor run seal failed: {donor_seal_errors}")
    if load_json(donor_checkpoint_path(ROOT))["checkpoint_sha256"] != DONOR_CHECKPOINT_SHA256:
        raise RuntimeError("donor checkpoint identity changed")
    stage0 = load_json(STAGE0)
    if stage0.get("passed") is not True:
        raise RuntimeError("frozen Stage 0 is not qualified")

    run_root = ROOT / "qualification_runs" / RUN_ID
    if run_root.exists():
        raise FileExistsError(f"run root already exists: {run_root}")
    run_root.mkdir(parents=True)
    write_json(run_root / "AUTHORIZATION_RECEIPT.json", authorization)
    write_json(
        run_root / "FREEZE_BINDING.json",
        {
            "authorization_request_sha256": sha256_file(REQUEST),
            "commit": git_commit(),
            "contract_sha256": sha256_file(CONTRACT),
            "donor_run_seal_sha256": sha256_file(DONOR_RUN_ROOT / "RUN_SEAL.json"),
            "execution_manifest": execution_manifest(ROOT),
            "frozen_readiness_sha256": sha256_file(READINESS),
            "model_profile_lock_sha256": sha256_file(ROOT / "MODEL_PROFILE_LOCK.json"),
            "run_id": RUN_ID,
            "schema": "trellis-e99-verification-lifecycle-freeze-binding-v1",
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
        migration = migrate_donor(
            repository_root=ROOT,
            trajectory_root=run_root / "trajectory",
            count_messages=lambda messages: tokenizer.count_messages(messages)[0],
            count_text=lambda value: len(tokenizer.tokenize(value)),
            maintenance_complete=maintenance_http,
            checkpoint_output=run_root / "migration" / "MIGRATED_CHECKPOINT.json",
            receipt_output=run_root / "migration" / "MIGRATION_RECEIPT.json",
        )
        frozen_migration = stage0["migration_receipt"]
        immutable_keys = (
            "candidate_sha256",
            "donor_checkpoint_sha256",
            "externalized_applied_effect_ids",
            "pending_effect_id",
        )
        mismatches = [
            key
            for key in immutable_keys
            if migration.receipt.get(key) != frozen_migration.get(key)
        ]
        live_preflight = {
            "frozen_offline_prompt_tokens": frozen_migration["prompt_tokens"],
            "immutable_mismatches": mismatches,
            "live_prompt_tokens": migration.receipt["prompt_tokens"],
            "passed": (
                not mismatches
                and migration.receipt["prompt_tokens"]
                <= migration.host.configuration.prompt_limit
            ),
            "prompt_limit": migration.host.configuration.prompt_limit,
            "schema": "trellis-e99-live-migration-preflight-v1",
            "token_authority": "running_server_apply_template_plus_tokenize",
        }
        write_json(run_root / "LIVE_PREFLIGHT.json", live_preflight)
        if not live_preflight["passed"]:
            raise RuntimeError(f"live migration preflight failed: {live_preflight}")

        starting_tokens = migration.counters.serialized_tokens
        starting_provider = migration.counters.provider_attempts
        tranche = run_interaction_tranche(
            orchestrator=migration.orchestrator,
            kernel=migration.kernel,
            counters=migration.counters,
            actor_complete=actor_http,
            run_root=run_root / "tranche-001",
            parent_checkpoint_path=run_root / "migration" / "MIGRATED_CHECKPOINT.json",
        )
        evaluation = external_evaluation(
            migration.adapter.world.candidate_root,
            run_root / "EXTERNAL_CHECKPOINT_EVALUATION.json",
        )
        additional_provider = tranche.counters.provider_attempts - starting_provider
        additional_tokens = tranche.counters.serialized_tokens - starting_tokens
        if tranche.actor_attempts > MAXIMUM_ADDITIONAL_ACTOR_CALLS:
            raise RuntimeError("additional actor authorization exceeded")
        if tranche.maintenance_attempts > MAXIMUM_ADDITIONAL_MAINTENANCE_CALLS:
            raise RuntimeError("additional maintenance authorization exceeded")
        if additional_provider > MAXIMUM_ADDITIONAL_PROVIDER_CALLS:
            raise RuntimeError("additional provider authorization exceeded")
        if additional_tokens > MAXIMUM_ADDITIONAL_SERIALIZED_TOKENS:
            raise RuntimeError("additional serialized token authorization exceeded")
        result = {
            "additional_actor_calls": tranche.actor_attempts,
            "additional_maintenance_calls": tranche.maintenance_attempts,
            "additional_provider_calls": additional_provider,
            "additional_serialized_tokens": additional_tokens,
            "candidate_sha256": migration.adapter.world.candidate_sha256,
            "cumulative_provider_calls": tranche.counters.provider_attempts,
            "cumulative_serialized_tokens": tranche.counters.serialized_tokens,
            "disposition": tranche.disposition.value,
            "evaluation_passed": evaluation["evaluation"].get("passed"),
            "freeze_commit": git_commit(),
            "runtime_gate_passed": runtime_gate["passed"],
            "run_id": RUN_ID,
            "schema": "trellis-e99-verification-lifecycle-result-v1",
            "submitted": migration.adapter.world.submitted,
        }
        write_json(run_root / "LIFECYCLE_SCOUT_RESULT.json", result)
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
