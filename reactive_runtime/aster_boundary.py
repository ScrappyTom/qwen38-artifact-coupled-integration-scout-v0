from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reactive_runtime.canonical import sha256_file


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def verify_aster_pressure_handoff(root: Path) -> dict[str, Any]:
    root = root.resolve()
    handoff_path = root / "ASTER_PRESSURE_BOUNDARY_HANDOFF.json"
    audit_path = root / "ASTER_PRESSURE_SCREEN_AUDIT.json"
    handoff = load_object(handoff_path)
    audit = load_object(audit_path)
    run_root = root / str(handoff.get("run_root", ""))
    failures: list[str] = []
    expected = {
        "schema_version": "aster-pressure-boundary-handoff-v0",
        "status": "passed_authentic_interaction_pressure_boundary",
        "run_id": "2026-08-25-aster-provenance-relational-pressure-screen-v0",
        "task_id": "aster-payment-recovery-decision-v0",
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
        "task_source_lock_sha256": root / "task_aster" / "TASK_SOURCE_LOCK.json",
    }
    for key, path in bindings.items():
        if not path.is_file() or handoff.get(key) != sha256_file(path):
            failures.append(f"binding:{key}")
    if failures:
        raise RuntimeError(f"Aster pressure handoff failed: {sorted(set(failures))}")
    return handoff
