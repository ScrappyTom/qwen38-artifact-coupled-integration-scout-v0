from __future__ import annotations

import json
from pathlib import Path

from tools import audit_solace_anchored_interaction as audit


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = (
    ROOT
    / "runs"
    / "2026-08-26-solace-anchored-provenance-interaction-measured-v0"
)


def test_frozen_solace_interaction_mechanical_audit_passes() -> None:
    result = audit.audit(RUN_ROOT)
    assert result["passed"] is True
    assert result["failures"] == []
    assert result["provider_calls"] == 34
    assert result["actor_calls"] == 27
    assert result["maintenance_calls"] == 7
    assert result["serialized_tokens"] == 578_257
    assert result["runtime_released"] is True


def test_frozen_solace_interaction_cell_contrast() -> None:
    result = audit.audit(RUN_ROOT)
    cells = {row["configuration_id"]: row for row in result["cells"]}
    assert cells["W0_DIRECT_EXACT_WORK_FRESH"]["action_counts"] == {
        "read_batch": 1,
        "rejected": 2,
        "reopen_exact": 14,
        "replace_evidence_ledger": 1,
    }
    assert cells["L1_FAULT_TOLERANT_ANCHORED_PROVENANCE"]["action_counts"] == {
        "read_batch": 1,
        "replace_decision": 1,
        "replace_evidence_ledger": 1,
        "upsert_decision_section": 6,
    }
    assert cells["L1_FAULT_TOLERANT_ANCHORED_PROVENANCE"]["register_claims"] == 20
    assert all(row["closure_readiness"] == "not_ready" for row in cells.values())


def test_semantic_adjudication_is_candidate_bound() -> None:
    adjudication = json.loads(
        (ROOT / "SOLACE_ANCHORED_INTERACTION_SEMANTIC_ADJUDICATION.json").read_text(
            encoding="utf-8"
        )
    )
    run = json.loads((RUN_ROOT / "RUN_RESULT.json").read_text(encoding="utf-8"))
    run_candidates = {
        row["configuration_id"]: row["candidate_sha256"] for row in run["cells"]
    }
    for record in adjudication["records"]:
        assert record["candidate_sha256"] == run_candidates[record["configuration_id"]]
    assert adjudication["records"][0]["quality_class"] == "incomplete"
    assert adjudication["records"][1]["quality_class"] == "strong_partial"
    assert adjudication["records"][1]["closure_readiness"] == "not_ready"
