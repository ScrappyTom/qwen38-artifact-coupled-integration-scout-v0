from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import write_json


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def verify() -> dict:
    failures: list[str] = []
    preflight = load(ROOT / "ORCHARD_PHASE_LIFECYCLE_STAGE0_PREFLIGHT.json")
    lock = load(ROOT / "task_orchard" / "TASK_SOURCE_LOCK.json")
    contract = load(ROOT / "ORCHARD_PRESSURE_SCREEN_CONTRACT.json")
    request = load(ROOT / "ORCHARD_PRESSURE_SCREEN_AUTHORIZATION_REQUEST.json")
    design = load(ROOT / "ORCHARD_INTERACTION_DESIGN.json")

    if preflight.get("passed") is not True or preflight.get("provider_calls") != 0:
        failures.append("preflight_not_provider_free_pass")
    if preflight.get("gpu_authorized") is not False:
        failures.append("preflight_gpu_authority_present")
    if len(lock.get("source_custody", [])) != 13:
        failures.append("source_custody_count")
    pressure = preflight.get("prospective_pressure_opportunity") or {}
    if not (
        pressure.get("ordinary_prompt_tokens", 0) > 20_992
        and pressure.get("relieved_prompt_tokens", 99_999) <= 20_992
        and pressure.get("selected_result_ids") == ["RESULT-001"]
    ):
        failures.append("prospective_pressure_or_relief")
    fixtures = preflight.get("provider_free_lifecycles", [])
    if len(fixtures) != 2 or not all(row.get("recheck_passed") and row.get("submitted") for row in fixtures):
        failures.append("provider_free_lifecycle")
    if fixtures and len(fixtures) == 2 and fixtures[0].get("final_candidate_sha256") != fixtures[1].get("final_candidate_sha256"):
        failures.append("provider_free_candidate_parity")
    if not all(row.get("caught") for row in preflight.get("relationship_red_team", [])):
        failures.append("relationship_red_team")
    if contract.get("semantic_maintenance_present") is not False or contract.get("treatment_present") is not False:
        failures.append("screen_contains_treatment")
    if contract.get("maximum_actor_calls") != 30 or request.get("maximum_model_calls") != 30:
        failures.append("screen_budget_mismatch")
    if contract.get("gpu_authorized") is not False or request.get("authorized") is not False:
        failures.append("authorization_not_inert")
    if design.get("component_isolation_claim") is not False or design.get(
        "current_next_operation"
    ) not in {
        "treatment_free_pressure_screen",
        "separately_authorized_frozen_F0_P1_measured_interaction",
    }:
        failures.append("design_scope")
    runner = (ROOT / "tools" / "run_orchard_pressure_screen.py").read_text(encoding="utf-8")
    for literal in (
        "2026-08-27-orchard-phase-lifecycle-pressure-screen-v0",
        "orchard_phase_lifecycle_pressure_screen_v0",
        "runner.MAX_CALLS = 30",
        "runner.MIN_QUALIFYING_SOURCES = 10",
        "runner.MIN_QUALIFYING_DOMAINS = 10",
    ):
        if literal not in runner:
            failures.append(f"runner_missing:{literal}")
    return {
        "schema": "orchard-phase-lifecycle-stage0-audit-v0",
        "passed": not failures,
        "failures": failures,
        "provider_calls": 0,
        "gpu_authorized": False,
        "source_count": len(lock.get("source_custody", [])),
        "prospective_pressure_tokens": pressure.get("ordinary_prompt_tokens"),
        "prospective_relieved_tokens": pressure.get("relieved_prompt_tokens"),
        "provider_free_cells": len(fixtures),
        "relationship_red_team_cases": len(preflight.get("relationship_red_team", [])),
        "next_operation": design.get("current_next_operation"),
    }


if __name__ == "__main__":
    value = verify()
    write_json(ROOT / "ORCHARD_STAGE0_AUDIT.json", value)
    print(json.dumps(value, indent=2, sort_keys=True))
    raise SystemExit(0 if value["passed"] else 1)
