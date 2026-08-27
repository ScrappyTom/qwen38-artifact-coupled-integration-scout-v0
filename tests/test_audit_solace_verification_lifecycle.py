from __future__ import annotations

import json
from pathlib import Path

from tools import audit_solace_verification_lifecycle as audit


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "2026-08-27-solace-verification-lifecycle-measured-v0"


def test_frozen_verification_lifecycle_audit_passes() -> None:
    assert audit.main() == 0
    result = json.loads(
        (ROOT / "SOLACE_VERIFICATION_LIFECYCLE_AUDIT.json").read_text(encoding="utf-8")
    )
    assert result["passed"] is True
    assert result["failures"] == []
    assert result["provider_calls"] == 14
    assert result["serialized_tokens"] == 243_637


def test_frozen_verification_lifecycle_contrast() -> None:
    result = json.loads(
        (ROOT / "SOLACE_VERIFICATION_LIFECYCLE_AUDIT.json").read_text(encoding="utf-8")
    )
    cells = {row["configuration_id"]: row for row in result["cells"]}
    a0 = cells["A0_EXACT_ARTIFACT_ONLY"]
    a1 = cells["A1_EXACT_ARTIFACT_PLUS_FROZEN_REGISTER"]
    assert a0["actions"] == [
        "run_check",
        "read_batch",
        "read_batch",
        "patch_decision",
        "run_check",
        "patch_decision",
        "run_check",
        "patch_decision",
        "run_check",
        "patch_decision",
    ]
    assert a1["actions"] == [
        "run_check",
        "read_batch",
        "read_batch",
        "patch_decision",
    ]
    assert a0["offline_final_evaluation"]["blocking_requirements"] == [
        "decision_heading_order: exact ordered level-two headings"
    ]
    assert a1["offline_final_evaluation"]["blocking_requirements"] == [
        "decision_heading_order: exact ordered level-two headings"
    ]
    assert a0["final_effect_crossed_later_model_boundary"] is False
    assert a1["final_effect_crossed_later_model_boundary"] is False
    assert result["comparison"]["A1_over_A0_initial_prompt_tokens"] == 6_646


def test_semantic_adjudication_is_candidate_bound_and_not_ready() -> None:
    adjudication = json.loads(
        (ROOT / "SOLACE_VERIFICATION_LIFECYCLE_SEMANTIC_ADJUDICATION.json").read_text(
            encoding="utf-8"
        )
    )
    run = json.loads((RUN_ROOT / "RUN_RESULT.json").read_text(encoding="utf-8"))
    run_candidates = {
        row["configuration_id"]: row["candidate_sha256"] for row in run["cells"]
    }
    records = {row["configuration_id"]: row for row in adjudication["records"]}
    for configuration_id, record in records.items():
        assert record["candidate_sha256"] == run_candidates[configuration_id]
        assert record["quality_class"] == "strong_partial"
        assert record["closure_readiness"] == "not_ready"
        assert record["useful_completion"] is False
    assert records["A0_EXACT_ARTIFACT_ONLY"]["requirement_summary"] == {
        "met": 11,
        "partial": 1,
        "not_met": 0,
    }
    assert records["A1_EXACT_ARTIFACT_PLUS_FROZEN_REGISTER"]["requirement_summary"] == {
        "met": 10,
        "partial": 2,
        "not_met": 0,
    }


def test_result_and_appendix_preserve_key_claim_limits() -> None:
    result = (ROOT / "SOLACE_VERIFICATION_LIFECYCLE_RESULT.md").read_text(
        encoding="utf-8"
    )
    appendix = (
        ROOT / "SOLACE_VERIFICATION_LIFECYCLE_QUALITATIVE_TRANSCRIPT_APPENDIX.md"
    ).read_text(encoding="utf-8")
    assert "Both final artifacts are therefore `strong_partial`, `not_ready`" in result
    assert "does not earn verification-phase residency" not in result
    assert "This is local evidence for demoting construction scaffolding" in result
    assert "The register remained behaviorally useful" not in result
    assert "Important visible state" in appendix
    assert "forty-eight samples per round" in appendix
    assert "6.5 MW" in appendix

