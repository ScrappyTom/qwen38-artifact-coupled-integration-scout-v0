from __future__ import annotations

import argparse
import json
import sys
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_bytes, sha256_file, write_json  # noqa: E402
from reactive_runtime.meridian_boundary import verify_meridian_pressure_handoff  # noqa: E402
from reactive_runtime.meridian_qualification import build_meridian_delta_case  # noqa: E402
from reactive_runtime.seal import seal_tree  # noqa: E402
from reactive_runtime.source_delta import (  # noqa: E402
    DELTA_PROVIDER_MAX_TOKENS,
    DELTA_TOKEN_BUDGET,
    SLOT_TOKEN_BUDGET,
    validate_source_delta,
)
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


RUN_ID = "2026-08-25-meridian-source-delta-expression-qualification-v0"
SCOPE = "meridian_source_delta_expression_qualification_v0"
MAX_CALLS = 1
CONTEXT_TOKENS = 25_088
CONTRACT = ROOT / "MERIDIAN_SOURCE_DELTA_QUALIFICATION_CONTRACT.json"
REQUEST = ROOT / "MERIDIAN_SOURCE_DELTA_AUTHORIZATION_REQUEST.json"
PREFLIGHT = ROOT / "MERIDIAN_SOURCE_DELTA_QUALIFICATION_PREFLIGHT.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def authorize(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if resolved.is_relative_to(ROOT.resolve()):
        raise RuntimeError("authorization receipt must remain outside the repository")
    receipt = load(resolved)
    request = load(REQUEST)
    commit = git_commit()
    expected = {
        "authorized": True,
        "authorized_freeze_commit": commit,
        "authorized_scopes": [SCOPE],
        "authorized_run_id": RUN_ID,
        "maximum_model_calls": MAX_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
        "authorization_text": request["expected_user_quote_template"].replace(
            "{commit}", commit
        ),
    }
    failures = [key for key, value in expected.items() if receipt.get(key) != value]
    if failures:
        raise RuntimeError(f"authorization receipt mismatch: {failures}")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization-receipt", required=True, type=Path)
    args = parser.parse_args()
    require_clean_tree()
    handoff = verify_meridian_pressure_handoff(ROOT)
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
            "schema": "meridian-source-delta-qualification-freeze-v0",
            "commit": git_commit(),
            "run_id": RUN_ID,
            "pressure_handoff": handoff,
            "pressure_handoff_sha256": sha256_file(
                ROOT / "MERIDIAN_PRESSURE_BOUNDARY_HANDOFF.json"
            ),
            "contract_sha256": sha256_file(CONTRACT),
            "preflight_sha256": sha256_file(PREFLIGHT),
            "task_source_lock_sha256": sha256_file(
                ROOT / "task_meridian" / "TASK_SOURCE_LOCK.json"
            ),
            "model_profile_lock_sha256": sha256_file(
                ROOT / "MERIDIAN_MODEL_PROFILE_LOCK.json"
            ),
        },
    )
    process = stdout = stderr = None
    release: dict[str, Any] | None = None
    failure: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    try:
        process, stdout, stderr, _ = start_server(run_root / "model")
        tokenizer = LiveTokenizer()
        case = build_meridian_delta_case(ROOT)
        prompt_tokens, rendered = tokenizer.count_messages(case.messages)
        if prompt_tokens + DELTA_PROVIDER_MAX_TOKENS > CONTEXT_TOKENS:
            raise RuntimeError("qualification prompt exceeds context")
        call_root = run_root / "calls" / f"01-{case.case_id}"
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
                max_tokens=DELTA_PROVIDER_MAX_TOKENS,
            ),
            call_root / "provider_attempt",
        )
        usage = provider.get("usage")
        if not isinstance(usage, dict):
            raise RuntimeError("provider usage missing")
        if usage.get("prompt_tokens") != prompt_tokens:
            raise RuntimeError("provider prompt usage mismatch")
        if usage.get("total_tokens") != usage.get("prompt_tokens", 0) + usage.get(
            "completion_tokens", 0
        ):
            raise RuntimeError("provider usage arithmetic mismatch")
        output = provider["content"]
        (call_root / "assistant_content.txt").write_text(
            output, encoding="utf-8", newline=""
        )
        catalog = load(ROOT / "task_meridian" / "SOURCE_CATALOG.json")
        known_source_ids = [str(row["source_id"]) for row in catalog["sources"]]
        validation = validate_source_delta(
            output,
            count_text=lambda value: len(tokenizer.tokenize(value)),
            allowed_source_versions=case.allowed_source_versions,
            known_source_ids=known_source_ids,
            token_budget=DELTA_TOKEN_BUDGET,
            slot_token_budget=SLOT_TOKEN_BUDGET,
        )
        transport_passed = provider.get("finish_reason") == "stop" and validation.valid
        result = {
            "schema": "meridian-source-delta-expression-result-v0",
            "run_id": RUN_ID,
            "freeze_commit": git_commit(),
            "case_id": case.case_id,
            "seed": case.seed,
            "model_calls": 1,
            "input_result_ids": list(case.input_result_ids),
            "allowed_source_versions": case.allowed_source_versions,
            "prompt_tokens": prompt_tokens,
            "finish_reason": provider.get("finish_reason"),
            "output_sha256": sha256_bytes(output.encode("utf-8")),
            "usage": usage,
            "validation": asdict(validation),
            "transport_passed": transport_passed,
            "semantic_safety_adjudication": "pending_offline",
            "qualification_passed": False,
            "measured_continuation_authorized": False,
        }
        write_json(call_root / "RESULT.json", result)
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
                release = {
                    "released": False,
                    "exception": f"{type(exc).__name__}: {exc}",
                }
        write_json(run_root / "FINALIZATION.json", {"failure": failure, "release": release})
        seal_tree(run_root, run_root / "RUN_SEAL.json")
    if failure is not None:
        print(json.dumps(failure, indent=2, sort_keys=True))
        return 1
    if release is None or release.get("released") is not True:
        raise RuntimeError("GPU/runtime release did not qualify")
    assert result is not None
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["transport_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
