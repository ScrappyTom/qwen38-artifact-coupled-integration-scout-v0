from __future__ import annotations

# ruff: noqa: E402

import argparse
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from host_refactor.whole_lifecycle.readiness import adjudicate_readiness
from host_refactor.whole_lifecycle.resume import hydrate_checkpoint
from interaction_scout.fixtures import GroundedMaintenanceFixture, ScriptedActorProvider
from interaction_scout.live_path import run_interaction_tranche
from reactive_runtime.canonical import sha256_file, write_json
from reactive_runtime.seal import verify_tree_seal
from reactive_runtime.task_decision_evaluator import evaluate
from tools.offline_tokenizer import OfflineTokenizer


PARENT_RUN_ID = "2026-08-30-trellis-clean-whole-lifecycle-v0"
PARENT_RESULT_COMMIT = "fa67aecdf833b72f282a03819a3fbc35e263c320"
PARENT_ROOT = ROOT / "qualification_runs" / PARENT_RUN_ID
PARENT_CHECKPOINT = PARENT_ROOT / "tranche-001" / "CHECKPOINT.json"


def build() -> dict:
    seal_errors = verify_tree_seal(PARENT_ROOT, PARENT_ROOT / "RUN_SEAL.json")
    tokenizer = OfflineTokenizer()
    with tempfile.TemporaryDirectory(prefix="trellis-e107-stage0-") as temp:
        output = Path(temp)
        maintenance = GroundedMaintenanceFixture(
            ROOT / "task_trellis",
            tokenizer.count_messages,
            tokenizer.count_text,
        )
        orchestrator, adapter, kernel, counters = hydrate_checkpoint(
            repository_root=ROOT,
            checkpoint_path=PARENT_CHECKPOINT,
            trajectory_root=output / "trajectory",
            count_messages=tokenizer.count_messages,
            count_text=tokenizer.count_text,
            maintenance_complete=maintenance,
        )
        starting_calls = len(kernel.project().completed_calls)
        starting_maintenance = orchestrator.lifecycle.maintenance_calls
        starting_provider = counters.provider_attempts
        starting_tokens = counters.serialized_tokens
        starting_candidate = adapter.world.candidate_sha256
        starting_pending = list(kernel.project().pending_result_ids)
        maintenance.calls = starting_maintenance
        actor = ScriptedActorProvider(
            adapter,
            tokenizer.count_messages,
            tokenizer.count_text,
        )
        actor.calls = starting_calls
        tranche = run_interaction_tranche(
            orchestrator=orchestrator,
            kernel=kernel,
            counters=counters,
            actor_complete=actor,
            run_root=output / "tranche-002",
            parent_checkpoint_path=PARENT_CHECKPOINT,
        )
        final = evaluate(ROOT / "task_trellis", adapter.world.candidate_root)
        readiness = adjudicate_readiness(
            ROOT,
            final,
            current_candidate_sha256=adapter.world.candidate_sha256,
        )
        additional_provider = tranche.counters.provider_attempts - starting_provider
        additional_tokens = tranche.counters.serialized_tokens - starting_tokens
        passed = (
            not seal_errors
            and starting_calls == 12
            and starting_maintenance == 6
            and tranche.disposition.value == "completed"
            and tranche.actor_attempts <= 12
            and tranche.maintenance_attempts <= 6
            and additional_provider <= 18
            and additional_tokens <= 400_000
            and readiness["closure_readiness"] == "ready"
            and adapter.world.submitted
        )
        return {
            "schema": "trellis-clean-whole-lifecycle-continuation-stage0-v0",
            "passed": passed,
            "live_authorized": False,
            "provider_calls": 0,
            "configuration": "V1_CLEAN_PROSPECTIVE_LIFECYCLE",
            "parent_run_id": PARENT_RUN_ID,
            "parent_result_commit": PARENT_RESULT_COMMIT,
            "parent_bindings": {
                "checkpoint_sha256": sha256_file(PARENT_CHECKPOINT),
                "run_seal_sha256": sha256_file(PARENT_ROOT / "RUN_SEAL.json"),
                "tranche_result_sha256": sha256_file(PARENT_ROOT / "TRANCHE_RESULT.json"),
                "seal_errors": list(seal_errors),
            },
            "hydrated_state": {
                "completed_actor_calls": starting_calls,
                "maintenance_calls": starting_maintenance,
                "provider_calls": starting_provider,
                "serialized_tokens": starting_tokens,
                "pending_result_ids": starting_pending,
                "candidate_sha256": starting_candidate,
            },
            "provider_free_continuation": {
                "disposition": tranche.disposition.value,
                "additional_actor_calls": tranche.actor_attempts,
                "additional_maintenance_calls": tranche.maintenance_attempts,
                "additional_provider_calls": additional_provider,
                "additional_serialized_tokens": additional_tokens,
                "final_candidate_sha256": adapter.world.candidate_sha256,
                "closure_readiness": readiness["closure_readiness"],
                "submitted": adapter.world.submitted,
            },
            "additional_limits": {
                "actor_calls": 12,
                "maintenance_calls": 6,
                "provider_calls": 18,
                "serialized_tokens": 400_000,
                "attempts_per_call": 1,
                "retries": 0,
            },
            "policy_change": False,
            "automatic_continuation": False,
            "next_live_operation": (
                "separately_authorized_exact_checkpoint_continuation_only"
            ),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    write_json(args.output, build())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
