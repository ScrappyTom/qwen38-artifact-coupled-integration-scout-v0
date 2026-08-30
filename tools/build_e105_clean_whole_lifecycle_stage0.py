from __future__ import annotations

# ruff: noqa: E402

import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from host_refactor.whole_lifecycle.provider_free import (
    run_provider_free_complete_lifecycle,
)
from host_refactor.whole_lifecycle.readiness import adjudicate_readiness
from host_refactor.whole_lifecycle.system import (
    CONFIGURATION_LABEL,
    INITIAL_MAXIMUM_ACTOR_CALLS,
    INITIAL_MAXIMUM_MAINTENANCE_CALLS,
    INITIAL_MAXIMUM_PROVIDER_CALLS,
    INITIAL_MAXIMUM_SERIALIZED_TOKENS,
    MAXIMUM_CUMULATIVE_ACTOR_CALLS,
    MAXIMUM_CUMULATIVE_MAINTENANCE_CALLS,
    MAXIMUM_CUMULATIVE_PROVIDER_CALLS,
    MAXIMUM_CUMULATIVE_SERIALIZED_TOKENS,
    RUN_ID,
    SCOPE,
    execution_manifest,
)
from reactive_runtime.canonical import load_json, sha256_file, write_json
from reactive_runtime.task_decision_evaluator import evaluate
from tools.offline_tokenizer import OfflineTokenizer


OUTPUT = ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_STAGE0.json"
CONTRACT = ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CONTRACT.json"
REQUEST = ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_AUTHORIZATION_REQUEST.json"


def build() -> dict[str, Any]:
    contract = load_json(CONTRACT)
    request = load_json(REQUEST)
    tokenizer = OfflineTokenizer()
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temp:
        complete = run_provider_free_complete_lifecycle(
            ROOT,
            output_root=Path(temp) / "complete-lifecycle",
        )
    expected_headings = [
        "Authority, scope, and operating states",
        "Heat triggers and geographic staging",
        "Power, water, and cooling continuity",
        "Clinical, shelter, and accessibility operations",
        "Transit, communications, logistics, and staffing",
        "Execution, rollback, verification, and closure",
    ]
    if contract["run_id"] != RUN_ID or request["run_id"] != RUN_ID:
        failures.append("run_id_mismatch")
    if request["scope"] != SCOPE:
        failures.append("scope_mismatch")
    if contract["configuration"] != CONFIGURATION_LABEL:
        failures.append("configuration_mismatch")
    if contract["initial_state"]["e103_resumed"] is not False:
        failures.append("historical_route_imported")
    if complete["terminal"] != "completed" or complete["submitted"] is not True:
        failures.append("provider_free_completion_failed")
    if complete["final_evaluation"].get("passed") is not True:
        failures.append("provider_free_final_evaluation_failed")
    if complete["readiness_adjudication"]["closure_readiness"] != "ready":
        failures.append("provider_free_external_readiness_not_ready")
    checks = complete["check_sequence"]
    if len(checks) != 2 or checks[0]["passed"] is not False or checks[1]["passed"] is not True:
        failures.append("provider_free_check_repair_recheck_failed")
    if not complete["external_check_result_ids"]:
        failures.append("e104_check_turnover_not_exercised")
    if not complete["candidate_effect_receipt_ids"]:
        failures.append("e97_effect_turnover_not_exercised")
    if complete["decision_headings"] != expected_headings:
        failures.append("exact_heading_contract_failed")
    if complete["glued_heading_present"] is not False:
        failures.append("section_boundary_corruption")
    if complete["relief_events"] < 1:
        failures.append("pressure_relief_not_exercised")
    if complete["scaffold_ever_exposed"] is not True:
        failures.append("construction_scaffold_not_exposed")
    if complete["scaffold_active_at_end"] is not False:
        failures.append("scaffold_not_demoted_for_verification")
    if complete["actor_calls"] > MAXIMUM_CUMULATIVE_ACTOR_CALLS:
        failures.append("actor_budget_exceeded")
    if complete["maintenance_calls"] > MAXIMUM_CUMULATIVE_MAINTENANCE_CALLS:
        failures.append("maintenance_budget_exceeded")
    if complete["provider_calls"] > MAXIMUM_CUMULATIVE_PROVIDER_CALLS:
        failures.append("provider_budget_exceeded")
    if complete["serialized_tokens"] > MAXIMUM_CUMULATIVE_SERIALIZED_TOKENS:
        failures.append("serialized_budget_exceeded")
    initial_limits = {
        "maximum_actor_calls": INITIAL_MAXIMUM_ACTOR_CALLS,
        "maximum_maintenance_calls": INITIAL_MAXIMUM_MAINTENANCE_CALLS,
        "maximum_provider_calls": INITIAL_MAXIMUM_PROVIDER_CALLS,
        "maximum_serialized_tokens": INITIAL_MAXIMUM_SERIALIZED_TOKENS,
    }
    if any(request[key] != value for key, value in initial_limits.items()):
        failures.append("initial_authorization_limits_mismatch")
    initial_candidate = ROOT / "task_trellis" / "candidate"
    initial_evaluation = evaluate(ROOT / "task_trellis", initial_candidate)
    initial_readiness = adjudicate_readiness(
        ROOT,
        initial_evaluation,
        current_candidate_sha256=str(initial_evaluation["candidate_sha256"]),
    )
    if initial_evaluation.get("closure_readiness") != "not_ready":
        failures.append("initial_readiness_not_frozen_negative")
    if initial_readiness["closure_readiness"] != "not_ready":
        failures.append("initial_external_readiness_not_frozen_negative")
    base_messages = [
        {"role": "system", "content": (ROOT / "task_trellis" / "SYSTEM.md").read_text(encoding="utf-8")},
        {"role": "user", "content": (ROOT / "task_trellis" / "TASK.md").read_text(encoding="utf-8")},
    ]
    return {
        "schema": "trellis-clean-whole-lifecycle-stage0-v0",
        "run_id": RUN_ID,
        "configuration": CONFIGURATION_LABEL,
        "provider_calls": 0,
        "gpu_model_calls": 0,
        "contract_sha256": sha256_file(CONTRACT),
        "authorization_request_sha256": sha256_file(REQUEST),
        "execution_manifest": execution_manifest(ROOT),
        "initial_task_prompt_tokens": tokenizer.count_messages(base_messages),
        "initial_evaluation": {
            "candidate_sha256": initial_evaluation.get("candidate_sha256"),
            "closure_readiness": initial_evaluation.get("closure_readiness"),
            "passed": initial_evaluation.get("passed"),
        },
        "initial_readiness_adjudication": initial_readiness,
        "first_live_tranche_limits": initial_limits,
        "complete_provider_free_lifecycle": complete,
        "failures": failures,
        "passed": not failures,
        "live_authorized": False,
        "automatic_continuation": False,
        "claim_limit": "Provider-free completion qualifies reachability and exact lifecycle mechanics, not live Qwen utility.",
    }


def main() -> int:
    value = build()
    write_json(OUTPUT, value)
    if not value["passed"]:
        raise RuntimeError(f"E105 Stage 0 failed: {value['failures']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
