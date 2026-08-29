from __future__ import annotations

from pathlib import Path

import pytest

from reactive_runtime.seal import verify_tree_seal

from interaction_scout.continuation import hydrate_continuation
from interaction_scout.fixtures import GroundedMaintenanceFixture, ScriptedActorProvider
from interaction_scout.lifecycle import TREATMENT_CONFIGURATION
from interaction_scout.live_path import run_interaction_tranche
from interaction_scout.system import CONFIGURATION_ORDER
from tools.offline_tokenizer import OfflineTokenizer
from tools.run_refactored_interaction_continuation import (
    MAXIMUM_ACTOR_CALLS,
    MAXIMUM_MAINTENANCE_CALLS,
    MAXIMUM_PROVIDER_CALLS,
    MAXIMUM_SERIALIZED_TOKENS,
    PARENT_ROOT,
    RUN_ID,
    continuation_execution_manifest,
)


ROOT = Path(__file__).resolve().parents[1]


def test_continuation_freeze_and_parent_seal() -> None:
    assert not verify_tree_seal(PARENT_ROOT, PARENT_ROOT / "RUN_SEAL.json")
    assert MAXIMUM_ACTOR_CALLS == 24
    assert MAXIMUM_MAINTENANCE_CALLS == 6
    assert MAXIMUM_PROVIDER_CALLS == 30
    assert MAXIMUM_SERIALIZED_TOKENS == 520_028
    manifest = continuation_execution_manifest()
    assert manifest["parent_result_commit"] == (
        "0626259773f1411272566caa1b4a00c83e70e606"
    )
    assert manifest["execution_manifest_sha256"]


@pytest.mark.parametrize("configuration_id", CONFIGURATION_ORDER)
def test_exact_checkpoint_resume_reaches_common_scripted_closure(
    tmp_path: Path,
    configuration_id: str,
) -> None:
    tokenizer = OfflineTokenizer()
    maintenance = GroundedMaintenanceFixture(
        ROOT / "task_trellis", tokenizer.count_messages, tokenizer.count_text
    )
    maintenance.calls = 6
    checkpoint = (
        PARENT_ROOT
        / "cells"
        / configuration_id
        / "tranche-001"
        / "CHECKPOINT.json"
    )
    orchestrator, adapter, kernel, counters = hydrate_continuation(
        repository_root=ROOT,
        checkpoint_path=checkpoint,
        trajectory_root=tmp_path / configuration_id,
        configuration_id=configuration_id,
        count_messages=tokenizer.count_messages,
        count_text=tokenizer.count_text,
        maintenance_complete=(
            maintenance if configuration_id == TREATMENT_CONFIGURATION else None
        ),
    )
    state = kernel.project()
    assert len(state.completed_calls) == 12
    assert state.results["RESULT-012"].delivery_state.value == "pending"
    actor = ScriptedActorProvider(adapter, tokenizer.count_messages, tokenizer.count_text)
    actor.calls = 12
    result = run_interaction_tranche(
        orchestrator=orchestrator,
        kernel=kernel,
        counters=counters,
        actor_complete=actor,
        run_root=tmp_path / f"run-{configuration_id}",
        parent_checkpoint_path=checkpoint,
    )
    assert result.disposition.value == "completed"
    assert result.actor_attempts == 7
    assert adapter.world.submitted is True
    assert adapter.world.last_check_projection is not None
    assert adapter.world.last_check_projection["passed"] is True
    if configuration_id == TREATMENT_CONFIGURATION:
        assert result.maintenance_attempts <= 6
    else:
        assert result.maintenance_attempts == 0
    assert RUN_ID.endswith("continuation-v0")
