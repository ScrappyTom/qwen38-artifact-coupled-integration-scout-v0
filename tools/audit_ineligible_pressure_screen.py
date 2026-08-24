from __future__ import annotations

import json
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
from reactive_runtime.seal import verify_tree_seal
from reactive_runtime.world import ArchitectureWorld
from tools import run_pressure_screen as runner
from tools.offline_tokenizer import OfflineTokenizer


RUN_ROOT = ROOT / "runs" / runner.RUN_ID
OUTPUT = ROOT / "NORTHSTAR_PRESSURE_SCREEN_DISPOSITION.json"
AUTHORIZED_FREEZE = "40272d6cc0c5aa2eda7bb5df9394ff02d767829d"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(*, write_output: bool = True) -> dict[str, Any]:
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
        if not (RUN_ROOT / relative).is_file():
            failures.append(f"missing:{relative}")
    if failures:
        value = {
            "schema": "northstar-ineligible-pressure-screen-disposition-v0",
            "mechanical_integrity_passed": False,
            "failures": failures,
        }
        if write_output:
            write_json(OUTPUT, value)
        return value

    failures.extend(f"seal:{item}" for item in verify_tree_seal(RUN_ROOT, RUN_ROOT / "RUN_SEAL.json"))
    result = load(RUN_ROOT / "SCREEN_RESULT.json")
    trace = load(RUN_ROOT / "CALL_TRACE.json")
    boundary = load(RUN_ROOT / "PRESSURE_BOUNDARY.json")
    messages = load(RUN_ROOT / "FINAL_MESSAGES.json")
    ledger_value = load(RUN_ROOT / "RESULT_LEDGER.json")
    authorization = load(RUN_ROOT / "AUTHORIZATION_RECEIPT.json")
    binding = load(RUN_ROOT / "FREEZE_BINDING.json")
    finalization = load(RUN_ROOT / "FINALIZATION.json")
    release = load(RUN_ROOT / "model" / "RUNTIME_RELEASE.json")
    runtime_gate = load(RUN_ROOT / "model" / "RUNTIME_GATE.json")
    runtime_assets = load(RUN_ROOT / "RUNTIME_ASSET_VERIFICATION.json")

    task_lock_sha256 = sha256_file(ROOT / "task" / "TASK_SOURCE_LOCK.json")
    expected_result = {
        "freeze_commit": AUTHORIZED_FREEZE,
        "run_id": runner.RUN_ID,
        "seed": runner.SEED,
        "actor_calls": 2,
        "terminal_disposition": "pressure_boundary_ineligible",
        "pressure_qualified": False,
        "candidate_submitted": False,
    }
    for key, expected in expected_result.items():
        if result.get(key) != expected:
            failures.append(f"result:{key}")
    expected_authorization = {
        "authorized": True,
        "authorized_freeze_commit": AUTHORIZED_FREEZE,
        "authorized_scopes": [runner.SCOPE],
        "authorized_run_id": runner.RUN_ID,
        "maximum_model_calls": runner.MAX_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, expected in expected_authorization.items():
        if authorization.get(key) != expected:
            failures.append(f"authorization:{key}")
    if binding.get("commit") != AUTHORIZED_FREEZE or binding.get("task_source_lock_sha256") != task_lock_sha256:
        failures.append("freeze_binding")
    if runtime_gate.get("passed") is not True or runtime_assets.get("passed") is not True:
        failures.append("runtime_gate_or_assets")
    if release.get("released") is not True or finalization.get("release", {}).get("released") is not True:
        failures.append("runtime_release")
    if finalization.get("failure") is not None:
        failures.append("runtime_failure")

    if not isinstance(trace, list) or len(trace) != 2:
        failures.append("trace:length")
        trace = []
    serialized_tokens = 0
    for ordinal, row in enumerate(trace, 1):
        if row.get("actor_call") != ordinal or row.get("finish_reason") != "stop":
            failures.append(f"trace:{ordinal}:shape")
        usage = row.get("usage", {})
        prompt = usage.get("prompt_tokens")
        completion = usage.get("completion_tokens")
        total = usage.get("total_tokens")
        if not all(type(item) is int and item >= 0 for item in (prompt, completion, total)) or prompt + completion != total:
            failures.append(f"trace:{ordinal}:usage")
        else:
            serialized_tokens += total
        if row.get("candidate_sha256_before") != row.get("candidate_sha256_after"):
            failures.append(f"trace:{ordinal}:candidate_changed")
        if row.get("rejection_code") is not None or row.get("result_kind") != "source_observation":
            failures.append(f"trace:{ordinal}:action_result")
        attempt = RUN_ROOT / "actor" / f"call-{ordinal:03d}" / "provider_attempt" / "PROVIDER_CALL_RECEIPT.json"
        receipt = load(attempt)
        if receipt.get("attempted") is not True or receipt.get("outcome") != "valid_completion_response":
            failures.append(f"provider:{ordinal}")
    if serialized_tokens != 17_418 or result.get("serialized_tokens") != serialized_tokens:
        failures.append("serialized_tokens")

    if boundary.get("messages") != messages or boundary.get("result_ledger") != ledger_value:
        failures.append("boundary:custody")
    prospective = OfflineTokenizer().count_messages(messages)
    if prospective != 25_705 or boundary.get("ordinary_prospective_prompt_tokens") != prospective:
        failures.append("boundary:token_recount")
    if boundary.get("overflow_tokens") != 4_713 or boundary.get("prompt_limit") != runner.PROMPT_LIMIT:
        failures.append("boundary:arithmetic")
    if boundary.get("eligibility_failures") != ["fewer_than_four_source_observations_delivered"]:
        failures.append("boundary:eligibility_class")

    ledger = ResultLedger.from_dict(ledger_value)
    pending_id = str(boundary.get("pending_result_id"))
    pending = ledger.get(pending_id)
    delivered = [row for row in ledger.records() if row.result_kind == "source_observation" and row.previously_visible]
    delivered_source_ids = sorted({source for row in delivered for source in row.metadata.get("source_ids", [])})
    pending_source_ids = sorted(set(pending.metadata.get("source_ids", [])))
    if pending.previously_visible or len(delivered) != 1 or delivered_source_ids != ["S01", "S02", "S03"]:
        failures.append("boundary:delivered_evidence")
    if pending_source_ids != ["S04", "S05", "S06"]:
        failures.append("boundary:pending_evidence")
    relief = positive_savings_first_fit_step(
        messages=deepcopy(messages),
        ledger=ResultLedger.from_dict(ledger_value),
        prompt_limit=runner.PROMPT_LIMIT,
        count_messages=OfflineTokenizer().count_messages,
        protected_result_ids=(pending_id,),
    )
    if list(relief.selected_result_ids) != ["RESULT-001"] or relief.prompt_tokens != 14_654:
        failures.append("boundary:positive_relief")

    with tempfile.TemporaryDirectory() as temporary:
        initial = ArchitectureWorld(ROOT / "task", Path(temporary)).candidate_sha256
    if result.get("candidate_sha256") != initial or boundary.get("candidate_sha256") != initial:
        failures.append("candidate_identity")

    qualification_audit = load(ROOT / "NORTHSTAR_PRESSURE_SCREEN_AUDIT.json")
    apparatus_defects = []
    if "task_source_lock_sha256" not in result:
        apparatus_defects.append(
            "frozen runner omitted task_source_lock_sha256 from SCREEN_RESULT even though the frozen auditor requires it; the exact lock remains verified in FREEZE_BINDING"
        )
    value = {
        "schema": "northstar-ineligible-pressure-screen-disposition-v0",
        "run_id": runner.RUN_ID,
        "authorized_freeze_commit": AUTHORIZED_FREEZE,
        "mechanical_integrity_passed": not failures,
        "failures": failures,
        "provider_calls": len(trace),
        "attempts_per_call": 1,
        "retries": 0,
        "serialized_tokens": serialized_tokens,
        "pressure_observed": True,
        "ordinary_prospective_prompt_tokens": prospective,
        "prompt_limit": runner.PROMPT_LIMIT,
        "overflow_tokens": prospective - runner.PROMPT_LIMIT,
        "delivered_source_observation_objects": len(delivered),
        "delivered_source_ids": delivered_source_ids,
        "pending_result_id": pending_id,
        "pending_source_ids": pending_source_ids,
        "pending_result_delivered": pending.previously_visible,
        "positive_relief_feasible": bool(relief.selected_result_ids),
        "positive_relief_result_ids": list(relief.selected_result_ids),
        "positive_relief_after_tokens": relief.prompt_tokens,
        "scientific_boundary_qualified": False,
        "scientific_ineligibility_reason": "the frozen gate required at least four previously delivered source-observation result objects; only one batch result object covering S01-S03 had crossed a later actor boundary",
        "measured_fork_eligible": False,
        "measured_fork_authorized": False,
        "task_selection_disposition": "closed_non_diagnostic_under_frozen_stage0_rule",
        "original_qualification_audit_passed": qualification_audit.get("passed") is True,
        "original_qualification_audit_sha256": sha256_file(ROOT / "NORTHSTAR_PRESSURE_SCREEN_AUDIT.json"),
        "apparatus_defects": apparatus_defects,
        "run_seal_sha256": sha256_file(RUN_ROOT / "RUN_SEAL.json"),
        "screen_result_sha256": sha256_file(RUN_ROOT / "SCREEN_RESULT.json"),
        "claim_limit": "The sealed run proves an authentic early overflow and a mechanically feasible positive relief step. It does not satisfy the frozen meaningful-acquisition gate, create a D0/A1 fork, or authorize a retry or measured continuation.",
    }
    if write_output:
        write_json(OUTPUT, value)
    return value


def main() -> int:
    value = audit()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value["mechanical_integrity_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
