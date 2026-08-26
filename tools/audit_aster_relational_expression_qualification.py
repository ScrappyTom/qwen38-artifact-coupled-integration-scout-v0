from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.aster_boundary import verify_aster_pressure_handoff  # noqa: E402
from reactive_runtime.aster_qualification import build_aster_relational_case  # noqa: E402
from reactive_runtime.canonical import sha256_bytes, sha256_file  # noqa: E402
from reactive_runtime.provenance_claims import (  # noqa: E402
    NON_AUTHORITATIVE_DERIVATIVE,
    OWNER_SOURCE_REPORTED,
    SOURCE_REPORTED_FACT,
)
from reactive_runtime.relational_delta import (  # noqa: E402
    CLAIM_HEADING,
    validate_relational_delta,
)
from reactive_runtime.seal import verify_tree_seal  # noqa: E402
from tools.offline_tokenizer import OfflineTokenizer  # noqa: E402


RUN_ID = "2026-08-26-aster-relational-expression-qualification-v0"
FREEZE_COMMIT = "8aa9afbec32b5669755760f2d4d7b5c992150e05"
CASE_ID = "Q1_FIRST_ACTUAL_SOURCE_EXTERNALIZATION"
ADJUDICATION_NAME = "ASTER_RELATIONAL_EXPRESSION_MATERIAL_SAFETY_ADJUDICATION.json"
AUDIT_NAME = "ASTER_RELATIONAL_EXPRESSION_QUALIFICATION_AUDIT.json"
EXPECTED_RAW_CLAIMS = {
    "ANCHOR-001": ("ANCHOR", 5),
    "ANCHOR-002": ("ANCHOR", 5),
    "BRIDGE-001": ("BRIDGE", 5),
    "BRIDGE-002": ("BRIDGE", 6),
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def parse_raw_claims(text: str) -> dict[str, dict[str, str]]:
    matches = list(CLAIM_HEADING.finditer(text))
    result: dict[str, dict[str, str]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        fields: dict[str, str] = {}
        for line in text[match.end() : end].strip().splitlines():
            if ": " in line:
                key, value = line.split(": ", 1)
                fields[key] = value.strip()
        result[match.group(1)] = fields
    return result


def audit(repository_root: Path = ROOT) -> dict[str, Any]:
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
            "schema": "aster-relational-expression-audit-v0",
            "run_id": RUN_ID,
            "passed": False,
            "failures": failures,
        }

    failures.extend(
        f"seal:{item}" for item in verify_tree_seal(run_root, run_root / "RUN_SEAL.json")
    )
    handoff = verify_aster_pressure_handoff(root)
    case = build_aster_relational_case(root)
    result = load(run_root / "QUALIFICATION_RESULT.json")
    call_result = load(call_root / "RESULT.json")
    authorization = load(run_root / "AUTHORIZATION_RECEIPT.json")
    finalization = load(run_root / "FINALIZATION.json")
    freeze = load(run_root / "FREEZE_BINDING.json")
    assets = load(run_root / "RUNTIME_ASSET_VERIFICATION.json")
    gate = load(run_root / "model" / "RUNTIME_GATE.json")
    release = load(run_root / "model" / "RUNTIME_RELEASE.json")
    receipt = load(call_root / "provider_attempt" / "PROVIDER_CALL_RECEIPT.json")
    adjudication = load(adjudication_path)
    request = load(root / "ASTER_RELATIONAL_EXPRESSION_AUTHORIZATION_REQUEST.json")

    if call_result != result:
        failures.append("call_result")
    expected_result = {
        "run_id": RUN_ID,
        "freeze_commit": FREEZE_COMMIT,
        "case_id": CASE_ID,
        "seed": 531702,
        "model_calls": 1,
        "input_result_ids": ["RESULT-001"],
        "input_source_ids": ["ANCHOR", "BRIDGE"],
        "prompt_tokens": 4428,
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
        "authorized_scopes": ["aster_relational_expression_qualification_v0"],
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
    if release.get("active_llama_server_pids_after") != []:
        failures.append("runtime_process_cleanup")
    if finalization.get("failure") is not None:
        failures.append("finalization_failure")
    if finalization.get("release") != release:
        failures.append("finalization_release")
    if (run_root / "RUN_FAILURE.json").exists():
        failures.append("run_failure_present")
    if receipt.get("attempted") is not True or receipt.get("outcome") != "valid_completion_response":
        failures.append("provider_attempt")
    provider_attempts = len(list(run_root.glob("calls/*/provider_attempt")))
    if provider_attempts != 1:
        failures.append("provider_attempt_count")

    messages = json.loads((call_root / "messages.json").read_text(encoding="utf-8"))
    if messages != case.messages:
        failures.append("messages")
    tokenizer = OfflineTokenizer()
    prompt_tokens = tokenizer.count_messages(case.messages)
    if prompt_tokens != 4428 or result.get("prompt_tokens") != prompt_tokens:
        failures.append("prompt_tokens")
    output = (call_root / "assistant_content.txt").read_text(encoding="utf-8")
    output_hash = sha256_bytes(output.encode("utf-8"))
    if output_hash != result.get("output_sha256"):
        failures.append("output_hash")

    catalog = load(root / "task_aster" / "SOURCE_CATALOG.json")
    source_catalog = {str(row["source_id"]): row for row in catalog["sources"]}
    validation = validate_relational_delta(
        output,
        count_text=tokenizer.count_text,
        source_catalog=source_catalog,
        task_root=root / "task_aster",
        newly_externalized=case.records,
        current_source_versions=case.source_versions,
    )
    normalized_validation = json.loads(json.dumps(asdict(validation)))
    if result.get("validation") != normalized_validation:
        failures.append("validation")
    if validation.valid or validation.code != "evidence_quote_not_unique_exact_line":
        failures.append("literal_transport_disposition")
    if validation.output_tokens != 707:
        failures.append("output_tokens")
    if validation.claims or validation.source_ids or validation.provenance:
        failures.append("unexpected_admitted_claim")
    if validation.issues != (
        "evidence_quote_not_unique_exact_line",
        "externalized_source_unrepresented:ANCHOR",
        "externalized_source_unrepresented:BRIDGE",
    ):
        failures.append("transport_issues")

    raw_claims = parse_raw_claims(output)
    if set(raw_claims) != set(EXPECTED_RAW_CLAIMS):
        failures.append("raw_claim_ids")
    source_lines: dict[str, list[str]] = {}
    for source_id in ("ANCHOR", "BRIDGE"):
        path = root / "task_aster" / str(source_catalog[source_id]["path"])
        source_lines[source_id] = path.read_text(encoding="utf-8").splitlines()
    expected_fields = {
        "SLOT_SOURCE",
        "SOURCE_VERSION",
        "EVIDENCE_RESULT",
        "EVIDENCE_QUOTE",
        "MODE",
        "ATTRIBUTION",
        "REFERENTS",
        "AUTHORITY",
        "STATEMENT",
    }
    for claim_id, (source_id, line_number) in EXPECTED_RAW_CLAIMS.items():
        fields = raw_claims.get(claim_id, {})
        if set(fields) != expected_fields:
            failures.append(f"raw_claim_fields:{claim_id}")
            continue
        expected_version = case.source_versions[source_id]
        expected_values = {
            "SLOT_SOURCE": source_id,
            "SOURCE_VERSION": expected_version,
            "EVIDENCE_RESULT": "RESULT-001",
            "MODE": SOURCE_REPORTED_FACT,
            "ATTRIBUTION": OWNER_SOURCE_REPORTED,
            "REFERENTS": "NONE",
            "AUTHORITY": NON_AUTHORITATIVE_DERIVATIVE,
        }
        for field, expected in expected_values.items():
            if fields.get(field) != expected:
                failures.append(f"raw_claim:{claim_id}:{field}")
        quote = fields["EVIDENCE_QUOTE"]
        containing = [
            index
            for index, line in enumerate(source_lines[source_id], start=1)
            if quote in line
        ]
        if containing != [line_number]:
            failures.append(f"quote_containment:{claim_id}")
        if quote == source_lines[source_id][line_number - 1]:
            failures.append(f"quote_unexpectedly_complete:{claim_id}")

    usage = result.get("usage")
    if not isinstance(usage, dict):
        failures.append("usage")
        usage = {}
    if usage.get("prompt_tokens") != 4428:
        failures.append("usage_prompt")
    if usage.get("completion_tokens") != 708:
        failures.append("usage_completion")
    if usage.get("total_tokens") != 5136:
        failures.append("usage_total")
    if usage.get("total_tokens") != usage.get("prompt_tokens", 0) + usage.get(
        "completion_tokens", 0
    ):
        failures.append("usage_arithmetic")

    if adjudication.get("output_sha256") != output_hash:
        failures.append("adjudication_output_binding")
    if adjudication.get("input_source_versions") != {
        source_id: case.source_versions[source_id] for source_id in case.input_source_ids
    }:
        failures.append("adjudication_source_binding")
    if adjudication.get("raw_claim_count") != 4:
        failures.append("adjudication_raw_claim_count")
    if adjudication.get("mechanically_admitted_claim_count") != 0:
        failures.append("adjudication_admitted_claim_count")
    criteria = adjudication.get("criteria")
    if not isinstance(criteria, list) or len(criteria) != 8:
        failures.append("adjudication_criteria")
        criteria = []
    allowed_statuses = {"pass", "pass_with_omission", "omitted"}
    if any(
        not isinstance(row, dict) or row.get("status") not in allowed_statuses
        for row in criteria
    ):
        failures.append("adjudication_criterion_status")
    flags = adjudication.get("automatic_failure_flags")
    if not isinstance(flags, dict) or any(value is not False for value in flags.values()):
        failures.append("adjudication_automatic_failure")
    expected_adjudication = {
        "raw_output_material_safety_passed": True,
        "admission_based_relevance_gate_passed": False,
        "material_safety_passed": True,
        "qualification_passed": False,
        "measured_continuation_authorized": False,
    }
    for key, expected in expected_adjudication.items():
        if adjudication.get(key) != expected:
            failures.append(f"adjudication:{key}")
    transport = adjudication.get("transport_disposition")
    if not isinstance(transport, dict):
        failures.append("adjudication_transport")
        transport = {}
    if transport.get("passed") is not False or transport.get("code") != validation.code:
        failures.append("adjudication_transport_disposition")
    if len(transport.get("quote_failures", [])) != 4:
        failures.append("adjudication_quote_failures")

    return {
        "schema": "aster-relational-expression-audit-v0",
        "run_id": RUN_ID,
        "freeze_commit": FREEZE_COMMIT,
        "passed": not failures,
        "failures": sorted(set(failures)),
        "case_id": CASE_ID,
        "model_calls": 1,
        "provider_attempts": provider_attempts,
        "attempts_per_call": 1,
        "retries": 0,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "serialized_tokens": usage.get("total_tokens"),
        "output_tokens": validation.output_tokens,
        "raw_claim_count": len(raw_claims),
        "mechanically_admitted_claim_count": len(validation.claims),
        "transport_passed": False,
        "transport_code": validation.code,
        "raw_output_material_safety_passed": adjudication.get(
            "raw_output_material_safety_passed"
        )
        is True,
        "admission_based_relevance_gate_passed": adjudication.get(
            "admission_based_relevance_gate_passed"
        )
        is True,
        "qualification_passed": False,
        "runtime_released": release.get("released") is True,
        "measured_continuation_authorized": False,
        "output_sha256": output_hash,
        "qualification_result_sha256": sha256_file(
            run_root / "QUALIFICATION_RESULT.json"
        ),
        "material_safety_adjudication_sha256": sha256_file(adjudication_path),
        "run_seal_sha256": sha256_file(run_root / "RUN_SEAL.json"),
    }


def main() -> int:
    value = audit()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
