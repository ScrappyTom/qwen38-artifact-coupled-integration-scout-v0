from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json
from reactive_runtime.configuration import PHASE_LIFECYCLE_CONFIGURATIONS
from reactive_runtime.orchard_boundary import verify_orchard_pressure_handoff
from tools import run_orchard_phase_lifecycle as runner


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def preflight(*, write_output: bool = True) -> dict[str, Any]:
    failures: list[str] = []
    handoff = verify_orchard_pressure_handoff(ROOT)
    stage0 = load(ROOT / "ORCHARD_PHASE_LIFECYCLE_STAGE0_PREFLIGHT.json")
    contract = load(ROOT / "ORCHARD_PHASE_LIFECYCLE_MEASURED_CONTRACT.json")
    request = load(ROOT / "ORCHARD_PHASE_LIFECYCLE_AUTHORIZATION_REQUEST.json")
    design = load(ROOT / "ORCHARD_INTERACTION_DESIGN.json")
    pressure_audit = load(ROOT / "ORCHARD_PRESSURE_SCREEN_AUDIT.json")
    if stage0.get("passed") is not True or stage0.get("provider_calls") != 0:
        failures.append("stage0")
    if pressure_audit.get("passed") is not True:
        failures.append("pressure_audit")
    if handoff.get("positive_relief_result_ids") != ["RESULT-001"]:
        failures.append("pressure_relief")
    if handoff.get("pending_result_id") != "RESULT-006":
        failures.append("pending_result")
    if tuple(contract.get("configuration_order", [])) != PHASE_LIFECYCLE_CONFIGURATIONS:
        failures.append("contract_configuration_order")
    if tuple(design.get("configuration_order", [])) != PHASE_LIFECYCLE_CONFIGURATIONS:
        failures.append("design_configuration_order")
    expected_budgets = {
        "maximum_actor_calls_total": 2 * runner.MAX_ACTOR_CALLS_PER_CELL,
        "maximum_maintenance_calls_total": 2 * runner.MAX_MAINTENANCE_CALLS_PER_CELL,
        "maximum_provider_calls_total": runner.MAX_PROVIDER_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, expected in expected_budgets.items():
        if contract.get("budgets", {}).get(key) != expected:
            failures.append(f"contract_budget:{key}")
    if request.get("authorized") is not False:
        failures.append("authorization_request_not_inert")
    if request.get("maximum_provider_calls") != runner.MAX_PROVIDER_CALLS:
        failures.append("authorization_provider_budget")
    if request.get("maximum_actor_calls") != 2 * runner.MAX_ACTOR_CALLS_PER_CELL:
        failures.append("authorization_actor_budget")
    if request.get("maximum_maintenance_calls") != 2 * runner.MAX_MAINTENANCE_CALLS_PER_CELL:
        failures.append("authorization_maintenance_budget")
    if (ROOT / "runs" / runner.RUN_ID).exists():
        failures.append("measured_run_root_already_exists")
    fixtures = stage0.get("provider_free_lifecycles", [])
    if len(fixtures) != 2 or not all(
        row.get("construction_milestone", {}).get("passed")
        and row.get("prior_check_stale_after_patch")
        and row.get("recheck_passed")
        and row.get("submitted")
        for row in fixtures
    ):
        failures.append("provider_free_lifecycle")
    value = {
        "schema": "orchard-phase-lifecycle-measured-preflight-v0",
        "passed": not failures,
        "failures": failures,
        "provider_calls": 0,
        "gpu_authorized": False,
        "task_id": "orchard-biologics-restart-decision-v0",
        "run_id": runner.RUN_ID,
        "configuration_order": list(runner.CONFIGURATION_ORDER),
        "exact_pressure_handoff": {
            "run_id": handoff["run_id"],
            "freeze_commit": handoff["freeze_commit"],
            "actor_calls": handoff["actor_calls"],
            "pending_result_id": handoff["pending_result_id"],
            "ordinary_prospective_prompt_tokens": handoff["ordinary_prospective_prompt_tokens"],
            "overflow_tokens": handoff["overflow_tokens"],
            "positive_relief_result_ids": handoff["positive_relief_result_ids"],
            "positive_relief_after_tokens": handoff["positive_relief_after_tokens"],
        },
        "budget": {
            "actor_calls_per_cell": runner.MAX_ACTOR_CALLS_PER_CELL,
            "construction_actor_calls_per_cell": runner.MAX_CONSTRUCTION_CALLS_PER_CELL,
            "verification_actor_calls_per_cell": runner.MAX_VERIFICATION_CALLS_PER_CELL,
            "maintenance_calls_per_cell": runner.MAX_MAINTENANCE_CALLS_PER_CELL,
            "provider_calls_total": runner.MAX_PROVIDER_CALLS,
            "attempts_per_call": 1,
            "retries": 0,
        },
        "provider_free_lifecycle_passed": True,
        "relationship_red_team_passed": all(
            row.get("caught") for row in stage0.get("relationship_red_team", [])
        ),
        "bindings": {
            "pressure_handoff_sha256": sha256_file(ROOT / "ORCHARD_PRESSURE_BOUNDARY_HANDOFF.json"),
            "pressure_audit_sha256": sha256_file(ROOT / "ORCHARD_PRESSURE_SCREEN_AUDIT.json"),
            "contract_sha256": sha256_file(ROOT / "ORCHARD_PHASE_LIFECYCLE_MEASURED_CONTRACT.json"),
            "authorization_request_sha256": sha256_file(ROOT / "ORCHARD_PHASE_LIFECYCLE_AUTHORIZATION_REQUEST.json"),
            "task_source_lock_sha256": sha256_file(ROOT / "task_orchard" / "TASK_SOURCE_LOCK.json"),
            "model_profile_lock_sha256": sha256_file(ROOT / "ORCHARD_MODEL_PROFILE_LOCK.json"),
        },
        "claim_limit": "Offline qualification of the exact pressure fork, compound F0/P1 runner, budgets, provider-free lifecycle, relational checker, and authorization gate. It supplies no live comparative behavior or utility evidence.",
    }
    if write_output:
        write_json(ROOT / "ORCHARD_PHASE_LIFECYCLE_MEASURED_PREFLIGHT.json", value)
    return value


def main() -> int:
    value = preflight()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
