from __future__ import annotations

import json
from pathlib import Path

from tools.build_e107_clean_whole_lifecycle_continuation_stage0 import build
from tools.run_e107_clean_whole_lifecycle_continuation import (
    MAXIMUM_ACTOR_CALLS,
    MAXIMUM_MAINTENANCE_CALLS,
    MAXIMUM_PROVIDER_CALLS,
    MAXIMUM_SERIALIZED_TOKENS,
    PARENT_RESULT_COMMIT,
    RUN_ID,
)


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_frozen_stage0_recomputes_exactly() -> None:
    assert build() == load(
        ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CONTINUATION_STAGE0.json"
    )


def test_continuation_is_bound_to_parent_and_additional_limits() -> None:
    contract = load(ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CONTINUATION_CONTRACT.json")
    request = load(
        ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CONTINUATION_AUTHORIZATION_REQUEST.json"
    )
    stage0 = load(ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CONTINUATION_STAGE0.json")

    assert contract["parent_result_commit"] == PARENT_RESULT_COMMIT
    assert stage0["parent_result_commit"] == PARENT_RESULT_COMMIT
    assert contract["run_id"] == request["run_id"] == RUN_ID
    assert contract["policy_change"] is False
    assert stage0["live_authorized"] is False
    assert request["maximum_actor_calls"] == MAXIMUM_ACTOR_CALLS == 12
    assert request["maximum_maintenance_calls"] == MAXIMUM_MAINTENANCE_CALLS == 6
    assert request["maximum_provider_calls"] == MAXIMUM_PROVIDER_CALLS == 18
    assert request["maximum_serialized_tokens"] == MAXIMUM_SERIALIZED_TOKENS == 400000


def test_provider_free_continuation_reaches_ready_submission() -> None:
    stage0 = load(ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CONTINUATION_STAGE0.json")
    continuation = stage0["provider_free_continuation"]

    assert stage0["passed"] is True
    assert stage0["provider_calls"] == 0
    assert stage0["hydrated_state"]["pending_result_ids"] == ["RESULT-012"]
    assert continuation["disposition"] == "completed"
    assert continuation["closure_readiness"] == "ready"
    assert continuation["submitted"] is True
    assert continuation["additional_actor_calls"] <= MAXIMUM_ACTOR_CALLS
    assert continuation["additional_maintenance_calls"] <= MAXIMUM_MAINTENANCE_CALLS
    assert continuation["additional_provider_calls"] <= MAXIMUM_PROVIDER_CALLS
    assert continuation["additional_serialized_tokens"] <= MAXIMUM_SERIALIZED_TOKENS
