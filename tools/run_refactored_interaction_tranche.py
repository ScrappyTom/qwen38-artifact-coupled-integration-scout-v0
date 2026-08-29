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

from reactive_runtime.canonical import load_json, sha256_file, write_json
from reactive_runtime.seal import seal_tree

from host_refactor.checkpoint import RuntimeCounters
from host_refactor.model import TerminalCode
from interaction_scout.live_path import run_interaction_tranche
from interaction_scout.system import (
    CONFIGURATION_ORDER,
    MAXIMUM_ACTOR_CALLS,
    MAXIMUM_MAINTENANCE_CALLS,
    MAXIMUM_PROVIDER_CALLS,
    MAXIMUM_SERIALIZED_TOKENS,
    RUN_ID,
    SCOPE,
    build_interaction_system,
    interaction_execution_manifest,
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


CONTRACT = ROOT / "TRELLIS_REFACTORED_INTERACTION_CONTRACT.json"
REQUEST = ROOT / "TRELLIS_REFACTORED_INTERACTION_AUTHORIZATION_REQUEST.json"
SELECTED_ASSETS = {"model_gguf", "llama_server_cuda", "llama_tokenize_cpu"}


def authorize(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    receipt = load_json(resolved)
    request = load_json(REQUEST)
    expected = {
        "authorized": True,
        "authorized_freeze_commit": git_commit(),
        "authorized_scopes": [SCOPE],
        "authorized_run_id": RUN_ID,
        "configuration_order": list(CONFIGURATION_ORDER),
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


def external_evaluation(candidate_root: Path, output_path: Path) -> dict[str, Any]:
    script = ROOT / "task_trellis" / "evaluator" / "evaluate.py"
    process = subprocess.run(
        [sys.executable, str(script), str(candidate_root)],
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
        "schema": "trellis-checkpoint-external-evaluation-v0",
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
    run_root = ROOT / "qualification_runs" / RUN_ID
    if run_root.exists():
        raise FileExistsError(f"interaction run root already exists: {run_root}")
    run_root.mkdir(parents=True)
    write_json(run_root / "AUTHORIZATION_RECEIPT.json", authorization)
    write_json(
        run_root / "FREEZE_BINDING.json",
        {
            "authorization_request_sha256": sha256_file(REQUEST),
            "commit": git_commit(),
            "contract_sha256": sha256_file(CONTRACT),
            "execution_manifest": interaction_execution_manifest(ROOT),
            "model_profile_lock_sha256": sha256_file(ROOT / "MODEL_PROFILE_LOCK.json"),
            "run_id": RUN_ID,
            "schema": "trellis-refactored-interaction-freeze-binding-v0",
        },
    )
    assets = verify_runtime_assets(SELECTED_ASSETS)
    write_json(run_root / "RUNTIME_ASSET_VERIFICATION.json", assets)
    if assets["passed"] is not True:
        raise RuntimeError(f"runtime assets failed: {assets['failures']}")

    results: list[dict[str, Any]] = []
    total_actor = total_maintenance = total_provider = total_tokens = 0
    failure: dict[str, Any] | None = None
    try:
        for configuration_id in CONFIGURATION_ORDER:
            cell_root = run_root / "cells" / configuration_id
            cell_root.mkdir(parents=True, exist_ok=False)
            process = stdout = stderr = None
            release = None
            try:
                process, stdout, stderr, runtime_gate = start_server(cell_root / "model")
                tokenizer = LiveTokenizer()
                maintenance_http = HttpProvider(cell_root / "http", "maintenance")
                host, adapter, kernel, orchestrator = build_interaction_system(
                    repository_root=ROOT,
                    trajectory_root=cell_root / "trajectory",
                    configuration_id=configuration_id,
                    run_id=f"{RUN_ID}:{configuration_id}",
                    count_messages=lambda messages: tokenizer.count_messages(messages)[0],
                    count_text=lambda text: len(tokenizer.tokenize(text)),
                    maintenance_complete=(
                        maintenance_http
                        if configuration_id == CONFIGURATION_ORDER[1]
                        else None
                    ),
                )
                actor_http = HttpProvider(cell_root / "http", "actor")
                tranche = run_interaction_tranche(
                    orchestrator=orchestrator,
                    kernel=kernel,
                    counters=RuntimeCounters(),
                    actor_complete=actor_http,
                    run_root=cell_root / "tranche-001",
                )
                evaluation = external_evaluation(
                    adapter.world.candidate_root,
                    cell_root / "EXTERNAL_CHECKPOINT_EVALUATION.json",
                )
                if tranche.disposition not in {
                    TerminalCode.CHECKPOINT_PAUSE,
                    TerminalCode.COMPLETED,
                }:
                    raise RuntimeError(
                        f"nonqualifying tranche disposition: {tranche.disposition.value}"
                    )
                actor_calls = tranche.actor_attempts
                maintenance_calls = tranche.maintenance_attempts
                provider_calls = tranche.counters.provider_attempts
                serialized = tranche.counters.serialized_tokens
                total_actor += actor_calls
                total_maintenance += maintenance_calls
                total_provider += provider_calls
                total_tokens += serialized
                result = {
                    "actor_calls": actor_calls,
                    "candidate_sha256": adapter.world.candidate_sha256,
                    "configuration_id": configuration_id,
                    "disposition": tranche.disposition.value,
                    "evaluation_passed": evaluation["evaluation"].get("passed"),
                    "maintenance_calls": maintenance_calls,
                    "provider_calls": provider_calls,
                    "runtime_gate_passed": runtime_gate["passed"],
                    "serialized_tokens": serialized,
                }
                results.append(result)
                write_json(cell_root / "CELL_RESULT.json", result)
            finally:
                if process is not None:
                    release = stop_server(process, stdout, stderr, cell_root / "model")
                write_json(cell_root / "RUNTIME_RELEASE.json", {"release": release})
                if process is not None and (
                    release is None or release.get("released") is not True
                ):
                    raise RuntimeError(f"runtime release failed: {configuration_id}")
        if total_actor > MAXIMUM_ACTOR_CALLS:
            raise RuntimeError("actor call authorization exceeded")
        if total_maintenance > MAXIMUM_MAINTENANCE_CALLS:
            raise RuntimeError("maintenance call authorization exceeded")
        if total_provider > MAXIMUM_PROVIDER_CALLS:
            raise RuntimeError("provider call authorization exceeded")
        if total_tokens > MAXIMUM_SERIALIZED_TOKENS:
            raise RuntimeError("serialized token authorization exceeded")
        write_json(
            run_root / "INTERACTION_TRANCHE_RESULT.json",
            {
                "actor_calls": total_actor,
                "cells": results,
                "freeze_commit": git_commit(),
                "maintenance_calls": total_maintenance,
                "provider_calls": total_provider,
                "run_id": RUN_ID,
                "schema": "trellis-refactored-interaction-result-v0",
                "serialized_tokens": total_tokens,
            },
        )
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
        write_json(
            run_root / "FINALIZATION.json",
            {"cells": results, "failure": failure},
        )
        seal_tree(run_root, run_root / "RUN_SEAL.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
