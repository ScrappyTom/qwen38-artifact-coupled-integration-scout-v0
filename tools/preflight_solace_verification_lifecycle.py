from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import write_json
from reactive_runtime.canonical import sha256_file
from tools.offline_tokenizer import OfflineTokenizer
from tools.run_solace_verification_lifecycle import (
    CONTEXT_TOKENS,
    MAX_ACTOR_CALLS_PER_CELL,
    MAX_PROVIDER_CALLS,
    MAX_TOKENS,
    PROMPT_LIMIT,
)
from tools.solace_verification_lifecycle_stage0 import (
    CONFIGURATION_ORDER,
    build_stage0,
    repair_patch_action,
)


OUTPUT = ROOT / "SOLACE_VERIFICATION_LIFECYCLE_PREFLIGHT.json"
DONOR_LOCK = ROOT / "SOLACE_VERIFICATION_LIFECYCLE_DONOR_LOCK.json"
EXPECTED_BLOCKER_PREFIXES = {
    "decision_heading_order",
    "Q02_hydraulics",
    "Q03_sampling",
    "Q04_pumping",
    "Q09_observation",
}


def build(*, write_output: bool = True) -> dict[str, Any]:
    value = build_stage0()
    tokenizer = OfflineTokenizer()
    patch_text = json.dumps(repair_patch_action(), ensure_ascii=False, separators=(",", ":"))
    patch_tokens = tokenizer.count_text(patch_text)
    failures: list[str] = []
    if tuple(value["configuration_order"]) != CONFIGURATION_ORDER:
        failures.append("configuration_order_mismatch")
    if value["donor"]["register_claims"] != 20:
        failures.append("donor_register_not_20_claims")
    donor_lock = json.loads(DONOR_LOCK.read_text(encoding="utf-8"))
    for relative, expected_hash in donor_lock["files"].items():
        path = ROOT / relative
        if not path.is_file() or sha256_file(path) != expected_hash:
            failures.append(f"donor_lock_mismatch:{relative}")
    for configuration_id, geometry in value["geometry"].items():
        if geometry["candidate_sha256"] != value["donor"]["candidate_sha256"]:
            failures.append(f"{configuration_id}_candidate_mismatch")
        if geometry["prompt_tokens"] > PROMPT_LIMIT:
            failures.append(f"{configuration_id}_initial_prompt_over_limit")
        if geometry["prompt_tokens"] + MAX_TOKENS > CONTEXT_TOKENS:
            failures.append(f"{configuration_id}_response_reserve_not_preserved")
    final_hashes: set[str] = set()
    for fixture in value["provider_free_lifecycles"]:
        blockers = {row.split(":", 1)[0] for row in fixture["initial_blocking_requirements"]}
        if blockers != EXPECTED_BLOCKER_PREFIXES:
            failures.append(f"{fixture['configuration_id']}_blocker_set_mismatch")
        if fixture["initial_check_passed"]:
            failures.append(f"{fixture['configuration_id']}_donor_unexpectedly_passed")
        if not fixture["prior_check_stale_after_patch"]:
            failures.append(f"{fixture['configuration_id']}_stale_binding_missing")
        if not fixture["recheck_passed"] or fixture["recheck_blocking_requirements"]:
            failures.append(f"{fixture['configuration_id']}_recheck_failed")
        if not fixture["submitted"]:
            failures.append(f"{fixture['configuration_id']}_submission_fixture_failed")
        final_hashes.add(fixture["patched_candidate_sha256"])
    if len(final_hashes) != 1:
        failures.append("provider_free_final_candidates_diverged")
    if patch_tokens > MAX_TOKENS:
        failures.append("bounded_patch_exceeds_response_budget")
    if MAX_PROVIDER_CALLS != len(CONFIGURATION_ORDER) * MAX_ACTOR_CALLS_PER_CELL:
        failures.append("provider_budget_arithmetic")
    value.update(
        {
            "passed": not failures,
            "failures": failures,
            "patch_transport": {
                "edit_count": len(repair_patch_action()["edits"]),
                "serialized_tokens": patch_tokens,
                "maximum_completion_tokens": MAX_TOKENS,
                "fits_response_budget": patch_tokens <= MAX_TOKENS,
            },
            "trajectory_budget": {
                "minimum_clean_path_calls": 4,
                "minimum_clean_path": ["run_check", "patch_decision", "run_check", "submit"],
                "additional_bounded_repair_or_recovery_calls": 6,
                "expression_failure_allowance": 2,
                "maximum_actor_calls_per_cell": MAX_ACTOR_CALLS_PER_CELL,
                "maximum_provider_calls": MAX_PROVIDER_CALLS,
                "attempts_per_call": 1,
                "retries": 0,
            },
            "gpu_authorized": False,
            "donor_lock_sha256": sha256_file(DONOR_LOCK),
        }
    )
    if write_output:
        write_json(OUTPUT, value)
    return value


def main() -> int:
    value = build()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
