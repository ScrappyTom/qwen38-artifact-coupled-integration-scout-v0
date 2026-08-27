from __future__ import annotations

import json
from pathlib import Path

from tools import audit_orchard_phase_lifecycle as audit


ROOT = Path(__file__).resolve().parents[1]


def test_frozen_orchard_phase_lifecycle_audit_passes() -> None:
    assert audit.main() == 0
    result = json.loads(
        (ROOT / "ORCHARD_PHASE_LIFECYCLE_AUDIT.json").read_text(encoding="utf-8")
    )
    assert result["passed"] is True
    assert result["failures"] == []
    assert result["actor_calls"] == 38
    assert result["maintenance_calls"] == 16
    assert result["provider_calls"] == 54
    assert result["serialized_tokens"] == 736_332


def test_compound_lifecycle_contrast_is_exact() -> None:
    result = json.loads(
        (ROOT / "ORCHARD_PHASE_LIFECYCLE_AUDIT.json").read_text(encoding="utf-8")
    )
    cells = {row["configuration_id"]: row for row in result["cells"]}
    f0 = cells["F0_FIXED_SCAFFOLD_APPEND_ONLY_VERIFICATION"]
    p1 = cells["P1_PHASE_CONDITIONAL_CURRENT_VERIFICATION"]
    assert result["comparison"]["common_prefix_byte_identical_actions"] is True
    assert f0["terminal_disposition"] == "context_pressure_without_feasible_relief"
    assert p1["terminal_disposition"] == "verification_call_budget_exhausted"
    assert f0["check_calls"] == [13]
    assert p1["check_calls"] == [13, 19]
    assert p1["rejected_actions"] == [
        {"actor_call": 16, "code": "patch_anchor_not_unique"},
        {"actor_call": 20, "code": "patch_anchor_not_unique"},
    ]
    assert p1["actions"][-4:] == ["read_source"] * 4
    assert result["comparison"]["P1_terminal_identical_CURRENT_reads"] == 4
    assert result["comparison"]["P1_post_repair_check_blockers"] == 3


def test_semantic_adjudication_preserves_quality_and_readiness_limits() -> None:
    adjudication = json.loads(
        (ROOT / "ORCHARD_PHASE_LIFECYCLE_SEMANTIC_ADJUDICATION.json").read_text(
            encoding="utf-8"
        )
    )
    records = {row["configuration_id"]: row for row in adjudication["records"]}
    f0 = records["F0_FIXED_SCAFFOLD_APPEND_ONLY_VERIFICATION"]
    p1 = records["P1_PHASE_CONDITIONAL_CURRENT_VERIFICATION"]
    assert f0["quality_class"] == "partial"
    assert f0["substantive_requirement_summary"] == {
        "met": 5,
        "partial": 7,
        "not_met": 0,
    }
    assert p1["quality_class"] == "strong_partial"
    assert p1["substantive_requirement_summary"] == {
        "met": 12,
        "partial": 0,
        "not_met": 0,
    }
    assert p1["mechanical_evaluator_reconciliation"]["R05_utilities"] == (
        "direct_review_met_surface_order_false_negative"
    )
    assert all(row["closure_readiness"] == "not_ready" for row in records.values())
    assert all(row["useful_completion"] is False for row in records.values())


def test_result_and_qualitative_appendix_preserve_system_claim_limits() -> None:
    result = (ROOT / "ORCHARD_PHASE_LIFECYCLE_RESULT.md").read_text(encoding="utf-8")
    appendix = (
        ROOT / "ORCHARD_PHASE_LIFECYCLE_QUALITATIVE_TRANSCRIPT_APPENDIX.md"
    ).read_text(encoding="utf-8")
    assert "This is a compound configuration result" in result
    assert "not readiness or useful completion" in result
    assert "P1 achieves readiness or useful completion | no" in result
    assert "Important visible state" in appendix
    assert "P1 A19 — effect uptake and current recheck" in appendix
    assert "P1 A24 — fourth CURRENT read" in appendix
    assert "The present run establishes only" in appendix
