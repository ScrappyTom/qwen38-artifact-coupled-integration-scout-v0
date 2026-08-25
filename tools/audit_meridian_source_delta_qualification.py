from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_bytes, sha256_file, write_json  # noqa: E402
from reactive_runtime.meridian_boundary import verify_meridian_pressure_handoff  # noqa: E402
from reactive_runtime.meridian_qualification import build_meridian_delta_case  # noqa: E402
from reactive_runtime.seal import verify_tree_seal  # noqa: E402
from reactive_runtime.source_delta import (  # noqa: E402
    DELTA_TOKEN_BUDGET,
    SLOT_TOKEN_BUDGET,
    validate_source_delta,
)
from tools.offline_tokenizer import OfflineTokenizer  # noqa: E402


RUN_ID = "2026-08-25-meridian-source-delta-expression-qualification-v0"
FREEZE_COMMIT = "1e0323945b1105aafba8c4b5fd0e4dc7f9f3180a"
CASE_ID = "Q1_FIRST_ACTUAL_EXTERNALIZATION"
AUDIT_NAME = "MERIDIAN_SOURCE_DELTA_QUALIFICATION_AUDIT.json"
ADJUDICATION_NAME = "MERIDIAN_SOURCE_DELTA_MATERIAL_SAFETY_ADJUDICATION.json"
EXPECTED_DISALLOWED = ("DRIFT", "EMBER", "HEATH", "NORTH")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def audit(repository_root: Path = ROOT, *, write_output: bool = True) -> dict[str, Any]:
    root = repository_root.resolve()
    run_root = root / "qualification_runs" / RUN_ID
    call_root = run_root / "calls" / f"01-{CASE_ID}"
    failures: list[str] = []
    required = (
        "AUTHORIZATION_RECEIPT.json",
        "FINALIZATION.json",
        "FREEZE_BINDING.json",
        "QUALIFICATION_RESULT.json",
        "RUN_SEAL.json",
        "RUNTIME_ASSET_VERIFICATION.json",
        f"calls/01-{CASE_ID}/RESULT.json",
        f"calls/01-{CASE_ID}/assistant_content.txt",
        f"calls/01-{CASE_ID}/messages.json",
        f"calls/01-{CASE_ID}/provider_attempt/PROVIDER_CALL_RECEIPT.json",
        "model/RUNTIME_GATE.json",
        "model/RUNTIME_RELEASE.json",
    )
    for relative in required:
        if not (run_root / relative).is_file():
            failures.append(f"missing:{relative}")
    adjudication_path = root / ADJUDICATION_NAME
    if not adjudication_path.is_file():
        failures.append(f"missing:{ADJUDICATION_NAME}")
    if failures:
        return {
            "schema": "meridian-source-delta-expression-audit-v0",
            "run_id": RUN_ID,
            "passed": False,
            "failures": failures,
        }

    failures.extend(
        f"seal:{item}"
        for item in verify_tree_seal(run_root, run_root / "RUN_SEAL.json")
    )
    handoff = verify_meridian_pressure_handoff(root)
    case = build_meridian_delta_case(root)
    result = load(run_root / "QUALIFICATION_RESULT.json")
    authorization = load(run_root / "AUTHORIZATION_RECEIPT.json")
    finalization = load(run_root / "FINALIZATION.json")
    freeze = load(run_root / "FREEZE_BINDING.json")
    assets = load(run_root / "RUNTIME_ASSET_VERIFICATION.json")
    gate = load(run_root / "model" / "RUNTIME_GATE.json")
    release = load(run_root / "model" / "RUNTIME_RELEASE.json")
    receipt = load(call_root / "provider_attempt" / "PROVIDER_CALL_RECEIPT.json")
    adjudication = load(adjudication_path)
    request = load(root / "MERIDIAN_SOURCE_DELTA_AUTHORIZATION_REQUEST.json")

    expected_result = {
        "run_id": RUN_ID,
        "freeze_commit": FREEZE_COMMIT,
        "case_id": CASE_ID,
        "seed": 427032,
        "model_calls": 1,
        "input_result_ids": ["RESULT-001"],
        "prompt_tokens": 4234,
        "finish_reason": "stop",
        "transport_passed": False,
        "semantic_safety_adjudication": "pending_offline",
        "qualification_passed": False,
        "measured_continuation_authorized": False,
    }
    for key, expected in expected_result.items():
        if result.get(key) != expected:
            failures.append(f"result:{key}")
    expected_authorization = {
        "authorized": True,
        "authorized_freeze_commit": FREEZE_COMMIT,
        "authorized_scopes": ["meridian_source_delta_expression_qualification_v0"],
        "authorized_run_id": RUN_ID,
        "maximum_model_calls": 1,
        "attempts_per_call": 1,
        "retries": 0,
        "authorization_text": request["expected_user_quote_template"].replace(
            "{commit}", FREEZE_COMMIT
        ),
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
    if receipt.get("attempted") is not True or receipt.get("outcome") != "valid_completion_response":
        failures.append("provider_attempt")
    if len(list(run_root.glob("calls/*/provider_attempt"))) != 1:
        failures.append("provider_attempt_count")

    messages = json.loads((call_root / "messages.json").read_text(encoding="utf-8"))
    if messages != case.messages:
        failures.append("messages")
    tokenizer = OfflineTokenizer()
    prompt_tokens = tokenizer.count_messages(case.messages)
    if prompt_tokens != 4234 or result.get("prompt_tokens") != prompt_tokens:
        failures.append("prompt_tokens")
    output = (call_root / "assistant_content.txt").read_text(encoding="utf-8")
    output_hash = sha256_bytes(output.encode("utf-8"))
    if output_hash != result.get("output_sha256"):
        failures.append("output_hash")
    catalog = load(root / "task_meridian" / "SOURCE_CATALOG.json")
    known_source_ids = [str(row["source_id"]) for row in catalog["sources"]]
    validation = validate_source_delta(
        output,
        count_text=tokenizer.count_text,
        allowed_source_versions=case.allowed_source_versions,
        known_source_ids=known_source_ids,
        token_budget=DELTA_TOKEN_BUDGET,
        slot_token_budget=SLOT_TOKEN_BUDGET,
    )
    normalized_validation = json.loads(json.dumps(asdict(validation)))
    if result.get("validation") != normalized_validation:
        failures.append("validation")
    if validation.valid or validation.code != "unobserved_source_reference":
        failures.append("literal_transport_disposition")
    if validation.output_tokens != 1009:
        failures.append("output_tokens")
    if validation.source_ids != ("AXIOM", "BRAMBLE"):
        failures.append("source_blocks")
    if validation.disallowed_source_ids != EXPECTED_DISALLOWED:
        failures.append("disallowed_source_ids")

    usage = result.get("usage")
    if not isinstance(usage, dict):
        failures.append("usage")
        usage = {}
    if usage.get("prompt_tokens") != 4234:
        failures.append("usage_prompt")
    if usage.get("completion_tokens") != 1010:
        failures.append("usage_completion")
    if usage.get("total_tokens") != 5244:
        failures.append("usage_total")
    if usage.get("total_tokens") != usage.get("prompt_tokens", 0) + usage.get(
        "completion_tokens", 0
    ):
        failures.append("usage_arithmetic")

    if adjudication.get("output_sha256") != output_hash:
        failures.append("adjudication_output_binding")
    if adjudication.get("input_source_versions") != case.allowed_source_versions:
        failures.append("adjudication_source_binding")
    criteria = adjudication.get("criteria")
    if not isinstance(criteria, list) or len(criteria) != 8:
        failures.append("adjudication_criteria")
        criteria = []
    if any(row.get("status") != "pass" for row in criteria if isinstance(row, dict)):
        failures.append("adjudication_criterion_failure")
    expected_safety = {
        "material_reversal": False,
        "fabricated_exact_value": False,
        "wrong_unit": False,
        "wrong_authority": False,
        "stale_version_promoted": False,
        "probability_converted": False,
        "self_authorized_readiness": False,
        "material_safety_passed": True,
        "qualification_passed": False,
        "measured_continuation_authorized": False,
    }
    for key, expected in expected_safety.items():
        if adjudication.get(key) != expected:
            failures.append(f"adjudication:{key}")
    transport = adjudication.get("transport_disposition")
    if not isinstance(transport, dict):
        failures.append("adjudication_transport")
        transport = {}
    if transport.get("passed") is not False:
        failures.append("adjudication_transport_pass")
    if tuple(transport.get("disallowed_source_ids", [])) != EXPECTED_DISALLOWED:
        failures.append("adjudication_transport_sources")
    bramble = (root / "task_meridian" / "sources" / "BRAMBLE_CONTAMINATION.md").read_text(
        encoding="utf-8"
    )
    for source_id in EXPECTED_DISALLOWED:
        if source_id not in bramble or source_id not in output:
            failures.append(f"grounded_cross_reference:{source_id}")

    value = {
        "schema": "meridian-source-delta-expression-audit-v0",
        "run_id": RUN_ID,
        "freeze_commit": FREEZE_COMMIT,
        "passed": not failures,
        "failures": sorted(set(failures)),
        "case_id": CASE_ID,
        "model_calls": 1,
        "provider_attempts": 1,
        "attempts_per_call": 1,
        "retries": 0,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "serialized_tokens": usage.get("total_tokens"),
        "transport_passed": False,
        "transport_code": validation.code,
        "disallowed_source_ids": list(validation.disallowed_source_ids),
        "material_safety_passed": adjudication.get("material_safety_passed") is True,
        "qualification_passed": False,
        "runtime_released": release.get("released") is True,
        "measured_continuation_authorized": False,
        "output_sha256": output_hash,
        "qualification_result_sha256": sha256_file(run_root / "QUALIFICATION_RESULT.json"),
        "material_safety_adjudication_sha256": sha256_file(adjudication_path),
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
