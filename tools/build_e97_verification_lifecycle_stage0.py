from __future__ import annotations

# ruff: noqa: E402

import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from host_refactor.lifecycle_scout.fixtures import (
    DonorLifecycleActorFixture,
    NoOpMaintenanceFixture,
)
from host_refactor.lifecycle_scout.migration import (
    DONOR_CANDIDATE_SHA256,
    EXPECTED_PENDING_EFFECT,
    migrate_e96_donor,
)
from host_refactor.lifecycle_scout.system import (
    MAXIMUM_ADDITIONAL_ACTOR_CALLS,
    MAXIMUM_ADDITIONAL_MAINTENANCE_CALLS,
    MAXIMUM_ADDITIONAL_PROVIDER_CALLS,
    MAXIMUM_ADDITIONAL_SERIALIZED_TOKENS,
    RUN_ID,
    lifecycle_scout_execution_manifest,
)
from host_refactor.model import EventKind, TerminalCode
from interaction_scout.live_path import run_interaction_tranche
from reactive_runtime.canonical import load_json, sha256_file, write_json
from reactive_runtime.task_decision_evaluator import evaluate
from tools.offline_tokenizer import OfflineTokenizer


OUTPUT = ROOT / "TRELLIS_E97_VERIFICATION_LIFECYCLE_STAGE0.json"
CONTRACT = ROOT / "TRELLIS_E97_VERIFICATION_LIFECYCLE_SCOUT_CONTRACT.json"
REQUEST = ROOT / "TRELLIS_E97_VERIFICATION_LIFECYCLE_SCOUT_AUTHORIZATION_REQUEST.json"
READINESS = ROOT / "TRELLIS_E97_DONOR_READINESS_ADJUDICATION.json"


def _check_rows(kernel: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for projected in kernel.project().results.values():
        if projected.result.result_kind != "check_observation":
            continue
        check = projected.result.metadata.get("check_projection")
        if isinstance(check, Mapping):
            rows.append(dict(check))
    return rows


def build() -> dict[str, Any]:
    tokenizer = OfflineTokenizer()
    readiness = load_json(READINESS)
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        migration = migrate_e96_donor(
            repository_root=ROOT,
            trajectory_root=temp_root / "trajectory",
            count_messages=tokenizer.count_messages,
            count_text=tokenizer.count_text,
            maintenance_complete=NoOpMaintenanceFixture(),
            checkpoint_output=temp_root / "MIGRATED_CHECKPOINT.json",
            receipt_output=temp_root / "MIGRATION_RECEIPT.json",
        )
        initial_evaluation = evaluate(
            ROOT / "task_trellis", migration.adapter.world.candidate_root
        )
        actor = DonorLifecycleActorFixture(
            migration.adapter,
            tokenizer.count_messages,
            tokenizer.count_text,
        )
        kernel = migration.kernel
        counters = migration.counters
        parent = temp_root / "MIGRATED_CHECKPOINT.json"
        tranches = []
        for tranche_index in range(1, 4):
            tranche = run_interaction_tranche(
                orchestrator=migration.orchestrator,
                kernel=kernel,
                counters=counters,
                actor_complete=actor,
                run_root=temp_root / f"tranche-{tranche_index:03d}",
                parent_checkpoint_path=parent,
            )
            tranches.append(tranche)
            kernel = tranche.kernel
            counters = tranche.counters
            parent = tranche.checkpoint_path
            if tranche.disposition is not TerminalCode.CHECKPOINT_PAUSE:
                break
        final_evaluation = evaluate(
            ROOT / "task_trellis", migration.adapter.world.candidate_root
        )
        checks = _check_rows(kernel)
        invocations = [
            dict(event.data)
            for event in kernel.events
            if event.kind is EventKind.INVOCATION_COMPLETED
            and int(event.data["call_index"]) >= 19
        ]
        actions = [
            dict(event.data)
            for event in kernel.events
            if event.kind is EventKind.ACTION_DISPOSITION
            and int(event.data["call_index"]) >= 19
        ]
        first_binding = dict(invocations[0].get("request_binding", {}))
        exposed_slots = {
            str(row["state_slot_id"])
            for invocation in invocations
            for row in invocation.get("request_binding", {}).get(
                "state_slot_exposures", []
            )
        }
        marginal_tokens = (
            counters.serialized_tokens
            - migration.counters.serialized_tokens
        )
        marginal_provider = (
            counters.provider_attempts
            - migration.counters.provider_attempts
        )
        total_actor_attempts = sum(row.actor_attempts for row in tranches)
        total_maintenance_attempts = sum(row.maintenance_attempts for row in tranches)

        if initial_evaluation["candidate_sha256"] != DONOR_CANDIDATE_SHA256:
            failures.append("initial_candidate_hash_mismatch")
        if initial_evaluation["closure_readiness"] != "not_ready":
            failures.append("initial_readiness_not_frozen_negative")
        observed_blockers = {
            row["criterion_id"]
            for row in initial_evaluation["criterion_results"]
            if row["status"] == "fail"
        }
        if observed_blockers != set(readiness["blocking_criterion_ids"]):
            failures.append("frozen_blocking_criteria_mismatch")
        if EXPECTED_PENDING_EFFECT not in first_binding.get(
            "included_result_ids", []
        ):
            failures.append("pending_effect_not_in_first_completed_request")
        if "current_candidate" not in exposed_slots:
            failures.append("current_candidate_not_exposed")
        if "current_candidate_effect" not in exposed_slots:
            failures.append("current_effect_not_exposed")
        expected_actions = [
            "upsert_decision_section",
            "begin_verification",
            "run_check",
            *(["replace_artifact_section"] * 6),
            "run_check",
            "submit",
        ]
        observed_actions = [row.get("action", {}).get("action") for row in actions]
        if observed_actions != expected_actions:
            failures.append("provider_free_action_lifecycle_mismatch")
        if len(checks) != 2 or checks[0]["passed"] is not False or checks[1]["passed"] is not True:
            failures.append("provider_free_check_repair_recheck_failed")
        if final_evaluation["passed"] is not True:
            failures.append("provider_free_final_candidate_failed")
        if migration.adapter.world.submitted is not True:
            failures.append("provider_free_submission_missing")
        if tranches[-1].disposition is not TerminalCode.COMPLETED:
            failures.append("provider_free_terminal_not_completed")
        if total_actor_attempts > MAXIMUM_ADDITIONAL_ACTOR_CALLS:
            failures.append("actor_budget_exceeded")
        if total_maintenance_attempts > MAXIMUM_ADDITIONAL_MAINTENANCE_CALLS:
            failures.append("maintenance_budget_exceeded")
        if marginal_provider > MAXIMUM_ADDITIONAL_PROVIDER_CALLS:
            failures.append("provider_budget_exceeded")
        if marginal_tokens > MAXIMUM_ADDITIONAL_SERIALIZED_TOKENS:
            failures.append("serialized_token_budget_exceeded")
        if any(
            event.kind in {EventKind.REOPEN_REQUESTED, EventKind.REPEAT_DEMAND}
            for event in kernel.events
            if event.ordinal > 144
        ):
            failures.append("provider_free_unplanned_reopen_or_repeat")

        result = {
            "action_sequence": observed_actions,
            "additional_actor_calls": total_actor_attempts,
            "additional_maintenance_calls": total_maintenance_attempts,
            "additional_provider_calls": marginal_provider,
            "additional_serialized_tokens": marginal_tokens,
            "candidate_changed": (
                final_evaluation["candidate_sha256"] != DONOR_CANDIDATE_SHA256
            ),
            "check_sequence": [
                {
                    "candidate_sha256": row["evaluated_candidate_sha256"],
                    "passed": row["passed"],
                    "blocking_requirement_count": len(row["blocking_criterion_ids"]),
                }
                for row in checks
            ],
            "contract_sha256": sha256_file(CONTRACT),
            "disposition": tranches[-1].disposition.value,
            "donor_evaluation": initial_evaluation,
            "execution_manifest": lifecycle_scout_execution_manifest(ROOT),
            "failures": failures,
            "final_evaluation": final_evaluation,
            "first_new_request_binding": first_binding,
            "frozen_readiness_sha256": sha256_file(READINESS),
            "migration_receipt": dict(migration.receipt),
            "passed": not failures,
            "request_sha256": sha256_file(REQUEST),
            "run_id": RUN_ID,
            "schema": "trellis-e97-verification-lifecycle-stage0-v0",
            "state_slots_exposed": sorted(exposed_slots),
            "tranche_dispositions": [row.disposition.value for row in tranches],
        }
    return result


def main() -> int:
    value = build()
    write_json(OUTPUT, value)
    if not value["passed"]:
        raise RuntimeError(f"Stage 0 failed: {value['failures']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
