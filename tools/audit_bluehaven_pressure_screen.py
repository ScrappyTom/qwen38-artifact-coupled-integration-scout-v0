from __future__ import annotations

import json
import re
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.activation import boundary_eligibility_failures  # noqa: E402
from reactive_runtime.canonical import sha256_bytes, sha256_file, write_json  # noqa: E402
from reactive_runtime.policy import positive_savings_first_fit_step  # noqa: E402
from reactive_runtime.records import ResultLedger  # noqa: E402
from reactive_runtime.seal import verify_tree_seal  # noqa: E402
from reactive_runtime.world import ArchitectureWorld  # noqa: E402
from tools import run_bluehaven_pressure_screen as runner  # noqa: E402
from tools.offline_tokenizer import OfflineTokenizer  # noqa: E402


TASK = ROOT / "task_bluehaven"
TASK_ID = "bluehaven-water-restoration-package-v0"
AUDIT_NAME = "BLUEHAVEN_PRESSURE_SCREEN_AUDIT.json"
HANDOFF_NAME = "BLUEHAVEN_PRESSURE_BOUNDARY_HANDOFF.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relief_audit(
    *,
    messages: list[dict[str, str]],
    ledger_value: dict[str, Any],
    pending_result_id: str,
    tokenizer: OfflineTokenizer,
) -> tuple[list[str], int]:
    candidate_messages = deepcopy(messages)
    candidate_ledger = ResultLedger.from_dict(ledger_value)
    selected: list[str] = []
    prompt_tokens = tokenizer.count_messages(candidate_messages)
    while prompt_tokens > runner.PROMPT_LIMIT:
        step = positive_savings_first_fit_step(
            messages=candidate_messages,
            ledger=candidate_ledger,
            prompt_limit=runner.PROMPT_LIMIT,
            count_messages=tokenizer.count_messages,
            protected_result_ids=(pending_result_id,),
        )
        if not step.selected_result_ids:
            break
        selected.extend(step.selected_result_ids)
        prompt_tokens = step.prompt_tokens
    return selected, prompt_tokens


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
            "schema": "bluehaven-pressure-screen-audit-v0",
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
        "schema": "bluehaven-pressure-screen-result-v0",
        "task_id": TASK_ID,
        "task_source_lock_sha256": sha256_file(TASK / "TASK_SOURCE_LOCK.json"),
        "freeze_commit": "87cc19ea18bd5b24fe3ab9707176bc21e2b7e764",
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
    expected_freeze = {
        "schema": "bluehaven-pressure-screen-freeze-binding-v0",
        "commit": freeze_commit,
        "run_id": runner.RUN_ID,
        "task_source_lock_sha256": sha256_file(TASK / "TASK_SOURCE_LOCK.json"),
        "model_profile_lock_sha256": sha256_file(root / "MODEL_PROFILE_LOCK.json"),
        "screen_contract_sha256": sha256_file(root / "BLUEHAVEN_PRESSURE_SCREEN_CONTRACT.json"),
    }
    for key, expected in expected_freeze.items():
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
    tokenizer = OfflineTokenizer()
    with tempfile.TemporaryDirectory() as replay_temporary:
        replay_world = ArchitectureWorld(TASK, Path(replay_temporary))
        replay_ledger = ResultLedger()
        prior_result_id: str | None = None
        for ordinal, row in enumerate(trace, 1):
            if not isinstance(row, dict) or row.get("actor_call") != ordinal:
                failures.append(f"trace:{ordinal}:ordinal")
                continue
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
            if row.get("finish_reason") != "stop":
                failures.append(f"trace:{ordinal}:finish_reason")
            if row.get("rejection_code") is not None:
                failures.append(f"trace:{ordinal}:rejection")
            parsed = row.get("parsed_action")
            if not isinstance(parsed, dict) or parsed.get("action") not in {"read_source", "read_batch"}:
                failures.append(f"trace:{ordinal}:pretreatment_action")
                continue
            call_root = run_root / "actor" / f"call-{ordinal:03d}"
            call_messages = load(call_root / "messages.json")
            if tokenizer.count_messages(call_messages) != row.get("prompt_tokens"):
                failures.append(f"trace:{ordinal}:offline_prompt_count")
            output = (call_root / "assistant_content.txt").read_text(encoding="utf-8")
            if sha256_bytes(output.encode("utf-8")) != row.get("output_sha256"):
                failures.append(f"trace:{ordinal}:output_hash")
            receipt = load(call_root / "provider_attempt" / "PROVIDER_CALL_RECEIPT.json")
            if receipt.get("attempted") is not True or receipt.get("outcome") != "valid_completion_response":
                failures.append(f"trace:{ordinal}:provider_outcome")
            if prior_result_id is not None:
                replay_ledger.mark_model_visible(
                    prior_result_id,
                    call_index=ordinal,
                    message_index=len(call_messages) - 1,
                )
            result_id = str(row.get("result_id"))
            execution = replay_world.execute(parsed, result_id=result_id, ledger=replay_ledger)
            replay_record = replay_world.make_result_record(
                execution,
                result_id=result_id,
                acquired_call=ordinal,
            )
            recorded = load(call_root / "RESULT_RECORD.json")
            if replay_record.as_dict(include_exact_content=True) != recorded:
                failures.append(f"trace:{ordinal}:result_reexecution")
            replay_ledger.add(replay_record)
            prior_result_id = result_id
        if replay_world.candidate_sha256 != result.get("candidate_sha256"):
            failures.append("replay:candidate_hash")
    if serialized != result.get("serialized_tokens"):
        failures.append("trace:serialized_total")

    if boundary.get("schema") != "bluehaven-authentic-pressure-boundary-v0":
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
    if tokenizer.count_messages(final_messages) != prospective:
        failures.append("boundary:offline_token_recount")
    if boundary.get("overflow_tokens") != prospective - runner.PROMPT_LIMIT:
        failures.append("boundary:overflow")
    if result.get("boundary", {}).get("ordinary_prospective_prompt_tokens") != prospective:
        failures.append("result:boundary_summary")

    activation_value: dict[str, Any] = {}
    selected: list[str] = []
    relief_after = 0
    pending_id = str(boundary.get("pending_result_id"))
    try:
        ledger = ResultLedger.from_dict(ledger_value)
        pending = ledger.get(pending_id)
        if pending.previously_visible:
            failures.append("boundary:pending_delivered")
        with tempfile.TemporaryDirectory() as activation_temporary:
            activation_world = ArchitectureWorld(TASK, Path(activation_temporary))
            activation_failures, activation = boundary_eligibility_failures(
                pending=pending,
                ledger=ledger,
                world=activation_world,
                initial_candidate_sha256=activation_world.candidate_sha256,
            )
        activation_value = activation.as_dict()
        failures.extend(f"boundary:activation:{item}" for item in activation_failures)
        if boundary.get("activation_snapshot") != activation_value:
            failures.append("boundary:activation_snapshot")
        selected, relief_after = relief_audit(
            messages=final_messages,
            ledger_value=ledger_value,
            pending_result_id=pending_id,
            tokenizer=tokenizer,
        )
        if not selected or relief_after > runner.PROMPT_LIMIT:
            failures.append("interaction_activation:no_feasible_relief")
        if boundary.get("counterfactual_positive_relief_result_ids") != selected:
            failures.append("boundary:relief_ids")
        if boundary.get("counterfactual_relief_prompt_tokens") != relief_after:
            failures.append("boundary:relief_tokens")
    except Exception as exc:
        failures.append(f"boundary:ledger_or_relief:{type(exc).__name__}")

    audit_value = {
        "schema": "bluehaven-pressure-screen-audit-v0",
        "run_id": runner.RUN_ID,
        "freeze_commit": freeze_commit,
        "task_id": TASK_ID,
        "actor_calls": actor_calls,
        "provider_attempts": actor_calls,
        "serialized_tokens": serialized,
        "ordinary_prospective_prompt_tokens": prospective,
        "prompt_limit": runner.PROMPT_LIMIT,
        "overflow_tokens": prospective - runner.PROMPT_LIMIT,
        "pending_result_id": pending_id,
        "pending_result_delivered": False,
        "activation_snapshot": activation_value,
        "positive_relief_result_ids": selected,
        "positive_relief_after_tokens": relief_after,
        "interaction_trigger_qualified": bool(selected) and relief_after <= runner.PROMPT_LIMIT,
        "runtime_released": runtime_release.get("released") is True,
        "measured_fork_authorized": False,
        "passed": not failures,
        "failures": sorted(set(failures)),
    }
    if write_outputs:
        write_json(root / AUDIT_NAME, audit_value)
        if audit_value["passed"]:
            handoff = {
                "schema_version": "bluehaven-pressure-boundary-handoff-v0",
                "status": "passed_authentic_pressure_boundary",
                "run_id": runner.RUN_ID,
                "run_root": str(run_root.relative_to(root)).replace("\\", "/"),
                "task_id": TASK_ID,
                "task_source_lock_sha256": sha256_file(TASK / "TASK_SOURCE_LOCK.json"),
                "freeze_commit": freeze_commit,
                "actor_calls": actor_calls,
                "provider_attempts": actor_calls,
                "attempts_per_call": 1,
                "retries": 0,
                "pressure_qualified": True,
                "interaction_trigger_qualified": True,
                "positive_relief_result_ids": selected,
                "positive_relief_after_tokens": relief_after,
                "ordinary_prospective_prompt_tokens": prospective,
                "prompt_limit": runner.PROMPT_LIMIT,
                "overflow_tokens": prospective - runner.PROMPT_LIMIT,
                "pending_result_id": pending_id,
                "pending_result_delivered": False,
                "activation_snapshot": activation_value,
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
                "claim_limit": "This handoff qualifies one exact common pre-treatment pressure fork. It does not establish B1 or W1 utility and authorizes no continuation.",
            }
            write_json(root / HANDOFF_NAME, handoff)
    return audit_value


def main() -> int:
    result = audit()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
