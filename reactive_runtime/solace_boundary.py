from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reactive_runtime.canonical import sha256_file


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def verify_solace_pressure_handoff(root: Path) -> dict[str, Any]:
    root = root.resolve()
    handoff_path = root / "SOLACE_PRESSURE_BOUNDARY_HANDOFF.json"
    audit_path = root / "SOLACE_PRESSURE_SCREEN_AUDIT.json"
    handoff = _load(handoff_path)
    audit = _load(audit_path)
    run_root = root / str(handoff.get("run_root", ""))
    failures: list[str] = []
    expected = {
        "schema_version": "solace-pressure-boundary-handoff-v0",
        "status": "passed_authentic_interaction_pressure_boundary",
        "run_id": "2026-08-26-solace-anchored-provenance-pressure-screen-v0",
        "task_id": "solace-water-recovery-decision-v0",
        "pressure_qualified": True,
        "interaction_trigger_qualified": True,
        "positive_relief_result_ids": ["RESULT-001"],
        "externalized_source_result_ids": ["RESULT-001"],
        "pending_result_id": "RESULT-006",
        "pending_result_delivered": False,
        "candidate_changed": False,
        "candidate_submitted": False,
        "current_check_binding": None,
        "expression_qualification_authorized": False,
        "measured_fork_authorized": False,
    }
    for key, value in expected.items():
        if handoff.get(key) != value:
            failures.append(f"handoff:{key}")
    if audit.get("passed") is not True or audit.get("failures") != []:
        failures.append("screen_audit")
    bindings = {
        "screen_result_sha256": run_root / "SCREEN_RESULT.json",
        "pressure_boundary_sha256": run_root / "PRESSURE_BOUNDARY.json",
        "final_messages_sha256": run_root / "FINAL_MESSAGES.json",
        "result_ledger_sha256": run_root / "RESULT_LEDGER.json",
        "run_seal_sha256": run_root / "RUN_SEAL.json",
        "screen_audit_sha256": audit_path,
        "task_source_lock_sha256": root / "task_solace" / "TASK_SOURCE_LOCK.json",
    }
    for key, path in bindings.items():
        if not path.is_file() or handoff.get(key) != sha256_file(path):
            failures.append(f"binding:{key}")
    if failures:
        raise RuntimeError(f"Solace pressure handoff failed: {sorted(set(failures))}")
    return handoff
