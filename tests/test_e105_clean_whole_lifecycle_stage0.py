from __future__ import annotations

import json
import tempfile
from pathlib import Path

from host_refactor.whole_lifecycle.provider_free import (
    run_provider_free_complete_lifecycle,
)
from host_refactor.whole_lifecycle.system import (
    CONFIGURATION_LABEL,
    RUN_ID,
    execution_manifest,
)
from tools import build_e105_clean_whole_lifecycle_stage0 as stage0
from tools import run_e105_clean_whole_lifecycle_tranche as runner
from reactive_runtime.canonical import write_json


ROOT = Path(__file__).resolve().parents[1]


def test_clean_lifecycle_provider_free_reaches_current_recheck_and_closure() -> None:
    with tempfile.TemporaryDirectory() as temp:
        result = run_provider_free_complete_lifecycle(
            ROOT,
            output_root=Path(temp) / "lifecycle",
        )
    assert result["terminal"] == "completed"
    assert result["submitted"] is True
    assert [row["passed"] for row in result["check_sequence"]] == [False, True]
    assert result["external_check_result_ids"]
    assert result["candidate_effect_receipt_ids"]
    assert result["decision_heading_count"] == 6
    assert result["glued_heading_present"] is False
    assert result["relief_events"] >= 1
    assert result["scaffold_ever_exposed"] is True
    assert result["scaffold_active_at_end"] is False
    assert result["final_evaluation"]["passed"] is True
    assert result["readiness_adjudication"]["closure_readiness"] == "ready"


def test_e105_stage0_is_clean_frozen_and_not_live_authorized() -> None:
    value = stage0.build()
    assert value["passed"] is True
    assert value["run_id"] == RUN_ID
    assert value["configuration"] == CONFIGURATION_LABEL
    assert value["gpu_model_calls"] == 0
    assert value["live_authorized"] is False
    assert value["automatic_continuation"] is False
    assert value["complete_provider_free_lifecycle"]["terminal"] == "completed"
    assert value["initial_readiness_adjudication"]["closure_readiness"] == "not_ready"


def test_e105_execution_manifest_binds_new_lifecycle_and_runner() -> None:
    manifest = execution_manifest(ROOT)
    files = manifest["files"]
    assert "host_refactor/effect_lifecycle/verification.py" in files
    assert "host_refactor/whole_lifecycle/system.py" in files
    assert "host_refactor/whole_lifecycle/provider_free.py" in files
    assert "host_refactor/whole_lifecycle/readiness.py" in files
    assert "tools/run_e105_clean_whole_lifecycle_tranche.py" in files


def test_published_e105_stage0_matches_contract() -> None:
    value = json.loads(
        (ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_STAGE0.json").read_text(
            encoding="utf-8"
        )
    )
    contract = json.loads(
        (ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert value["passed"] is True
    assert value["run_id"] == contract["run_id"]
    assert contract["initial_state"]["e103_resumed"] is False
    assert value["first_live_tranche_limits"]["maximum_actor_calls"] == 12
    assert value["first_live_tranche_limits"]["maximum_maintenance_calls"] == 6


def test_e105_authorization_is_external_exact_and_commit_bound() -> None:
    request = json.loads(
        (ROOT / "TRELLIS_CLEAN_WHOLE_LIFECYCLE_AUTHORIZATION_REQUEST.json").read_text(
            encoding="utf-8"
        )
    )
    commit = runner.git_commit()
    receipt = {
        "authorized": True,
        "authorized_freeze_commit": commit,
        "authorized_scopes": [runner.SCOPE],
        "authorized_run_id": runner.RUN_ID,
        "configuration": runner.CONFIGURATION_LABEL,
        "maximum_actor_calls": runner.INITIAL_MAXIMUM_ACTOR_CALLS,
        "maximum_maintenance_calls": runner.INITIAL_MAXIMUM_MAINTENANCE_CALLS,
        "maximum_provider_calls": runner.INITIAL_MAXIMUM_PROVIDER_CALLS,
        "maximum_serialized_tokens": runner.INITIAL_MAXIMUM_SERIALIZED_TOKENS,
        "attempts_per_call": 1,
        "retries": 0,
        "authorization_text": request["expected_user_quote_template"].replace(
            "{commit}", commit
        ),
    }
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "AUTHORIZATION.json"
        write_json(path, receipt)
        assert runner.authorize(path) == receipt
