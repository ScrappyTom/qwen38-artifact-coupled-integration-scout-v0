from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.bluehaven_boundary import (  # noqa: E402
    verify_bluehaven_pressure_handoff,
)
from reactive_runtime.bluehaven_qualification import (  # noqa: E402
    build_bluehaven_maintenance_cases,
)
from reactive_runtime.canonical import sha256_bytes, sha256_file, write_json  # noqa: E402
from reactive_runtime.integration import (  # noqa: E402
    BATCHED_INTEGRATION_PROVIDER_MAX_TOKENS,
    BATCHED_INTEGRATION_TOKEN_BUDGET,
    validate_integration,
)
from reactive_runtime.seal import seal_tree  # noqa: E402
from tools.live_common import (  # noqa: E402
    LiveTokenizer,
    complete_custodied,
    git_commit,
    provider_payload,
    require_clean_tree,
    start_server,
    stop_server,
)
from tools.verify_runtime_assets import verify as verify_runtime_assets  # noqa: E402


RUN_ID = "2026-08-25-bluehaven-batched-maintenance-expression-qualification-v0"
SCOPE = "bluehaven_batched_maintenance_expression_qualification_v0"
MAX_CALLS = 2
CONTEXT_TOKENS = 25_088


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def authorize(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise RuntimeError("authorization receipt must remain outside the repository")
    receipt = load(resolved)
    request = load(ROOT / "BLUEHAVEN_BATCHED_MAINTENANCE_AUTHORIZATION_REQUEST.json")
    commit = git_commit()
    expected = {
        "authorized": True,
        "authorized_freeze_commit": commit,
        "authorized_run_id": RUN_ID,
        "authorized_scope": SCOPE,
        "maximum_model_calls": MAX_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
        "user_quote": request["expected_user_quote_template"].replace("{commit}", commit),
    }
    failures = [
        key for key, expected_value in expected.items() if receipt.get(key) != expected_value
    ]
    if not isinstance(receipt.get("authorization_id"), str) or not receipt["authorization_id"]:
        failures.append("authorization_id")
    if failures:
        raise RuntimeError(f"authorization receipt mismatch: {sorted(set(failures))}")
    return receipt


def checked_usage(
    result: dict[str, Any], expected_prompt: int, maximum_completion: int
) -> dict[str, Any]:
    usage = result.get("usage")
    if not isinstance(usage, dict):
        raise RuntimeError("provider usage missing")
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    total = usage.get("total_tokens")
    if prompt != expected_prompt:
        raise RuntimeError(f"provider prompt mismatch: {prompt} != {expected_prompt}")
    if type(completion) is not int or not 0 <= completion <= maximum_completion:
        raise RuntimeError("provider completion count invalid")
    if total != prompt + completion:
        raise RuntimeError("provider total count invalid")
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "cached_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization-receipt", required=True, type=Path)
    args = parser.parse_args()
    require_clean_tree()
    handoff = verify_bluehaven_pressure_handoff(ROOT)
    authorization = authorize(args.authorization_receipt)
    run_root = ROOT / "qualification_runs" / RUN_ID
    if run_root.exists():
        raise FileExistsError(f"run root already exists: {run_root}")
    run_root.mkdir(parents=True)
    write_json(run_root / "AUTHORIZATION_RECEIPT.json", authorization)
    assets = verify_runtime_assets()
    write_json(run_root / "RUNTIME_ASSET_VERIFICATION.json", assets)
    if assets.get("passed") is not True:
        raise RuntimeError(f"runtime assets failed: {assets.get('failures')}")
    write_json(
        run_root / "FREEZE_BINDING.json",
        {
            "schema": "bluehaven-batched-maintenance-qualification-freeze-v0",
            "commit": git_commit(),
            "run_id": RUN_ID,
            "pressure_handoff": handoff,
            "task_source_lock_sha256": sha256_file(
                ROOT / "task_bluehaven" / "TASK_SOURCE_LOCK.json"
            ),
            "pressure_handoff_sha256": sha256_file(
                ROOT / "BLUEHAVEN_PRESSURE_BOUNDARY_HANDOFF.json"
            ),
            "contract_sha256": sha256_file(
                ROOT / "BLUEHAVEN_BATCHED_MAINTENANCE_QUALIFICATION_CONTRACT.json"
            ),
            "model_profile_lock_sha256": sha256_file(ROOT / "MODEL_PROFILE_LOCK.json"),
        },
    )
    process = stdout = stderr = None
    release: dict[str, Any] | None = None
    failure: dict[str, Any] | None = None
    rows: list[dict[str, Any]] = []
    try:
        process, stdout, stderr, _ = start_server(run_root / "model")
        tokenizer = LiveTokenizer()
        cases = build_bluehaven_maintenance_cases(ROOT)
        if len(cases) != MAX_CALLS:
            raise RuntimeError("qualification case count mismatch")
        for ordinal, case in enumerate(cases, 1):
            call_root = run_root / "calls" / f"{ordinal:02d}-{case.case_id}"
            prompt_tokens, rendered = tokenizer.count_messages(case.messages)
            if prompt_tokens + BATCHED_INTEGRATION_PROVIDER_MAX_TOKENS > CONTEXT_TOKENS:
                raise RuntimeError(f"qualification prompt exceeds context: {case.case_id}")
            write_json(call_root / "messages.json", case.messages)
            (call_root / "rendered_prompt.txt").parent.mkdir(parents=True, exist_ok=True)
            (call_root / "rendered_prompt.txt").write_text(
                rendered, encoding="utf-8", newline=""
            )
            provider = complete_custodied(
                provider_payload(
                    case.messages,
                    case.seed,
                    {"type": "text"},
                    max_tokens=BATCHED_INTEGRATION_PROVIDER_MAX_TOKENS,
                ),
                call_root / "provider_attempt",
            )
            usage = checked_usage(
                provider, prompt_tokens, BATCHED_INTEGRATION_PROVIDER_MAX_TOKENS
            )
            output = provider["content"]
            (call_root / "assistant_content.txt").write_text(
                output, encoding="utf-8", newline=""
            )
            validation = validate_integration(
                output,
                count_text=lambda value: len(tokenizer.tokenize(value)),
                allowed_source_ids=case.allowed_source_ids,
                token_budget=BATCHED_INTEGRATION_TOKEN_BUDGET,
            )
            accepted = provider.get("finish_reason") == "stop" and validation.valid
            row = {
                "case_id": case.case_id,
                "seed": case.seed,
                "input_result_ids": list(case.input_result_ids),
                "allowed_source_ids": list(case.allowed_source_ids),
                "prior_present": case.prior is not None,
                "prompt_tokens": prompt_tokens,
                "finish_reason": provider.get("finish_reason"),
                "accepted": accepted,
                "validation": validation.__dict__,
                "output_sha256": sha256_bytes(output.encode("utf-8")),
                "usage": usage,
            }
            rows.append(row)
            write_json(call_root / "RESULT.json", row)
        result = {
            "schema": "bluehaven-batched-maintenance-expression-result-v0",
            "run_id": RUN_ID,
            "freeze_commit": git_commit(),
            "model_calls": len(rows),
            "passed": len(rows) == MAX_CALLS and all(row["accepted"] for row in rows),
            "cases": rows,
            "measured_continuation_authorized": False,
        }
        write_json(run_root / "QUALIFICATION_RESULT.json", result)
    except BaseException as exc:
        failure = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "no_retry": True,
        }
        write_json(run_root / "RUN_FAILURE.json", failure)
    finally:
        if process is not None:
            try:
                release = stop_server(process, stdout, stderr, run_root / "model")
            except BaseException as exc:
                release = {"released": False, "exception": f"{type(exc).__name__}: {exc}"}
        write_json(run_root / "FINALIZATION.json", {"failure": failure, "release": release})
        seal_tree(run_root, run_root / "RUN_SEAL.json")
    if failure is not None:
        print(json.dumps(failure, indent=2, sort_keys=True))
        return 1
    if release is None or release.get("released") is not True:
        raise RuntimeError("GPU/runtime release did not qualify")
    result = load(run_root / "QUALIFICATION_RESULT.json")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("passed") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
