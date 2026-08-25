from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reactive_runtime.canonical import sha256_file
from reactive_runtime.records import ResultLedger
from reactive_runtime.seal import verify_tree_seal
from reactive_runtime.world import ArchitectureWorld


SCREEN_RUN_ID = "2026-08-25-cedar-ingress-aligned-pressure-screen-v0"
HANDOFF_NAME = "CEDAR_PRESSURE_BOUNDARY_HANDOFF.json"
TASK_ID = "cedar-valley-evacuation-decision-package-v0"


@dataclass(frozen=True)
class PressureBoundary:
    messages: list[dict[str, str]]
    ledger: ResultLedger
    pending_result_id: str
    pending_message_index: int
    actor_calls_completed: int
    next_result_ordinal: int
    candidate_sha256: str
    prospective_prompt_tokens: int
    prompt_limit: int


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def verify_pressure_handoff(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    handoff = _load(root / HANDOFF_NAME)
    run_root = (root / str(handoff.get("run_root"))).resolve()
    expected_root = (root / "runs" / SCREEN_RUN_ID).resolve()
    failures: list[str] = []
    if run_root != expected_root:
        failures.append("run_root")
    expected = {
        "status": "passed_authentic_pressure_boundary",
        "run_id": SCREEN_RUN_ID,
        "task_id": TASK_ID,
        "pressure_qualified": True,
        "interaction_trigger_qualified": True,
        "attempts_per_call": 1,
        "retries": 0,
        "pending_result_delivered": False,
        "prompt_limit": 20_992,
        "candidate_changed": False,
        "candidate_submitted": False,
        "runtime_released": True,
        "measured_fork_authorized": False,
        "task_source_lock_sha256": sha256_file(
            root / "task" / "TASK_SOURCE_LOCK.json"
        ),
    }
    for key, expected_value in expected.items():
        if handoff.get(key) != expected_value:
            failures.append(key)
    freeze_commit = handoff.get("freeze_commit")
    if not isinstance(freeze_commit, str) or len(freeze_commit) != 40:
        failures.append("freeze_commit")
    actor_calls = handoff.get("actor_calls")
    if type(actor_calls) is not int or not 1 <= actor_calls <= 20:
        failures.append("actor_calls")
    if handoff.get("provider_attempts") != actor_calls:
        failures.append("provider_attempts")
    pending_result_id = handoff.get("pending_result_id")
    if not isinstance(pending_result_id, str) or not pending_result_id.startswith("RESULT-"):
        failures.append("pending_result_id")
    prospective = handoff.get("ordinary_prospective_prompt_tokens")
    overflow = handoff.get("overflow_tokens")
    if type(prospective) is not int or prospective <= 20_992:
        failures.append("ordinary_prospective_prompt_tokens")
    elif overflow != prospective - 20_992:
        failures.append("overflow_tokens")
    activation = handoff.get("activation_snapshot")
    if not isinstance(activation, dict):
        failures.append("activation_snapshot")
    else:
        if len(activation.get("qualifying_sources", [])) < 4:
            failures.append("activation_qualifying_sources")
        if len(activation.get("qualifying_domains", [])) < 3:
            failures.append("activation_qualifying_domains")
        if not isinstance(activation.get("pending_novel_lines"), int) or activation["pending_novel_lines"] < 1:
            failures.append("activation_pending_novel_lines")
    relief_ids = handoff.get("positive_relief_result_ids")
    if not isinstance(relief_ids, list) or not relief_ids or not all(
        isinstance(value, str) and value.startswith("RESULT-") for value in relief_ids
    ):
        failures.append("positive_relief_result_ids")
    relief_after = handoff.get("positive_relief_after_tokens")
    if (
        type(relief_after) is not int
        or type(prospective) is not int
        or relief_after >= prospective
    ):
        failures.append("positive_relief_after_tokens")
    file_bindings = {
        "screen_result_sha256": run_root / "SCREEN_RESULT.json",
        "pressure_boundary_sha256": run_root / "PRESSURE_BOUNDARY.json",
        "final_messages_sha256": run_root / "FINAL_MESSAGES.json",
        "result_ledger_sha256": run_root / "RESULT_LEDGER.json",
        "run_seal_sha256": run_root / "RUN_SEAL.json",
        "screen_audit_sha256": root / "CEDAR_PRESSURE_SCREEN_AUDIT.json",
    }
    for key, path in file_bindings.items():
        if not path.is_file() or handoff.get(key) != sha256_file(path):
            failures.append(key)
    audit_path = root / "CEDAR_PRESSURE_SCREEN_AUDIT.json"
    if audit_path.is_file():
        audit = _load(audit_path)
        if audit.get("passed") is not True:
            failures.append("screen_audit_passed")
        if audit.get("run_id") != SCREEN_RUN_ID:
            failures.append("screen_audit_run_id")
        if audit.get("interaction_trigger_qualified") is not True:
            failures.append("screen_audit_interaction_trigger")
        if audit.get("positive_relief_result_ids") != relief_ids:
            failures.append("screen_audit_positive_relief")
    if run_root.is_dir():
        failures.extend(
            f"seal:{item}"
            for item in verify_tree_seal(run_root, run_root / "RUN_SEAL.json")
        )
    if failures:
        raise RuntimeError(
            f"pressure handoff verification failed: {sorted(set(failures))}"
        )
    return handoff


def hydrate_pressure_boundary(
    *, repository_root: Path, world: ArchitectureWorld
) -> PressureBoundary:
    handoff = verify_pressure_handoff(repository_root)
    run_root = repository_root.resolve() / str(handoff["run_root"])
    raw = _load(run_root / "PRESSURE_BOUNDARY.json")
    messages_value = raw.get("messages")
    ledger_value = raw.get("result_ledger")
    if not isinstance(messages_value, list) or not all(
        isinstance(row, dict)
        and row.get("role") in {"system", "user", "assistant"}
        and isinstance(row.get("content"), str)
        for row in messages_value
    ):
        raise ValueError("pressure boundary messages are invalid")
    if not isinstance(ledger_value, dict):
        raise ValueError("pressure boundary ledger is invalid")
    if raw.get("task_id") != TASK_ID:
        raise ValueError("pressure boundary task mismatch")
    if raw.get("eligibility_failures") != []:
        raise ValueError("pressure boundary was not eligible")
    if raw.get("candidate_sha256") != world.candidate_sha256:
        raise ValueError("fresh world does not match frozen boundary candidate")
    if raw.get("candidate_packet") != world.candidate_packet():
        raise ValueError("fresh candidate packet does not match frozen boundary")
    ledger = ResultLedger.from_dict(ledger_value)
    messages = [
        {"role": str(row["role"]), "content": str(row["content"])}
        for row in messages_value
    ]
    pending_id = str(raw.get("pending_result_id"))
    pending = ledger.get(pending_id)
    if pending.result_kind != "source_observation":
        raise ValueError("pending boundary result is not a source observation")
    matches = [
        index
        for index, message in enumerate(messages)
        if message == {"role": "user", "content": pending.exact_content}
    ]
    if len(matches) != 1:
        raise ValueError("pending result does not bind exactly one message")
    if pending.first_model_visible_call is not None:
        raise ValueError("frozen pending result was already delivered")
    for record in ledger.records():
        if record.result_id == pending_id:
            continue
        if not record.previously_visible or not record.resident or record.message_index is None:
            raise ValueError(f"prior result residency mismatch: {record.result_id}")
        if messages[record.message_index] != {
            "role": "user",
            "content": record.exact_content,
        }:
            raise ValueError(f"prior result message binding mismatch: {record.result_id}")
    ordinals = [
        int(record.result_id.split("-", 1)[1])
        for record in ledger.records()
        if record.result_id.startswith("RESULT-")
    ]
    return PressureBoundary(
        messages=deepcopy(messages),
        ledger=ledger,
        pending_result_id=pending_id,
        pending_message_index=matches[0],
        actor_calls_completed=int(raw["actor_calls_completed"]),
        next_result_ordinal=max(ordinals) + 1,
        candidate_sha256=str(raw["candidate_sha256"]),
        prospective_prompt_tokens=int(raw["ordinary_prospective_prompt_tokens"]),
        prompt_limit=int(raw["prompt_limit"]),
    )
