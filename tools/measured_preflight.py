from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.boundary import verify_pressure_handoff  # noqa: E402
from reactive_runtime.canonical import sha256_file, write_json  # noqa: E402
from tools import run_measured_interaction as measured  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def main() -> int:
    failures: list[str] = []
    measured.verify_task_lock()
    try:
        pressure = verify_pressure_handoff(ROOT)
    except Exception as exc:
        pressure = {"error": f"{type(exc).__name__}:{exc}"}
        failures.append("pressure_handoff")
    if pressure.get("interaction_trigger_qualified") is not True:
        failures.append("pressure_handoff:interaction_trigger")
    contract = load(ROOT / "MEASURED_INTERACTION_CONTRACT.json")
    request = load(ROOT / "MEASURED_AUTHORIZATION_REQUEST.json")
    design = load(ROOT / "INTERACTION_DESIGN.json")
    fixture = load(ROOT / "STAGE0_MEASURED_FIXTURE.json")
    expected = {
        "run_id": measured.RUN_ID,
        "scope": measured.SCOPE,
        "configuration_order": list(measured.CONFIGURATION_ORDER),
        "maximum_actor_calls_per_configuration": measured.MAX_ACTOR_CALLS_PER_CELL,
        "maximum_maintenance_calls_per_configuration": measured.MAX_MAINTENANCE_CALLS_PER_CELL,
        "maximum_reentries_per_configuration": measured.MAX_REENTRIES_PER_CELL,
        "maximum_serialized_tokens_per_configuration": measured.MAX_SERIALIZED_TOKENS_PER_CELL,
        "maximum_wall_seconds_per_configuration": measured.MAX_WALL_SECONDS_PER_CELL,
        "maximum_actor_calls": measured.MAX_ACTOR_CALLS_PER_CELL
        * len(measured.CONFIGURATION_ORDER),
        "maximum_maintenance_calls": measured.MAX_MAINTENANCE_CALLS_PER_CELL
        * len(measured.CONFIGURATION_ORDER),
        "maximum_provider_calls": measured.MAX_PROVIDER_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            failures.append(f"contract:{key}")
    request_expected = {
        "authorized": False,
        "scope": measured.SCOPE,
        "run_id": measured.RUN_ID,
        "configuration_order": list(measured.CONFIGURATION_ORDER),
        "maximum_actor_calls": expected["maximum_actor_calls"],
        "maximum_maintenance_calls": expected["maximum_maintenance_calls"],
        "maximum_provider_calls": measured.MAX_PROVIDER_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, value in request_expected.items():
        if request.get(key) != value:
            failures.append(f"authorization_request:{key}")
    if design.get("not_isolated_components") is not True:
        failures.append("interaction_design:isolated")
    if fixture.get("passed") is not True or fixture.get("offline_provider_only") is not True:
        failures.append("provider_free_fixture")
    cells = fixture.get("cells")
    if not isinstance(cells, list) or {row.get("configuration_id") for row in cells} != set(
        measured.CONFIGURATION_ORDER
    ):
        failures.append("provider_free_fixture:cells")
        cells = []
    for row in cells:
        configuration_id = row["configuration_id"]
        if row.get("terminal_disposition") != "submitted":
            failures.append(f"fixture:{configuration_id}:terminal")
        if int(row.get("accepted_integration_updates", 0)) < 1:
            failures.append(f"fixture:{configuration_id}:maintenance")
        if int(row.get("externalization_count", 0)) < 1:
            failures.append(f"fixture:{configuration_id}:relief")
        if int(row.get("candidate_effects_delivered", 0)) < 1:
            failures.append(f"fixture:{configuration_id}:effect_uptake")
        if int(row.get("check_count", 0)) != 2:
            failures.append(f"fixture:{configuration_id}:check_repair")
        budget = row.get("trajectory_budget", {})
        if budget.get("milestone_call") is None or int(
            budget.get("remaining_calls_in_current_window", 0)
        ) < 1:
            failures.append(f"fixture:{configuration_id}:postconstruction_tail")
        projection = row.get("mechanical_final_evaluation", {}).get("projection", {})
        if projection.get("closure_readiness") != "not_adjudicated":
            failures.append(f"fixture:{configuration_id}:mechanical_precheck")
    initial = fixture.get("initial_continuation")
    boundary_hash = pressure.get("candidate_sha256")
    if not isinstance(initial, dict):
        failures.append("provider_free_fixture:initial")
    else:
        if initial.get("D0_DETACHED", {}).get("candidate_sha256") != boundary_hash:
            failures.append("detached_initial_candidate_effect")
        if initial.get("A1_COUPLED", {}).get("candidate_sha256") == boundary_hash:
            failures.append("coupled_initial_candidate_effect")
    run_root = ROOT / "runs" / measured.RUN_ID
    if run_root.exists():
        failures.append("measured_run_root_already_exists")
    result = {
        "schema": "northstar-artifact-coupling-measured-preflight-v0",
        "passed": not failures,
        "failures": failures,
        "apparatus_commit": measured.git_commit(),
        "pressure_boundary": pressure,
        "pressure_boundary_handoff_sha256": sha256_file(
            ROOT / "NORTHSTAR_PRESSURE_BOUNDARY_HANDOFF.json"
        ),
        "provider_free_fixture_sha256": sha256_file(ROOT / "STAGE0_MEASURED_FIXTURE.json"),
        "contract_sha256": sha256_file(ROOT / "MEASURED_INTERACTION_CONTRACT.json"),
        "configuration_order": list(measured.CONFIGURATION_ORDER),
        "actor_call_ceiling": expected["maximum_actor_calls"],
        "maintenance_call_ceiling": expected["maximum_maintenance_calls"],
        "provider_call_ceiling": measured.MAX_PROVIDER_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
        "gpu_authorized": False,
        "next_step": "freeze_commit_then_explicit_user_authorization",
    }
    write_json(ROOT / "MEASURED_PREFLIGHT.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
