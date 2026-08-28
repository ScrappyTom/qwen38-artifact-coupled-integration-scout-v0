from __future__ import annotations

from tools.audit_keystone_event_fork import audit


def test_sealed_keystone_event_fork_closes_as_non_diagnostic() -> None:
    result = audit()
    assert result["passed"] is True
    assert result["scientific_disposition"] == {
        "run_valid": True,
        "causal_treatment_activated": False,
        "causal_treatment_evaluated": False,
        "keystone_disposition": "non_diagnostic_closed",
        "another_same_world_attempt_authorized": False,
        "promotion_authorized": False,
    }
    assert result["behavior"]["distinct_sources_observed"] == 14
    assert result["behavior"]["phase"] == "construction"
    assert (
        result["corrected_activation_tax"]["calls_before_first_treatment_decision"]
        == 27
    )
    assert (
        result["corrected_activation_tax"][
            "serialized_tokens_before_first_treatment_decision"
        ]
        == 300_754
    )
    assert result["embedded_summary_defect"]["custody_or_run_invalidated"] is False
