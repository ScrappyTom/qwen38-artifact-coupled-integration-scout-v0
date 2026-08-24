from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_bytes, write_json
from reactive_runtime.actions import action_json_schema, parse_action
from reactive_runtime.configuration import ordinary_actions
from reactive_runtime.integration import INTEGRATION_PROVIDER_MAX_TOKENS, validate_integration
from reactive_runtime.qualification import build_action_cases, build_cases
from reactive_runtime.seal import seal_tree
from tools.live_common import (
    LiveTokenizer,
    complete_custodied,
    git_commit,
    provider_payload,
    require_clean_tree,
    start_server,
    stop_server,
)
from tools.verify_runtime_assets import verify as verify_runtime_assets


RUN_ID = "2026-08-24-northstar-transfer-expression-qualification-v0"
SCOPE = "northstar_transfer_expression_qualification_v0"
MAX_CALLS = 4


def authorize(path: Path) -> dict[str, object]:
    receipt = json.loads(path.resolve().read_text(encoding="utf-8"))
    failures = []
    if path.resolve().is_relative_to(ROOT.resolve()):
        failures.append("authorization_must_remain_outside_repository")
    if receipt.get("authorized") is not True:
        failures.append("not_authorized")
    if receipt.get("authorized_freeze_commit") != git_commit():
        failures.append("commit_mismatch")
    if receipt.get("authorized_scopes") != [SCOPE]:
        failures.append("scope_mismatch")
    if receipt.get("authorized_run_id") != RUN_ID:
        failures.append("run_id_mismatch")
    if receipt.get("maximum_model_calls") != MAX_CALLS:
        failures.append("call_ceiling_mismatch")
    if receipt.get("attempts_per_call") != 1 or receipt.get("retries") != 0:
        failures.append("attempt_policy_mismatch")
    if failures:
        raise RuntimeError(f"authorization failed: {failures}")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization-receipt", required=True, type=Path)
    args = parser.parse_args()
    require_clean_tree()
    preflight = json.loads((ROOT / "STAGE0_PREFLIGHT.json").read_text(encoding="utf-8"))
    if preflight.get("passed") is not True:
        raise RuntimeError("offline Stage 0 preflight is not passing")
    authorization = authorize(args.authorization_receipt)
    run_root = ROOT / "qualification_runs" / RUN_ID
    if run_root.exists():
        raise FileExistsError(f"run root already exists: {run_root}")
    run_root.mkdir(parents=True)
    write_json(run_root / "AUTHORIZATION_RECEIPT.json", authorization)
    assets = verify_runtime_assets()
    write_json(run_root / "RUNTIME_ASSET_VERIFICATION.json", assets)
    if assets["passed"] is not True:
        raise RuntimeError(f"runtime assets failed: {assets['failures']}")
    process = stdout = stderr = None
    release = None
    rows = []
    failure = None
    qualified = False
    try:
        process, stdout, stderr, gate = start_server(run_root / "model")
        tokenizer = LiveTokenizer()
        for ordinal, case in enumerate(build_cases(ROOT), 1):
            call_root = run_root / "calls" / f"{ordinal:02d}-{case.case_id}"
            prompt_tokens, rendered = tokenizer.count_messages(case.messages)
            if prompt_tokens + INTEGRATION_PROVIDER_MAX_TOKENS > 25_088:
                raise RuntimeError(f"qualification prompt exceeds context: {case.case_id}")
            write_json(call_root / "messages.json", case.messages)
            (call_root / "rendered_prompt.txt").parent.mkdir(parents=True, exist_ok=True)
            (call_root / "rendered_prompt.txt").write_text(rendered, encoding="utf-8", newline="")
            provider = complete_custodied(
                provider_payload(case.messages, case.seed, {"type": "text"}, max_tokens=INTEGRATION_PROVIDER_MAX_TOKENS),
                call_root / "provider_attempt",
            )
            output = provider["content"]
            validation = validate_integration(output, count_text=lambda value: len(tokenizer.tokenize(value)), allowed_source_ids=case.allowed_source_ids)
            accepted = provider["finish_reason"] == "stop" and validation.valid
            (call_root / "assistant_content.txt").write_text(output, encoding="utf-8", newline="")
            row = {
                "case_id": case.case_id,
                "seed": case.seed,
                "prompt_tokens": prompt_tokens,
                "finish_reason": provider["finish_reason"],
                "accepted": accepted,
                "validation": validation.__dict__,
                "output_sha256": sha256_bytes(output.encode("utf-8")),
                "usage": provider["usage"],
            }
            rows.append(row)
            write_json(call_root / "RESULT.json", row)
        for offset, case in enumerate(build_action_cases(ROOT), 1):
            ordinal = len(rows) + 1
            call_root = run_root / "calls" / f"{ordinal:02d}-{case.case_id}"
            prompt_tokens, rendered = tokenizer.count_messages(case.messages)
            if prompt_tokens + 4096 > 25_088:
                raise RuntimeError(f"action qualification prompt exceeds context: {case.case_id}")
            write_json(call_root / "messages.json", case.messages)
            (call_root / "rendered_prompt.txt").parent.mkdir(parents=True, exist_ok=True)
            (call_root / "rendered_prompt.txt").write_text(rendered, encoding="utf-8", newline="")
            schema = action_json_schema((case.required_action,), source_ids=("S02",), reopen_result_ids=())
            provider = complete_custodied(provider_payload(case.messages, case.seed, schema, max_tokens=4096), call_root / "provider_attempt")
            output = provider["content"]
            parsed = None
            error = None
            try:
                parsed = parse_action(output, ordinary_actions())
                if parsed["action"] != case.required_action:
                    raise ValueError("wrong action")
                if case.required_action == "replace_evidence_ledger":
                    validation = validate_integration(parsed["content"], count_text=lambda value: len(tokenizer.tokenize(value)), allowed_source_ids=("S02",))
                    if not validation.valid:
                        raise ValueError(f"ledger action content invalid: {validation.issues}")
            except (ValueError, json.JSONDecodeError) as exc:
                error = f"{type(exc).__name__}: {exc}"
            accepted = provider["finish_reason"] == "stop" and parsed is not None and error is None
            (call_root / "assistant_content.txt").write_text(output, encoding="utf-8", newline="")
            row = {"case_id": case.case_id, "seed": case.seed, "prompt_tokens": prompt_tokens, "finish_reason": provider["finish_reason"], "accepted": accepted, "required_action": case.required_action, "parsed_action": parsed, "error": error, "output_sha256": sha256_bytes(output.encode("utf-8")), "usage": provider["usage"]}
            rows.append(row)
            write_json(call_root / "RESULT.json", row)
        result = {"schema": "northstar-transfer-expression-result-v0", "run_id": RUN_ID, "freeze_commit": git_commit(), "model_calls": len(rows), "passed": len(rows) == MAX_CALLS and all(row["accepted"] for row in rows), "cases": rows, "measured_actor_authorized": False}
        qualified = bool(result["passed"])
        write_json(run_root / "QUALIFICATION_RESULT.json", result)
    except BaseException as exc:
        failure = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(), "no_retry": True}
        write_json(run_root / "RUN_FAILURE.json", failure)
        raise
    finally:
        if process is not None:
            release = stop_server(process, stdout, stderr, run_root / "model")
        write_json(run_root / "FINALIZATION.json", {"failure": failure, "release": release})
        seal_tree(run_root, run_root / "RUN_SEAL.json")
    if release is None or release.get("released") is not True:
        raise RuntimeError("GPU/runtime release did not qualify")
    return 0 if qualified else 2


if __name__ == "__main__":
    raise SystemExit(main())
