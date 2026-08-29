from __future__ import annotations

# ruff: noqa: E402

import json
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json

from interaction_scout.lifecycle import (
    BASELINE_CONFIGURATION,
    SCAFFOLD_SLOT,
    TREATMENT_CONFIGURATION,
    VERIFICATION_SLOT,
)
from interaction_scout.provider_free import run_provider_free_lifecycle
from interaction_scout.system import (
    CONFIGURATION_ORDER,
    MAXIMUM_ACTOR_CALLS,
    MAXIMUM_MAINTENANCE_CALLS,
    MAXIMUM_PROVIDER_CALLS,
    MAXIMUM_SERIALIZED_TOKENS,
    RUN_ID,
    interaction_execution_manifest,
)


OUTPUT = ROOT / "TRELLIS_REFACTORED_INTERACTION_STAGE0.json"


def _summary(result: dict[str, Any]) -> dict[str, Any]:
    state = result["kernel"].project()
    lifecycle = result["lifecycle"]
    request_bindings = result["request_bindings"]
    exposed_slots = sorted(
        {
            row["state_slot_id"]
            for binding in request_bindings
            for row in binding["state_slot_exposures"]
        }
    )
    return {
        **result["summary"],
        "checkpoint_dispositions": [row.value for row in result["dispositions"]],
        "exposed_state_slots": exposed_slots,
        "final_candidate_sha256": result["adapter"].world.candidate_sha256,
        "final_delivery_states": {
            result_id: row.delivery_state.value
            for result_id, row in state.results.items()
        },
        "maintenance_serialized_tokens": lifecycle.maintenance_serialized_tokens,
        "register_claims": len(lifecycle.register.claims),
        "scaffold_active_at_end": lifecycle.scaffold_active,
        "scaffold_ever_exposed": lifecycle.scaffold_ever_exposed,
    }


def build() -> dict[str, Any]:
    contract = json.loads(
        (ROOT / "TRELLIS_REFACTORED_INTERACTION_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    request = json.loads(
        (ROOT / "TRELLIS_REFACTORED_INTERACTION_AUTHORIZATION_REQUEST.json").read_text(
            encoding="utf-8"
        )
    )
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        results = {
            configuration_id: run_provider_free_lifecycle(
                ROOT,
                configuration_id=configuration_id,
                output_root=temp_root / configuration_id,
            )
            for configuration_id in CONFIGURATION_ORDER
        }
        cells = {
            configuration_id: _summary(result)
            for configuration_id, result in results.items()
        }
    failures: list[str] = []
    for configuration_id, row in cells.items():
        if row["terminal"] != "completed" or row["submitted"] is not True:
            failures.append(f"{configuration_id}:provider_free_completion")
        if row["final_check_passed"] is not True:
            failures.append(f"{configuration_id}:provider_free_recheck")
        if row["relief_events"] < 1:
            failures.append(f"{configuration_id}:pressure_relief_not_exercised")
        if "current_candidate" not in row["exposed_state_slots"]:
            failures.append(f"{configuration_id}:candidate_slot_not_exposed")
        if VERIFICATION_SLOT not in row["exposed_state_slots"]:
            failures.append(f"{configuration_id}:verification_slot_not_exposed")
    treatment = cells[TREATMENT_CONFIGURATION]
    baseline = cells[BASELINE_CONFIGURATION]
    if baseline["maintenance_calls"] != 0 or SCAFFOLD_SLOT in baseline["exposed_state_slots"]:
        failures.append("baseline_semantic_treatment_present")
    if treatment["maintenance_calls"] < 1 or treatment["register_claims"] < 1:
        failures.append("treatment_semantic_path_not_exercised")
    if treatment["scaffold_ever_exposed"] is not True or treatment["scaffold_active_at_end"] is not False:
        failures.append("treatment_scaffold_lifecycle_invalid")
    if contract["run_id"] != RUN_ID or request["run_id"] != RUN_ID:
        failures.append("run_id_mismatch")
    if contract["configuration_order"] != list(CONFIGURATION_ORDER):
        failures.append("configuration_order_mismatch")
    return {
        "authorization_limits": {
            "maximum_actor_calls": MAXIMUM_ACTOR_CALLS,
            "maximum_maintenance_calls": MAXIMUM_MAINTENANCE_CALLS,
            "maximum_provider_calls": MAXIMUM_PROVIDER_CALLS,
            "maximum_serialized_tokens": MAXIMUM_SERIALIZED_TOKENS,
        },
        "cells": cells,
        "claim_limits": [
            "Scripted outputs qualify mechanics and transport, not Qwen behavior.",
            "The live causal unit is the whole configuration, not the scaffold alone.",
            "The first live tranche pauses after twelve actor calls per configuration.",
            "Cross-world transfer remains required after any positive Trellis signal.",
        ],
        "configuration_order": list(CONFIGURATION_ORDER),
        "contract_sha256": sha256_file(
            ROOT / "TRELLIS_REFACTORED_INTERACTION_CONTRACT.json"
        ),
        "execution_manifest": interaction_execution_manifest(ROOT),
        "failures": failures,
        "passed": not failures,
        "run_id": RUN_ID,
        "schema": "trellis-refactored-interaction-stage0-v0",
    }


def main() -> int:
    value = build()
    write_json(OUTPUT, value)
    if not value["passed"]:
        raise RuntimeError(f"Stage 0 failed: {value['failures']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
