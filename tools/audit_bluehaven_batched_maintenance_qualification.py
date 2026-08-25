from __future__ import annotations

import json
import sys
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
    BATCHED_INTEGRATION_TOKEN_BUDGET,
    validate_integration,
)
from reactive_runtime.seal import verify_tree_seal  # noqa: E402
from tools.offline_tokenizer import OfflineTokenizer  # noqa: E402


RUN_ID = "2026-08-25-bluehaven-batched-maintenance-expression-qualification-v0"
FREEZE_COMMIT = "7051e20b3f46c4100292db5c767482b359362178"
AUDIT_NAME = "BLUEHAVEN_BATCHED_MAINTENANCE_QUALIFICATION_AUDIT.json"
EXPECTED_CASES = (
    "Q1_INITIAL_THREE_RESULT_BATCH",
    "Q2_REPLACEMENT_THREE_RESULT_BATCH",
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def audit(repository_root: Path = ROOT, *, write_output: bool = True) -> dict[str, Any]:
    root = repository_root.resolve()
    run_root = root / "qualification_runs" / RUN_ID
    failures: list[str] = []
    required = (
        "AUTHORIZATION_RECEIPT.json",
        "FINALIZATION.json",
        "FREEZE_BINDING.json",
        "QUALIFICATION_RESULT.json",
        "RUN_SEAL.json",
        "RUNTIME_ASSET_VERIFICATION.json",
        "model/RUNTIME_GATE.json",
        "model/RUNTIME_RELEASE.json",
    )
    for relative in required:
        if not (run_root / relative).is_file():
            failures.append(f"missing:{relative}")
    if failures:
        return {
            "schema": "bluehaven-batched-maintenance-expression-audit-v0",
            "run_id": RUN_ID,
            "passed": False,
            "failures": failures,
        }

    seal_errors = list(verify_tree_seal(run_root, run_root / "RUN_SEAL.json"))
    failures.extend(f"seal:{item}" for item in seal_errors)
    handoff = verify_bluehaven_pressure_handoff(root)
    result = load(run_root / "QUALIFICATION_RESULT.json")
    authorization = load(run_root / "AUTHORIZATION_RECEIPT.json")
    finalization = load(run_root / "FINALIZATION.json")
    freeze = load(run_root / "FREEZE_BINDING.json")
    assets = load(run_root / "RUNTIME_ASSET_VERIFICATION.json")
    gate = load(run_root / "model" / "RUNTIME_GATE.json")
    release = load(run_root / "model" / "RUNTIME_RELEASE.json")

    expected_result = {
        "run_id": RUN_ID,
        "freeze_commit": FREEZE_COMMIT,
        "model_calls": 2,
        "passed": False,
        "measured_continuation_authorized": False,
    }
    for key, expected in expected_result.items():
        if result.get(key) != expected:
            failures.append(f"result:{key}")
    expected_authorization = {
        "authorized": True,
        "authorized_freeze_commit": FREEZE_COMMIT,
        "authorized_run_id": RUN_ID,
        "authorized_scope": "bluehaven_batched_maintenance_expression_qualification_v0",
        "maximum_model_calls": 2,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, expected in expected_authorization.items():
        if authorization.get(key) != expected:
            failures.append(f"authorization:{key}")
    if freeze.get("commit") != FREEZE_COMMIT or freeze.get("run_id") != RUN_ID:
        failures.append("freeze_binding")
    if freeze.get("pressure_handoff") != handoff:
        failures.append("freeze_pressure_handoff")
    if assets.get("passed") is not True or gate.get("passed") is not True:
        failures.append("runtime_gate")
    if release.get("released") is not True:
        failures.append("runtime_release")
    if finalization.get("failure") is not None:
        failures.append("finalization_failure")
    if finalization.get("release") != release:
        failures.append("finalization_release")
    if (run_root / "RUN_FAILURE.json").exists():
        failures.append("run_failure_present")

    cases = build_bluehaven_maintenance_cases(root)
    tokenizer = OfflineTokenizer()
    rows = result.get("cases")
    if not isinstance(rows, list):
        rows = []
        failures.append("result_cases_not_list")
    if tuple(row.get("case_id") for row in rows if isinstance(row, dict)) != EXPECTED_CASES:
        failures.append("case_order")
    total_prompt = 0
    total_completion = 0
    total_serialized = 0
    recomputed: list[dict[str, Any]] = []
    for ordinal, (case, row) in enumerate(zip(cases, rows, strict=False), 1):
        if not isinstance(row, dict):
            failures.append(f"case:{ordinal}:not_object")
            continue
        call_root = run_root / "calls" / f"{ordinal:02d}-{case.case_id}"
        messages = json.loads((call_root / "messages.json").read_text(encoding="utf-8"))
        if messages != case.messages:
            failures.append(f"case:{case.case_id}:messages")
        prompt = tokenizer.count_messages(case.messages)
        if row.get("prompt_tokens") != prompt:
            failures.append(f"case:{case.case_id}:prompt")
        if row.get("input_result_ids") != list(case.input_result_ids):
            failures.append(f"case:{case.case_id}:inputs")
        if row.get("allowed_source_ids") != list(case.allowed_source_ids):
            failures.append(f"case:{case.case_id}:allowlist")
        output = (call_root / "assistant_content.txt").read_text(encoding="utf-8")
        if row.get("output_sha256") != sha256_bytes(output.encode("utf-8")):
            failures.append(f"case:{case.case_id}:output_hash")
        validation = validate_integration(
            output,
            count_text=tokenizer.count_text,
            allowed_source_ids=case.allowed_source_ids,
            token_budget=BATCHED_INTEGRATION_TOKEN_BUDGET,
        )
        normalized_validation = json.loads(json.dumps(validation.__dict__))
        if row.get("validation") != normalized_validation:
            failures.append(f"case:{case.case_id}:validation")
        expected_accepted = row.get("finish_reason") == "stop" and validation.valid
        if row.get("accepted") is not expected_accepted:
            failures.append(f"case:{case.case_id}:accepted")
        usage = row.get("usage")
        if not isinstance(usage, dict):
            failures.append(f"case:{case.case_id}:usage")
            continue
        prompt_usage = usage.get("prompt_tokens")
        completion = usage.get("completion_tokens")
        total = usage.get("total_tokens")
        if prompt_usage != prompt or total != prompt_usage + completion:
            failures.append(f"case:{case.case_id}:usage_arithmetic")
        total_prompt += int(prompt_usage)
        total_completion += int(completion)
        total_serialized += int(total)
        receipt = load(call_root / "provider_attempt" / "PROVIDER_CALL_RECEIPT.json")
        if receipt.get("attempted") is not True:
            failures.append(f"case:{case.case_id}:not_attempted")
        if receipt.get("outcome") != "valid_completion_response":
            failures.append(f"case:{case.case_id}:provider_outcome")
        recomputed.append(
            {
                "case_id": case.case_id,
                "accepted": expected_accepted,
                "output_tokens": validation.output_tokens,
                "validation_code": validation.code,
                "disallowed_source_ids": list(validation.disallowed_source_ids),
            }
        )

    if len(list(run_root.glob("calls/*/provider_attempt"))) != 2:
        failures.append("provider_attempt_count")
    expected_recomputed = [
        {
            "case_id": "Q1_INITIAL_THREE_RESULT_BATCH",
            "accepted": False,
            "output_tokens": 1057,
            "validation_code": "unobserved_source_reference",
            "disallowed_source_ids": ["S07", "S08", "S09", "S10", "S11", "S12"],
        },
        {
            "case_id": "Q2_REPLACEMENT_THREE_RESULT_BATCH",
            "accepted": True,
            "output_tokens": 1273,
            "validation_code": "accepted",
            "disallowed_source_ids": [],
        },
    ]
    if recomputed != expected_recomputed:
        failures.append("literal_disposition")

    value = {
        "schema": "bluehaven-batched-maintenance-expression-audit-v0",
        "run_id": RUN_ID,
        "freeze_commit": FREEZE_COMMIT,
        "passed": not failures,
        "failures": sorted(set(failures)),
        "qualification_passed": result.get("passed") is True,
        "case_dispositions": recomputed,
        "model_calls": len(rows),
        "provider_attempts": len(list(run_root.glob("calls/*/provider_attempt"))),
        "attempts_per_call": 1,
        "retries": 0,
        "prompt_tokens": total_prompt,
        "completion_tokens": total_completion,
        "serialized_tokens": total_serialized,
        "runtime_released": release.get("released") is True,
        "measured_continuation_authorized": False,
        "qualification_result_sha256": sha256_file(run_root / "QUALIFICATION_RESULT.json"),
        "run_seal_sha256": sha256_file(run_root / "RUN_SEAL.json"),
    }
    if write_output:
        write_json(root / AUDIT_NAME, value)
    return value


def main() -> int:
    value = audit()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
