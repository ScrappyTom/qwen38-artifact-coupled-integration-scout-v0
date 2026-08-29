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
)
from host_refactor.lifecycle_scout_v1.migration import migrate_donor
from host_refactor.lifecycle_scout_v1.system import (
    MAXIMUM_ADDITIONAL_ACTOR_CALLS,
    MAXIMUM_ADDITIONAL_MAINTENANCE_CALLS,
    MAXIMUM_ADDITIONAL_PROVIDER_CALLS,
    MAXIMUM_ADDITIONAL_SERIALIZED_TOKENS,
    RUN_ID,
    execution_manifest,
)
from host_refactor.model import EventKind, TerminalCode
from interaction_scout.live_path import run_interaction_tranche
from reactive_runtime.canonical import load_json, sha256_file, write_json
from reactive_runtime.task_decision_evaluator import evaluate
from tools.offline_tokenizer import OfflineTokenizer


OUTPUT = ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_STAGE0.json"
CONTRACT = ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_SCOUT_CONTRACT.json"
REQUEST = ROOT / "TRELLIS_E99_VERIFICATION_LIFECYCLE_SCOUT_AUTHORIZATION_REQUEST.json"
READINESS = ROOT / "TRELLIS_E97_DONOR_READINESS_ADJUDICATION.json"
SEALED_E98 = (
    ROOT
    / "qualification_runs"
    / "2026-08-29-trellis-e97-verification-lifecycle-scout-v0"
    / "tranche-001"
)


def _check_rows(kernel: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for projected in kernel.project().results.values():
        if projected.result.result_kind != "check_observation":
            continue
        check = projected.result.metadata.get("check_projection")
        if isinstance(check, Mapping):
            rows.append(dict(check))
    return rows


class SealedE98Replay:
    def __init__(self, tokenizer: OfflineTokenizer) -> None:
        self.tokenizer = tokenizer
        self.call_index = 19

    def __call__(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        response_path = (
            SEALED_E98
            / f"call-{self.call_index:03d}"
            / "actor"
            / "RESPONSE.json"
        )
        row = load_json(response_path)
        self.call_index += 1
        messages = payload.get("messages")
        if not isinstance(messages, list):
            raise ValueError("sealed replay payload lacks messages")
        content = str(row["content"])
        prompt_tokens = self.tokenizer.count_messages(messages)
        completion_tokens = self.tokenizer.count_text(content)
        return {
            "content": content,
            "finish_reason": str(row["finish_reason"]),
            "usage": {
                "completion_tokens": completion_tokens,
                "prompt_tokens": prompt_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }


def _rejected_response_regression(
    tokenizer: OfflineTokenizer,
    temp_root: Path,
) -> dict[str, Any]:
    migration = migrate_donor(
        repository_root=ROOT,
        trajectory_root=temp_root / "rejection-trajectory",
        count_messages=tokenizer.count_messages,
        count_text=tokenizer.count_text,
        maintenance_complete=NoOpMaintenanceFixture(),
    )
    kernel = migration.kernel
    counters = migration.counters
    replay = SealedE98Replay(tokenizer)
    dispositions: list[str | None] = []
    for _ in range(4):
        step = migration.orchestrator.step(
            kernel=kernel,
            counters=counters,
            actor_complete=replay,
        )
        kernel = step.runner_step.kernel
        counters = step.runner_step.counters
        dispositions.append(
            None
            if step.runner_step.disposition is None
            else step.runner_step.disposition.value
        )
    packet = migration.host.composer.compose(kernel)
    prompt_tokens = tokenizer.count_messages(packet.message_list())
    state = kernel.project()
    return {
        "current_action_contract_visible": (
            "current_action_contract" in state.state_slots
        ),
        "dispositions": dispositions,
        "next_packet_feasible": (
            prompt_tokens <= migration.host.configuration.prompt_limit
        ),
        "next_prompt_tokens": prompt_tokens,
        "prompt_limit": migration.host.configuration.prompt_limit,
        "raw_rejected_bodies_model_resident": any(
            row.entry_kind == "ordinary"
            and row.entry_id in {
                "CALL-000021-ASSISTANT",
                "CALL-000022-ASSISTANT",
            }
            for row in state.transcript
        ),
        "rejected_response_receipts": sum(
            row.entry_kind == "rejected_assistant_response_receipt"
            for row in state.transcript
        ),
    }


def build() -> dict[str, Any]:
    tokenizer = OfflineTokenizer()
    readiness = load_json(READINESS)
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        migration = migrate_donor(
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
        exposed_slots = {
            str(row["state_slot_id"])
            for invocation in invocations
            for row in invocation.get("request_binding", {}).get(
                "state_slot_exposures", []
            )
        }
        marginal_tokens = counters.serialized_tokens - migration.counters.serialized_tokens
        marginal_provider = counters.provider_attempts - migration.counters.provider_attempts
        total_actor_attempts = sum(row.actor_attempts for row in tranches)
        total_maintenance_attempts = sum(row.maintenance_attempts for row in tranches)
        expected_actions = [
            "upsert_decision_section",
            "begin_verification",
            "run_check",
            *("replace_artifact_section" for _ in range(6)),
            "run_check",
            "submit",
        ]
        observed_actions = [row.get("action", {}).get("action") for row in actions]
        regression = _rejected_response_regression(tokenizer, temp_root)

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
        first_binding = dict(invocations[0].get("request_binding", {}))
        if EXPECTED_PENDING_EFFECT not in first_binding.get("included_result_ids", []):
            failures.append("pending_effect_not_in_first_completed_request")
        if observed_actions != expected_actions:
            failures.append("provider_free_action_lifecycle_mismatch")
        if "current_action_contract" not in exposed_slots:
            failures.append("verification_action_contract_not_exposed")
        if len(checks) != 2 or not (checks[0]["passed"] is False and checks[1]["passed"] is True):
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
        if regression["rejected_response_receipts"] != 2:
            failures.append("rejected_response_receipt_regression")
        if regression["raw_rejected_bodies_model_resident"] is not False:
            failures.append("raw_rejected_body_remained_resident")
        if regression["next_packet_feasible"] is not True:
            failures.append("repaired_e98_sequence_remained_infeasible")
        if regression["current_action_contract_visible"] is not True:
            failures.append("repaired_e98_sequence_lacked_phase_contract")

        result = {
            "action_sequence": observed_actions,
            "additional_actor_calls": total_actor_attempts,
            "additional_maintenance_calls": total_maintenance_attempts,
            "additional_provider_calls": marginal_provider,
            "additional_serialized_tokens": marginal_tokens,
            "candidate_changed": final_evaluation["candidate_sha256"] != DONOR_CANDIDATE_SHA256,
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
            "execution_manifest": execution_manifest(ROOT),
            "failures": failures,
            "final_evaluation": final_evaluation,
            "first_new_request_binding": first_binding,
            "frozen_readiness_sha256": sha256_file(READINESS),
            "migration_receipt": dict(migration.receipt),
            "passed": not failures,
            "rejected_response_regression": regression,
            "request_sha256": sha256_file(REQUEST),
            "run_id": RUN_ID,
            "schema": "trellis-e99-verification-lifecycle-stage0-v1",
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
