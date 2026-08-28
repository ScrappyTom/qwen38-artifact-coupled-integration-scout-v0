from __future__ import annotations

from reactive_runtime.causal_activation import (
    activation_tax,
    detect_causal_fork_activation,
)


C0 = "0" * 64
C1 = "1" * 64
C2 = "2" * 64


def event(
    call: int,
    action: str,
    *,
    before: str = C1,
    after: str = C1,
    result_kind: str | None = None,
    rejection: str | None = None,
    check_candidate: str | None = None,
    total_tokens: int = 100,
) -> dict:
    return {
        "actor_call": call,
        "parsed_action": {"action": action},
        "candidate_sha256_before": before,
        "candidate_sha256_after": after,
        "result_kind": result_kind,
        "rejection_code": rejection,
        "current_check_binding": (
            None
            if check_candidate is None
            else {"evaluated_candidate_sha256": check_candidate}
        ),
        "usage": {"total_tokens": total_tokens},
    }


def qualifying_trace() -> list[dict]:
    return [
        event(
            10,
            "upsert_decision_section",
            before=C0,
            after=C1,
            result_kind="candidate_effect",
        ),
        event(11, "begin_verification", result_kind="phase_effect"),
        event(12, "run_check", result_kind="check_observation", check_candidate=C1),
        event(13, "replace_artifact_section", rejection="section_version_mismatch"),
        event(14, "read_source", result_kind="source_observation"),
    ]


def test_exact_lifecycle_event_qualifies_without_source_or_pressure_counts() -> None:
    activation = detect_causal_fork_activation(
        qualifying_trace(), initial_candidate_sha256=C0
    )
    assert activation.qualified is True
    assert activation.candidate_sha256 == C1
    assert activation.verification_transition_call == 11
    assert activation.current_check_call == 12
    assert activation.rejected_repair_call == 13
    assert activation.subsequent_observation_call == 14
    assert activation.treatment_decision_call == 15
    assert activation.failures == ()


def test_source_acquisition_and_pressure_alone_never_qualify() -> None:
    trace = [
        event(
            call, "read_source", before=C0, after=C0, result_kind="source_observation"
        )
        for call in range(1, 15)
    ]
    activation = detect_causal_fork_activation(trace, initial_candidate_sha256=C0)
    assert activation.qualified is False
    assert "verification_transition_not_observed" in activation.failures


def test_rejection_without_a_later_observation_does_not_qualify() -> None:
    trace = qualifying_trace()[:-1]
    activation = detect_causal_fork_activation(trace, initial_candidate_sha256=C0)
    assert activation.qualified is False
    assert activation.failures == ("post_rejection_observation_not_observed",)


def test_candidate_change_after_rejection_invalidates_that_epoch() -> None:
    trace = qualifying_trace()[:-1]
    trace.append(
        event(
            14,
            "replace_artifact_section",
            before=C1,
            after=C2,
            result_kind="candidate_effect",
        )
    )
    trace.append(
        event(15, "read_source", before=C2, after=C2, result_kind="source_observation")
    )
    activation = detect_causal_fork_activation(trace, initial_candidate_sha256=C0)
    assert activation.qualified is False
    assert "post_rejection_observation_not_observed" in activation.failures


def test_stale_check_cannot_activate_the_fork() -> None:
    trace = qualifying_trace()
    trace[2]["current_check_binding"] = {"evaluated_candidate_sha256": C0}
    activation = detect_causal_fork_activation(trace, initial_candidate_sha256=C0)
    assert activation.qualified is False
    assert "current_candidate_bound_check_not_observed" in activation.failures


def test_activation_tax_counts_only_the_common_prefix_before_the_fork() -> None:
    trace = qualifying_trace()
    trace.append(event(15, "replace_artifact_section", total_tokens=900))
    activation = detect_causal_fork_activation(trace, initial_candidate_sha256=C0)
    tax = activation_tax(
        activation,
        parent_calls=9,
        parent_serialized_tokens=102_009,
        continuation_trace=trace,
    )
    assert tax["treatment_activated"] is True
    assert tax["continuation_calls"] == 5
    assert tax["calls_before_first_treatment_decision"] == 14
    assert tax["continuation_serialized_tokens"] == 500
    assert tax["serialized_tokens_before_first_treatment_decision"] == 102_509


def test_admitted_candidate_change_before_current_check_starts_a_new_epoch() -> None:
    trace = qualifying_trace()
    trace.insert(
        2,
        event(
            12,
            "replace_artifact_section",
            before=C1,
            after=C2,
            result_kind="candidate_effect",
        ),
    )
    for call, row in enumerate(trace[3:], start=13):
        row["actor_call"] = call
        row["candidate_sha256_before"] = C2
        row["candidate_sha256_after"] = C2
        if row.get("current_check_binding"):
            row["current_check_binding"]["evaluated_candidate_sha256"] = C2
    activation = detect_causal_fork_activation(trace, initial_candidate_sha256=C0)
    assert activation.qualified is True
    assert activation.candidate_sha256 == C2
