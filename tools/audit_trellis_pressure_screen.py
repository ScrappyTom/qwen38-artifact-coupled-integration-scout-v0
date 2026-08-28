from __future__ import annotations

import json
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.activation import activation_snapshot
from reactive_runtime.canonical import sha256_bytes, sha256_file, write_json
from reactive_runtime.keystone_world import KeystoneWorld
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
from reactive_runtime.seal import verify_tree_seal
from tools.offline_tokenizer import OfflineTokenizer
from tools import run_trellis_pressure_screen as runner


TASK = ROOT / "task_trellis"
RUN_ROOT = ROOT / "runs" / runner.RUN_ID
FREEZE_COMMIT = "6eba6badd5bfbebdf931a8374d99687c17d4347b"
AUDIT_PATH = ROOT / "TRELLIS_PRESSURE_SCREEN_AUDIT.json"
PROMPT_LIMIT = 20_992


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(*, write_output: bool = True) -> dict[str, Any]:
    failures: list[str] = []
    required = (
        "AUTHORIZATION_RECEIPT.json", "CALL_TRACE.json", "FINALIZATION.json",
        "FINAL_MESSAGES.json", "FREEZE_BINDING.json", "PRESSURE_BOUNDARY.json",
        "RESULT_LEDGER.json", "RUN_SEAL.json", "RUNTIME_ASSET_VERIFICATION.json",
        "SCREEN_RESULT.json", "model/RUNTIME_GATE.json", "model/RUNTIME_RELEASE.json",
    )
    for relative in required:
        if not (RUN_ROOT / relative).is_file():
            failures.append(f"missing:{relative}")
    if failures:
        return {"schema": "trellis-pressure-screen-audit-v0", "passed": False, "failures": failures}

    failures.extend(f"seal:{value}" for value in verify_tree_seal(RUN_ROOT, RUN_ROOT / "RUN_SEAL.json"))
    result = load(RUN_ROOT / "SCREEN_RESULT.json")
    trace = load(RUN_ROOT / "CALL_TRACE.json")
    boundary = load(RUN_ROOT / "PRESSURE_BOUNDARY.json")
    final_messages = load(RUN_ROOT / "FINAL_MESSAGES.json")
    ledger_value = load(RUN_ROOT / "RESULT_LEDGER.json")
    authorization = load(RUN_ROOT / "AUTHORIZATION_RECEIPT.json")
    freeze = load(RUN_ROOT / "FREEZE_BINDING.json")
    finalization = load(RUN_ROOT / "FINALIZATION.json")
    runtime_gate = load(RUN_ROOT / "model" / "RUNTIME_GATE.json")
    runtime_release = load(RUN_ROOT / "model" / "RUNTIME_RELEASE.json")

    expected_result = {
        "freeze_commit": FREEZE_COMMIT,
        "run_id": runner.RUN_ID,
        "task_id": runner.TASK_ID,
        "seed": runner.SEED,
        "actor_calls": 7,
        "serialized_tokens": 73_900,
        "terminal_disposition": "pressure_before_ingress_aligned_activation",
        "pressure_qualified": False,
        "candidate_submitted": False,
    }
    for key, value in expected_result.items():
        if result.get(key) != value:
            failures.append(f"result:{key}")
    expected_auth = {
        "authorized": True,
        "authorized_freeze_commit": FREEZE_COMMIT,
        "authorized_scopes": [runner.SCOPE],
        "authorized_run_id": runner.RUN_ID,
        "maximum_model_calls": 30,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, value in expected_auth.items():
        if authorization.get(key) != value:
            failures.append(f"authorization:{key}")
    if freeze.get("commit") != FREEZE_COMMIT:
        failures.append("freeze:commit")
    if freeze.get("task_source_lock_sha256") != sha256_file(TASK / "TASK_SOURCE_LOCK.json"):
        failures.append("freeze:task_lock")
    if freeze.get("model_profile_lock_sha256") != sha256_file(ROOT / "TRELLIS_MODEL_PROFILE_LOCK.json"):
        failures.append("freeze:model_lock")
    if freeze.get("screen_contract_sha256") != sha256_file(ROOT / "TRELLIS_PRESSURE_SCREEN_CONTRACT.json"):
        failures.append("freeze:contract")
    if runtime_gate.get("passed") is not True:
        failures.append("runtime_gate")
    if runtime_release.get("released") is not True or finalization.get("release", {}).get("released") is not True:
        failures.append("runtime_release")
    if finalization.get("failure") is not None:
        failures.append("finalization")

    tokenizer = OfflineTokenizer()
    serialized = 0
    visible_source_lines: dict[str, int] = {}
    with tempfile.TemporaryDirectory(prefix="trellis-audit-") as temp:
        world = KeystoneWorld(TASK, Path(temp))
        ledger = ResultLedger()
        prior_result_id: str | None = None
        for ordinal, row in enumerate(trace, 1):
            if row.get("actor_call") != ordinal or row.get("rejection_code") is not None:
                failures.append(f"trace:{ordinal}:shape")
                continue
            usage = row.get("usage", {})
            if usage.get("prompt_tokens") + usage.get("completion_tokens") != usage.get("total_tokens"):
                failures.append(f"trace:{ordinal}:usage")
            else:
                serialized += int(usage["total_tokens"])
            call_root = RUN_ROOT / "actor" / f"call-{ordinal:03d}"
            messages = load(call_root / "messages.json")
            if tokenizer.count_messages(messages) != row.get("prompt_tokens"):
                failures.append(f"trace:{ordinal}:prompt_count")
            output = (call_root / "assistant_content.txt").read_text(encoding="utf-8")
            if sha256_bytes(output.encode("utf-8")) != row.get("output_sha256"):
                failures.append(f"trace:{ordinal}:output_hash")
            if prior_result_id is not None:
                prior = ledger.get(prior_result_id)
                ledger.mark_model_visible(prior_result_id, call_index=ordinal, message_index=len(messages) - 1)
                for segment in prior.metadata.get("segments", []):
                    source_id = str(segment["source_id"])
                    visible_source_lines[source_id] = visible_source_lines.get(source_id, 0) + int(segment["end_line"]) - int(segment["start_line"]) + 1
            parsed = row["parsed_action"]
            result_id = str(row["result_id"])
            execution = world.execute(parsed, result_id=result_id, ledger=ledger)
            record = world.make_result_record(execution, result_id=result_id, acquired_call=ordinal)
            if record.as_dict(include_exact_content=True) != load(call_root / "RESULT_RECORD.json"):
                failures.append(f"trace:{ordinal}:reexecution")
            ledger.add(record)
            prior_result_id = result_id

        if world.candidate_sha256 != result.get("candidate_sha256"):
            failures.append("candidate_replay")
        pending_id = str(boundary["pending_result_id"])
        activation = activation_snapshot(
            pending=ledger.get(pending_id),
            ledger=ledger,
            world=world,
            minimum_qualifying_sources=8,
            minimum_evidence_domains=8,
        ).as_dict()
        if activation != boundary.get("activation_snapshot"):
            failures.append("activation_replay")
        candidate_messages = deepcopy(final_messages)
        candidate_ledger = ResultLedger.from_dict(ledger_value)
        prompt_tokens = tokenizer.count_messages(candidate_messages)
        relief_ids: list[str] = []
        while prompt_tokens > PROMPT_LIMIT:
            step = positive_savings_first_fit_step(
                messages=candidate_messages,
                ledger=candidate_ledger,
                prompt_limit=PROMPT_LIMIT,
                count_messages=tokenizer.count_messages,
                protected_result_ids=(pending_id,),
            )
            if not step.selected_result_ids:
                break
            relief_ids.extend(step.selected_result_ids)
            prompt_tokens = step.prompt_tokens
        if relief_ids != boundary.get("counterfactual_positive_relief_result_ids"):
            failures.append("relief:ids")
        if prompt_tokens != boundary.get("counterfactual_relief_prompt_tokens"):
            failures.append("relief:tokens")

    if serialized != result.get("serialized_tokens"):
        failures.append("serialized_total")
    if tokenizer.count_messages(final_messages) != boundary.get("ordinary_prospective_prompt_tokens"):
        failures.append("boundary:prompt_tokens")
    pending_sources = sorted(ledger.get(str(boundary["pending_result_id"])).metadata.get("source_ids", []))
    qualifying = sorted(boundary["activation_snapshot"]["qualifying_sources"])
    audit_value = {
        "schema": "trellis-pressure-screen-audit-v0",
        "run_id": runner.RUN_ID,
        "freeze_commit": FREEZE_COMMIT,
        "actor_calls": len(trace),
        "provider_attempts": len(trace),
        "serialized_tokens": serialized,
        "ordinary_prospective_prompt_tokens": boundary["ordinary_prospective_prompt_tokens"],
        "prompt_limit": PROMPT_LIMIT,
        "overflow_tokens": boundary["overflow_tokens"],
        "positive_relief_result_ids": boundary["counterfactual_positive_relief_result_ids"],
        "positive_relief_after_tokens": boundary["counterfactual_relief_prompt_tokens"],
        "visible_qualifying_sources": qualifying,
        "visible_qualifying_domains": boundary["activation_snapshot"]["qualifying_domains"],
        "pending_result_id": boundary["pending_result_id"],
        "pending_source_ids": pending_sources,
        "pending_result_delivered": False,
        "candidate_changed": False,
        "pressure_qualified": False,
        "measured_fork_authorized": False,
        "runtime_released": runtime_release.get("released") is True,
        "passed": not failures,
        "failures": sorted(set(failures)),
    }
    if write_output:
        write_json(AUDIT_PATH, audit_value)
    return audit_value


def main() -> int:
    value = audit()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
