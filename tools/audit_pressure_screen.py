from __future__ import annotations

import json
import re
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json  # noqa: E402
from reactive_runtime.policy import positive_savings_first_fit_step  # noqa: E402
from reactive_runtime.records import ResultLedger  # noqa: E402
from reactive_runtime.seal import verify_tree_seal  # noqa: E402
from reactive_runtime.world import ArchitectureWorld  # noqa: E402
from tools.offline_tokenizer import OfflineTokenizer  # noqa: E402
from tools import run_pressure_screen as runner  # noqa: E402


AUDIT_NAME = "NORTHSTAR_PRESSURE_SCREEN_AUDIT.json"
HANDOFF_NAME = "NORTHSTAR_PRESSURE_BOUNDARY_HANDOFF.json"
TASK_ID = "northstar-migration-architecture-package-v0"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(repository_root: Path = ROOT, *, write_outputs: bool = True) -> dict[str, Any]:
    root = repository_root.resolve()
    run_root = root / "runs" / runner.RUN_ID
    failures: list[str] = []
    required = (
        "AUTHORIZATION_RECEIPT.json",
        "CALL_TRACE.json",
        "FINALIZATION.json",
        "FINAL_MESSAGES.json",
        "FREEZE_BINDING.json",
        "PRESSURE_BOUNDARY.json",
        "RESULT_LEDGER.json",
        "RUN_SEAL.json",
        "RUNTIME_ASSET_VERIFICATION.json",
        "SCREEN_RESULT.json",
        "model/RUNTIME_GATE.json",
        "model/RUNTIME_RELEASE.json",
    )
    for relative in required:
        if not (run_root / relative).is_file():
            failures.append(f"missing:{relative}")
    if failures:
        return {
            "schema": "northstar-pressure-screen-audit-v0",
            "run_id": runner.RUN_ID,
            "passed": False,
            "failures": failures,
            "measured_fork_authorized": False,
        }

    failures.extend(
        f"seal:{item}"
        for item in verify_tree_seal(run_root, run_root / "RUN_SEAL.json")
    )
    result = load(run_root / "SCREEN_RESULT.json")
    trace = load(run_root / "CALL_TRACE.json")
    boundary = load(run_root / "PRESSURE_BOUNDARY.json")
    final_messages = load(run_root / "FINAL_MESSAGES.json")
    ledger_value = load(run_root / "RESULT_LEDGER.json")
    authorization = load(run_root / "AUTHORIZATION_RECEIPT.json")
    finalization = load(run_root / "FINALIZATION.json")
    freeze_binding = load(run_root / "FREEZE_BINDING.json")
    runtime_gate = load(run_root / "model" / "RUNTIME_GATE.json")
    runtime_release = load(run_root / "model" / "RUNTIME_RELEASE.json")
    runtime_assets = load(run_root / "RUNTIME_ASSET_VERIFICATION.json")

    freeze_commit = result.get("freeze_commit")
    if not isinstance(freeze_commit, str) or re.fullmatch(r"[0-9a-f]{40}", freeze_commit) is None:
        failures.append("result:freeze_commit")
    expected_result = {
        "schema": "northstar-transfer-pressure-screen-result-v0",
        "task_id": TASK_ID,
        "task_source_lock_sha256": sha256_file(root / "task" / "TASK_SOURCE_LOCK.json"),
        "run_id": runner.RUN_ID,
        "seed": runner.SEED,
        "terminal_disposition": "authentic_result_delivery_pressure",
        "pressure_qualified": True,
        "candidate_submitted": False,
    }
    for key, expected in expected_result.items():
        if result.get(key) != expected:
            failures.append(f"result:{key}")
    actor_calls = result.get("actor_calls")
    if type(actor_calls) is not int or not 1 <= actor_calls <= runner.MAX_CALLS:
        failures.append("result:actor_calls")
        actor_calls = 0
    expected_authorization = {
        "authorized": True,
        "authorized_freeze_commit": freeze_commit,
        "authorized_scopes": [runner.SCOPE],
        "authorized_run_id": runner.RUN_ID,
        "maximum_model_calls": runner.MAX_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, expected in expected_authorization.items():
        if authorization.get(key) != expected:
            failures.append(f"authorization:{key}")
    expected_freeze_binding = {
        "schema": "northstar-pressure-screen-freeze-binding-v0",
        "commit": freeze_commit,
        "run_id": runner.RUN_ID,
        "task_source_lock_sha256": sha256_file(root / "task" / "TASK_SOURCE_LOCK.json"),
        "model_profile_lock_sha256": sha256_file(root / "MODEL_PROFILE_LOCK.json"),
        "screen_contract_sha256": sha256_file(root / "PRESSURE_SCREEN_CONTRACT.json"),
    }
    for key, expected in expected_freeze_binding.items():
        if freeze_binding.get(key) != expected:
            failures.append(f"freeze_binding:{key}")
    if runtime_gate.get("passed") is not True:
        failures.append("runtime_gate")
    if runtime_assets.get("passed") is not True:
        failures.append("runtime_assets")
    if runtime_release.get("released") is not True:
        failures.append("runtime_release")
    if finalization.get("failure") is not None:
        failures.append("finalization:failure")
    if finalization.get("release", {}).get("released") is not True:
        failures.append("finalization:release")
    for forbidden in ("RUN_FAILURE.json", "BUDGET_STOP.json"):
        if (run_root / forbidden).exists():
            failures.append(f"forbidden:{forbidden}")

    if not isinstance(trace, list) or len(trace) != actor_calls:
        failures.append("trace:length")
        trace = []
    serialized = 0
    for ordinal, row in enumerate(trace, 1):
        if not isinstance(row, dict) or row.get("actor_call") != ordinal:
            failures.append(f"trace:{ordinal}:ordinal")
            continue
        if row.get("finish_reason") != "stop":
            failures.append(f"trace:{ordinal}:finish_reason")
        usage = row.get("usage")
        if not isinstance(usage, dict):
            failures.append(f"trace:{ordinal}:usage")
            continue
        prompt = usage.get("prompt_tokens")
        completion = usage.get("completion_tokens")
        total = usage.get("total_tokens")
        if not all(type(value) is int and value >= 0 for value in (prompt, completion, total)):
            failures.append(f"trace:{ordinal}:usage_values")
        elif prompt + completion != total:
            failures.append(f"trace:{ordinal}:usage_arithmetic")
        else:
            serialized += total
        if row.get("candidate_sha256_before") != row.get("candidate_sha256_after"):
            failures.append(f"trace:{ordinal}:candidate_effect")
        parsed = row.get("parsed_action")
        if isinstance(parsed, dict) and parsed.get("action") in {
            "replace_evidence_ledger",
            "upsert_decision_section",
            "replace_decision",
            "run_check",
            "submit",
        }:
            failures.append(f"trace:{ordinal}:pretreatment_action")
    if serialized != result.get("serialized_tokens"):
        failures.append("trace:serialized_total")
    attempt_roots = sorted(run_root.glob("actor/call-*/provider_attempt"))
    if len(attempt_roots) != actor_calls:
        failures.append("provider_attempts")
    for attempt_root in attempt_roots:
        receipt_path = attempt_root / "PROVIDER_CALL_RECEIPT.json"
        if not receipt_path.is_file():
            failures.append(f"provider_receipt:{attempt_root.name}")
            continue
        receipt = load(receipt_path)
        if receipt.get("attempted") is not True or receipt.get("outcome") != "valid_completion_response":
            failures.append(f"provider_outcome:{attempt_root.name}")

    if boundary.get("schema") != "northstar-authentic-pressure-boundary-v0":
        failures.append("boundary:schema")
    if boundary.get("task_id") != TASK_ID:
        failures.append("boundary:task_id")
    if boundary.get("eligibility_failures") != []:
        failures.append("boundary:eligibility")
    if boundary.get("actor_calls_completed") != actor_calls:
        failures.append("boundary:actor_calls")
    if boundary.get("messages") != final_messages:
        failures.append("boundary:messages")
    if boundary.get("result_ledger") != ledger_value:
        failures.append("boundary:ledger")
    prospective = boundary.get("ordinary_prospective_prompt_tokens")
    if type(prospective) is not int or prospective <= runner.PROMPT_LIMIT:
        failures.append("boundary:prospective_prompt_tokens")
        prospective = 0
    if boundary.get("prompt_limit") != runner.PROMPT_LIMIT:
        failures.append("boundary:prompt_limit")
    if boundary.get("overflow_tokens") != prospective - runner.PROMPT_LIMIT:
        failures.append("boundary:overflow")
    if result.get("boundary", {}).get("ordinary_prospective_prompt_tokens") != prospective:
        failures.append("result:boundary_summary")
    try:
        rendered_count = OfflineTokenizer().count_messages(final_messages)
        if rendered_count != prospective:
            failures.append("boundary:offline_token_recount")
    except Exception as exc:  # pragma: no cover
        failures.append(f"boundary:tokenizer:{type(exc).__name__}")

    relief_selected: list[str] = []
    relief_after_tokens: int | None = None
    delivered_sources = 0
    pending_id = boundary.get("pending_result_id")
    try:
        ledger = ResultLedger.from_dict(ledger_value)
        pending = ledger.get(str(pending_id))
        if pending.result_kind != "source_observation":
            failures.append("boundary:pending_kind")
        if pending.previously_visible:
            failures.append("boundary:pending_delivered")
        delivered_sources = sum(
            row.result_kind == "source_observation" and row.previously_visible
            for row in ledger.records()
        )
        if delivered_sources < 4 or boundary.get("delivered_source_observations") != delivered_sources:
            failures.append("boundary:delivered_sources")
        relief = positive_savings_first_fit_step(
            messages=deepcopy(final_messages),
            ledger=ResultLedger.from_dict(ledger_value),
            prompt_limit=runner.PROMPT_LIMIT,
            count_messages=OfflineTokenizer().count_messages,
            protected_result_ids=(str(pending_id),),
        )
        relief_selected = list(relief.selected_result_ids)
        relief_after_tokens = relief.prompt_tokens
        if not relief_selected:
            failures.append("interaction_activation:no_positive_relief")
    except Exception as exc:
        failures.append(f"boundary:ledger_or_relief:{type(exc).__name__}")

    with tempfile.TemporaryDirectory() as temporary:
        world = ArchitectureWorld(root / "task", Path(temporary))
        initial_hash = world.candidate_sha256
        if boundary.get("candidate_sha256") != initial_hash:
            failures.append("boundary:candidate_hash")
        if boundary.get("candidate_packet") != world.candidate_packet():
            failures.append("boundary:candidate_packet")
        if result.get("candidate_sha256") != initial_hash:
            failures.append("result:candidate_hash")

    audit_value = {
        "schema": "northstar-pressure-screen-audit-v0",
        "run_id": runner.RUN_ID,
        "freeze_commit": freeze_commit,
        "task_id": TASK_ID,
        "actor_calls": actor_calls,
        "provider_attempts": len(attempt_roots),
        "serialized_tokens": serialized,
        "ordinary_prospective_prompt_tokens": prospective,
        "prompt_limit": runner.PROMPT_LIMIT,
        "overflow_tokens": prospective - runner.PROMPT_LIMIT,
        "pending_result_id": pending_id,
        "pending_result_delivered": False,
        "delivered_source_observations": delivered_sources,
        "positive_relief_result_ids": relief_selected,
        "positive_relief_after_tokens": relief_after_tokens,
        "interaction_trigger_qualified": bool(relief_selected),
        "runtime_released": runtime_release.get("released") is True,
        "measured_fork_authorized": False,
        "passed": not failures,
        "failures": sorted(set(failures)),
    }
    if write_outputs:
        write_json(root / AUDIT_NAME, audit_value)
        if audit_value["passed"]:
            handoff = {
                "schema_version": "northstar-pressure-boundary-handoff-v0",
                "status": "passed_authentic_pressure_boundary",
                "run_id": runner.RUN_ID,
                "run_root": str(run_root.relative_to(root)).replace("\\", "/"),
                "task_id": TASK_ID,
                "task_source_lock_sha256": sha256_file(root / "task" / "TASK_SOURCE_LOCK.json"),
                "freeze_commit": freeze_commit,
                "actor_calls": actor_calls,
                "provider_attempts": len(attempt_roots),
                "attempts_per_call": 1,
                "retries": 0,
                "pressure_qualified": True,
                "interaction_trigger_qualified": True,
                "positive_relief_result_ids": relief_selected,
                "positive_relief_after_tokens": relief_after_tokens,
                "ordinary_prospective_prompt_tokens": prospective,
                "prompt_limit": runner.PROMPT_LIMIT,
                "overflow_tokens": prospective - runner.PROMPT_LIMIT,
                "pending_result_id": pending_id,
                "pending_result_delivered": False,
                "delivered_source_observations": delivered_sources,
                "candidate_sha256": boundary.get("candidate_sha256"),
                "candidate_changed": False,
                "candidate_submitted": False,
                "serialized_tokens": serialized,
                "runtime_released": True,
                "measured_fork_authorized": False,
                "screen_result_sha256": sha256_file(run_root / "SCREEN_RESULT.json"),
                "pressure_boundary_sha256": sha256_file(run_root / "PRESSURE_BOUNDARY.json"),
                "final_messages_sha256": sha256_file(run_root / "FINAL_MESSAGES.json"),
                "result_ledger_sha256": sha256_file(run_root / "RESULT_LEDGER.json"),
                "run_seal_sha256": sha256_file(run_root / "RUN_SEAL.json"),
                "screen_audit_sha256": sha256_file(root / AUDIT_NAME),
                "claim_limit": "This handoff qualifies one exact pre-treatment pressure fork with a positive deterministic relief trigger. It does not establish either interaction system's utility and does not authorize measured continuation.",
            }
            write_json(root / HANDOFF_NAME, handoff)
    return audit_value


def main() -> int:
    result = audit()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
