from __future__ import annotations

from pathlib import Path

from tools.audit_keystone_event_fork import audit


ROOT = Path(__file__).resolve().parents[1]


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


def test_qualitative_appendix_preserves_corrected_system_interpretation() -> None:
    text = (ROOT / "KEYSTONE_EVENT_FORK_QUALITATIVE_TRANSCRIPT_APPENDIX.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(text.split())
    required = (
        "27 model calls and 300,754",
        "Eight claims entered the register and forty",
        "represented only three of the",
        "retained no admitted relationship claim",
        "Ten maintenance invocations left eight actor decisions",
        "all fourteen source bodies had crossed an actor boundary",
        "The absence of a fork is therefore scientifically meaningful nonactivation",
        "that the same world should be continued or retried",
    )
    for phrase in required:
        assert phrase in normalized
