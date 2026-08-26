from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.actions import action_json_schema
from reactive_runtime.anchored_provenance import (
    AnchoredProvenanceRegister,
    admit_anchored_delta,
    anchored_delta_messages,
)
from reactive_runtime.configuration import (
    ANCHORED_RELATIONAL_CONFIGURATIONS,
    anchored_relational_actor_actions,
)
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
from reactive_runtime.solace_boundary import verify_solace_pressure_handoff
from reactive_runtime.solace_world import SolaceWorld
from tools.offline_tokenizer import OfflineTokenizer
from tools.run_solace_anchored_interaction import (
    CONTEXT_TOKENS,
    DELTA_TOKEN_BUDGET,
    MAX_ACTOR_CALLS_PER_CELL,
    MAX_MAINTENANCE_CALLS_L1,
    MAX_PROVIDER_CALLS,
    POSTCONSTRUCTION_CALLS_PER_CELL,
    PRESSURE_RUN,
    PROMPT_LIMIT,
    TASK,
)


OUTPUT = ROOT / "SOLACE_ANCHORED_INTERACTION_PREFLIGHT.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def delta_text(result_id: str, versions: dict[str, str], *, valid: bool) -> str:
    anchor = (
        "Only the county health officer may lift a do-not-drink order"
        if valid
        else "This exact anchor is absent from the source"
    )
    return "\n".join(
        (
            "# Anchored provenance-local delta",
            "## CLAIM AURORA_AUTHORITY",
            "SLOT_SOURCE: AURORA",
            f"SOURCE_VERSION: {versions['AURORA']}",
            f"EVIDENCE_RESULT: {result_id}",
            f"EVIDENCE_ANCHOR: {anchor}",
            "MODE: source_reported_fact",
            "ATTRIBUTION: owner_source_reported",
            "REFERENTS: NONE",
            "AUTHORITY: non_authoritative_derivative",
            "STATEMENT: AURORA reports that only the county health officer may lift the do-not-drink order.",
        )
    ) + "\n"


def build(repository_root: Path = ROOT, *, write_output: bool = True) -> dict[str, Any]:
    root = repository_root.resolve()
    handoff = verify_solace_pressure_handoff(root)
    boundary = load(PRESSURE_RUN / "PRESSURE_BOUNDARY.json")
    tokenizer = OfflineTokenizer()
    messages = [dict(row) for row in boundary["messages"]]
    ledger = ResultLedger.from_dict(boundary["result_ledger"])
    step = positive_savings_first_fit_step(
        messages=messages,
        ledger=ledger,
        prompt_limit=PROMPT_LIMIT,
        count_messages=tokenizer.count_messages,
        protected_result_ids=(str(boundary["pending_result_id"]),),
    )
    selected = [ledger.get(result_id) for result_id in step.selected_result_ids]
    with tempfile.TemporaryDirectory() as temporary:
        world = SolaceWorld(TASK, Path(temporary), count_text=tokenizer.count_text)
        maintenance_messages = anchored_delta_messages(
            task_text=(TASK / "TASK.md").read_text(encoding="utf-8"),
            register=AnchoredProvenanceRegister(),
            newly_externalized=selected,
            source_versions=world.source_versions,
        )
        maintenance_prompt_tokens = tokenizer.count_messages(maintenance_messages)
        catalog_value = load(TASK / "SOURCE_CATALOG.json")
        catalog = {
            str(row["source_id"]): row for row in catalog_value.get("sources", [])
        }
        valid_admission = admit_anchored_delta(
            delta_text(selected[0].result_id, world.source_versions, valid=True),
            count_text=tokenizer.count_text,
            source_catalog=catalog,
            task_root=TASK,
            newly_externalized=selected,
            current_source_versions=world.source_versions,
        )
        valid_transition = AnchoredProvenanceRegister().apply(
            valid_admission,
            current_source_versions=world.source_versions,
            count_text=tokenizer.count_text,
        )
        zero_admission = admit_anchored_delta(
            delta_text(selected[0].result_id, world.source_versions, valid=False),
            count_text=tokenizer.count_text,
            source_catalog=catalog,
            task_root=TASK,
            newly_externalized=selected,
            current_source_versions=world.source_versions,
        )
        zero_transition = AnchoredProvenanceRegister().apply(
            zero_admission,
            current_source_versions=world.source_versions,
            count_text=tokenizer.count_text,
        )
        action_schemas = {
            configuration_id: action_json_schema(
                anchored_relational_actor_actions(configuration_id),
                source_ids=world.sources,
                reopen_result_ids=tuple(step.selected_result_ids),
                decision_headings=world.decision_headings,
                schema_name=f"solace_{configuration_id.casefold()}_actor_action_v0",
            )
            for configuration_id in ANCHORED_RELATIONAL_CONFIGURATIONS
        }
        evaluation = world._run_check("PREFLIGHT-EVALUATION").metadata[
            "check_projection"
        ]
    failures: list[str] = []
    if handoff.get("interaction_trigger_qualified") is not True:
        failures.append("handoff_not_qualified")
    if list(step.selected_result_ids) != ["RESULT-001"] or not step.feasible:
        failures.append("common_first_fit_mismatch")
    if step.prompt_tokens != 18_595:
        failures.append("common_relief_token_mismatch")
    if maintenance_prompt_tokens + DELTA_TOKEN_BUDGET > CONTEXT_TOKENS:
        failures.append("maintenance_prompt_infeasible")
    if valid_admission.disposition != "full_admission":
        failures.append("valid_claim_not_admitted")
    if not valid_transition.changed or len(valid_transition.register.claims) != 1:
        failures.append("valid_register_transition_failed")
    if zero_admission.disposition != "zero_valid":
        failures.append("zero_valid_not_observed")
    if zero_transition.changed:
        failures.append("zero_valid_changed_register")
    if set(action_schemas) != set(ANCHORED_RELATIONAL_CONFIGURATIONS):
        failures.append("action_schema_missing")
    if evaluation.get("closure_readiness") != "not_ready":
        failures.append("initial_readiness_not_frozen_not_ready")
    if MAX_PROVIDER_CALLS != 2 * MAX_ACTOR_CALLS_PER_CELL + MAX_MAINTENANCE_CALLS_L1:
        failures.append("provider_budget_arithmetic")
    value = {
        "schema": "solace-anchored-interaction-preflight-v0",
        "provider_calls": 0,
        "passed": not failures,
        "failures": failures,
        "common_pressure": {
            "ordinary_prompt_tokens": boundary["ordinary_prospective_prompt_tokens"],
            "selected_result_ids": list(step.selected_result_ids),
            "relief_prompt_tokens": step.prompt_tokens,
            "pending_result_id": boundary["pending_result_id"],
        },
        "maintenance": {
            "prompt_tokens": maintenance_prompt_tokens,
            "maximum_completion_tokens": DELTA_TOKEN_BUDGET,
            "fits_context": maintenance_prompt_tokens + DELTA_TOKEN_BUDGET
            <= CONTEXT_TOKENS,
            "valid_admission": asdict(valid_admission),
            "valid_transition_changed": valid_transition.changed,
            "zero_valid_admission": asdict(zero_admission),
            "zero_valid_transition_changed": zero_transition.changed,
        },
        "action_schema_configurations": sorted(action_schemas),
        "initial_external_evaluation": evaluation,
        "budgets": {
            "maximum_actor_calls_per_cell": MAX_ACTOR_CALLS_PER_CELL,
            "postconstruction_calls": POSTCONSTRUCTION_CALLS_PER_CELL,
            "maximum_maintenance_calls_L1": MAX_MAINTENANCE_CALLS_L1,
            "maximum_provider_calls": MAX_PROVIDER_CALLS,
        },
        "claim_limit": "Provider-free qualification of the exact common fork, host/model provenance allocation, partial/zero-valid fallback, action surfaces, evaluator, and budgets. It establishes no model expression or downstream utility.",
    }
    if write_output:
        from reactive_runtime.canonical import write_json

        write_json(OUTPUT, value)
    return value


def main() -> int:
    value = build()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
