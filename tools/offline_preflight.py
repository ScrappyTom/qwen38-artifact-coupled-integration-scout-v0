from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.actions import DECISION_HEADINGS  # noqa: E402
from reactive_runtime.boundary import verify_pressure_handoff  # noqa: E402
from reactive_runtime.canonical import sha256_file, write_json  # noqa: E402
from reactive_runtime.configuration import CONFIGURATIONS, ordinary_actions  # noqa: E402
from reactive_runtime.trajectory_budget import ConstructionBudget  # noqa: E402
from reactive_runtime.world import ArchitectureWorld  # noqa: E402
from tools import run_measured_interaction as measured  # noqa: E402
from tools import run_pressure_screen as screen  # noqa: E402
from tools.materialize_transfer_world import SOURCES  # noqa: E402


TASK_ID = "northstar-migration-architecture-package-v0"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def main() -> int:
    failures: list[str] = []
    lock = load(ROOT / "task" / "TASK_SOURCE_LOCK.json")
    evaluator = load(ROOT / "task" / "EVALUATOR.json")
    world_spec = load(ROOT / "task" / "WORLD_SPEC.json")
    protocol = load(ROOT / "SEMANTIC_ADJUDICATION_PROTOCOL_TRANSFER.json")
    geometry = load(ROOT / "STAGE0_GEOMETRY.json")
    basic_fixture = load(ROOT / "STAGE0_INTERACTION_FIXTURE.json")
    measured_fixture = load(ROOT / "STAGE0_MEASURED_FIXTURE.json")
    screen_contract = load(ROOT / "PRESSURE_SCREEN_CONTRACT.json")
    screen_request = load(ROOT / "PRESSURE_SCREEN_AUTHORIZATION_REQUEST.json")
    measured_contract = load(ROOT / "MEASURED_INTERACTION_CONTRACT.json")
    measured_request = load(ROOT / "MEASURED_AUTHORIZATION_REQUEST.json")
    profile = load(ROOT / "MODEL_PROFILE_LOCK.json")

    if lock.get("task_id") != TASK_ID or lock.get("world_origin") != "deterministic_synthetic_northstar_world_v0":
        failures.append("fresh_task_lock_identity")
    for row in lock.get("files", []):
        path = ROOT / "task" / str(row.get("path"))
        if not path.is_file() or sha256_file(path) != row.get("sha256"):
            failures.append(f"task_lock:{row.get('path')}")
    custody = lock.get("source_custody")
    if not isinstance(custody, list) or len(custody) != 14:
        failures.append("source_custody_count")
        custody = []
    generated_names = list(SOURCES)
    for ordinal, name in enumerate(generated_names, 1):
        path = ROOT / "task" / "transfer_sources" / name
        if not path.is_file() or path.read_text(encoding="utf-8") != SOURCES[name]():
            failures.append(f"source_generator:S{ordinal:02d}")
    if any("task/sources/" in str(row.get("path", "")) for row in custody):
        failures.append("historical_source_catalog_leak")

    if evaluator.get("task_id") != TASK_ID or protocol.get("task_id") != TASK_ID:
        failures.append("evaluator_task_binding")
    if protocol.get("task_source_lock_sha256") != sha256_file(
        ROOT / "task" / "TASK_SOURCE_LOCK.json"
    ):
        failures.append("semantic_protocol:task_lock")
    if protocol.get("mechanical_evaluator_sha256") != sha256_file(
        ROOT / "task" / "evaluator" / "evaluate.py"
    ):
        failures.append("semantic_protocol:mechanical_evaluator")
    if protocol.get("world_spec_sha256") != sha256_file(
        ROOT / "task" / "WORLD_SPEC.json"
    ):
        failures.append("semantic_protocol:world_spec")
    criterion_ids = [row.get("id") for row in protocol.get("criteria", [])]
    if criterion_ids != [f"R{index:02d}" for index in range(1, 13)]:
        failures.append("semantic_criterion_order")
    if evaluator.get("required_ledger_requirements") != criterion_ids:
        failures.append("mechanical_semantic_criterion_alignment")
    if "current candidate-bound final check" not in str(protocol.get("readiness_rule")):
        failures.append("candidate_bound_readiness")
    if "Submission behavior never changes this rule" not in str(protocol.get("readiness_rule")):
        failures.append("submission_not_readiness")
    if world_spec.get("task_id") != TASK_ID:
        failures.append("world_spec_binding")

    if set(CONFIGURATIONS) != {"D0_DETACHED", "A1_COUPLED"}:
        failures.append("comparator_identity")
    if not {"read_batch", "upsert_decision_section", "run_check", "submit"}.issubset(
        set(ordinary_actions())
    ):
        failures.append("complete_action_loop")
    for name, fixture in (
        ("basic", basic_fixture),
        ("measured", measured_fixture),
    ):
        if fixture.get("passed") is not True or fixture.get("gpu_authorized") is not False:
            failures.append(f"fixture:{name}")
    fixture_hashes = measured_fixture.get("exact_apparatus_file_hashes", {})
    for relative in (
        "tools/dry_run_measured_interaction.py",
        "tools/run_measured_interaction.py",
        "task/TASK_SOURCE_LOCK.json",
        "MEASURED_INTERACTION_CONTRACT.json",
    ):
        if fixture_hashes.get(relative) != sha256_file(ROOT / relative):
            failures.append(f"measured_fixture_hash:{relative}")
    cells = measured_fixture.get("cells")
    if not isinstance(cells, list) or {row.get("configuration_id") for row in cells} != set(CONFIGURATIONS):
        failures.append("measured_fixture:configuration_parity")
        cells = []
    for row in cells:
        configuration_id = str(row.get("configuration_id"))
        if row.get("terminal_disposition") != "submitted":
            failures.append(f"measured_fixture:{configuration_id}:terminal")
        if int(row.get("check_count", 0)) != 2:
            failures.append(f"measured_fixture:{configuration_id}:check_repair_recheck")
        if int(row.get("candidate_effects_delivered", 0)) < 1:
            failures.append(f"measured_fixture:{configuration_id}:effect_uptake")
        budget = row.get("trajectory_budget", {})
        if budget.get("milestone_call") is None or int(budget.get("remaining_calls_in_current_window", 0)) < 1:
            failures.append(f"measured_fixture:{configuration_id}:postconstruction_tail")
        projection = row.get("mechanical_final_evaluation", {}).get("projection", {})
        if projection.get("closure_readiness") != "not_adjudicated":
            failures.append(f"measured_fixture:{configuration_id}:mechanical_precheck")

    budget = ConstructionBudget()
    if (
        budget.maximum_preconstruction_calls != 22
        or budget.postconstruction_calls != 8
        or budget.maximum_total_calls != 30
    ):
        failures.append("trajectory_budget")
    # The clean tail needs four actor decisions: receive construction effect +
    # check, receive check + repair, receive repair + recheck, receive recheck +
    # close. Eight freezes four additional decisions for targeted repairs or
    # expression loss without outcome-dependent extension.
    minimum_clean_tail = 4
    if budget.postconstruction_calls < minimum_clean_tail * 2:
        failures.append("postconstruction_allowance")

    expected_screen = {
        "run_id": screen.RUN_ID,
        "scope": screen.SCOPE,
        "seed": screen.SEED,
        "maximum_actor_calls": screen.MAX_CALLS,
        "maximum_serialized_tokens": screen.MAX_SERIALIZED,
        "prompt_limit": screen.PROMPT_LIMIT,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, value in expected_screen.items():
        if screen_contract.get(key) != value:
            failures.append(f"screen_contract:{key}")
    if screen_request.get("authorized") is not False or screen_request.get("scope") != screen.SCOPE:
        failures.append("screen_authorization_placeholder")
    expected_measured = {
        "run_id": measured.RUN_ID,
        "scope": measured.SCOPE,
        "configuration_order": list(measured.CONFIGURATION_ORDER),
        "maximum_preconstruction_actor_calls_per_configuration": measured.MAX_PRECONSTRUCTION_CALLS_PER_CELL,
        "postconstruction_actor_calls_per_configuration": measured.POSTCONSTRUCTION_CALLS_PER_CELL,
        "maximum_actor_calls_per_configuration": measured.MAX_ACTOR_CALLS_PER_CELL,
        "maximum_maintenance_calls_per_configuration": measured.MAX_MAINTENANCE_CALLS_PER_CELL,
        "maximum_provider_calls": measured.MAX_PROVIDER_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, value in expected_measured.items():
        if measured_contract.get(key) != value:
            failures.append(f"measured_contract:{key}")
    if measured_request.get("authorized") is not False:
        failures.append("measured_authorization_placeholder")
    if (
        profile.get("screen_seed") != screen.SEED
        or profile.get("measured_actor_seed") != measured.ACTOR_SEED
        or profile.get("measured_maintenance_seed") != measured.MAINTENANCE_SEED
    ):
        failures.append("model_profile_seed_binding")

    if geometry.get("activation_qualified") is not False:
        failures.append("offline_activation_overclaim")
    if int(geometry.get("source_corpus_tokens", 0)) <= 25_088:
        failures.append("task_world_not_large")
    try:
        verify_pressure_handoff(ROOT)
    except RuntimeError:
        pass
    else:
        failures.append("placeholder_pressure_handoff_accepted")
    if (ROOT / "runs" / screen.RUN_ID).exists():
        failures.append("pressure_screen_run_root_exists")
    if (ROOT / "runs" / measured.RUN_ID).exists():
        failures.append("measured_run_root_exists")

    with tempfile.TemporaryDirectory() as temporary:
        world = ArchitectureWorld(ROOT / "task", Path(temporary))
        if len(world.sources) != 14:
            failures.append("world_source_count")
        if tuple(DECISION_HEADINGS) != tuple(evaluator.get("decision_headings", [])):
            failures.append("decision_heading_binding")

    result = {
        "schema": "northstar-transfer-stage0-preflight-v0",
        "passed": not failures,
        "failures": sorted(set(failures)),
        "task_id": TASK_ID,
        "fresh_task_world_qualified": not any(
            item.startswith(("fresh_task", "source_", "historical_", "world_"))
            for item in failures
        ),
        "source_count": len(custody),
        "source_bytes": sum(int(row.get("size_bytes", 0)) for row in custody),
        "source_corpus_tokens": geometry.get("source_corpus_tokens"),
        "comparator_ids": list(CONFIGURATIONS),
        "provider_free_complete_loop_qualified": basic_fixture.get("passed") is True
        and measured_fixture.get("passed") is True,
        "candidate_bound_evaluator_frozen": evaluator.get("task_id") == TASK_ID
        and protocol.get("task_id") == TASK_ID,
        "closure_readiness_requires_independent_adjudication": True,
        "maximum_preconstruction_actor_calls_per_configuration": 22,
        "postconstruction_actor_calls_per_configuration": 8,
        "minimum_clean_postconstruction_path_calls": minimum_clean_tail,
        "additional_postconstruction_allowance_calls": 4,
        "maximum_actor_calls_per_configuration": 30,
        "gpu_authorized": False,
        "offline_apparatus_qualified": not failures,
        "authentic_interaction_activation_qualified": False,
        "activation_status": "requires_frozen_live_ordinary_pressure_screen",
        "measured_interaction_eligible": False,
        "next_live_gate": screen.RUN_ID,
        "claim_limit": "Offline Stage 0 qualifies the fresh world, two viable interacting configurations, evaluator, budgets, runners, and fixtures. It does not establish authentic model-driven pressure or authorize any provider call.",
    }
    write_json(ROOT / "STAGE0_PREFLIGHT.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
