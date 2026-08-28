"""Exact activation logic for the bounded causal-verification comparison.

The comparison is eligible only after the live trajectory itself produces the
state in which causal continuity can matter.  Source counts, domain counts,
accessible-world size, and context pressure are deliberately absent here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


DEFAULT_MUTATION_ACTIONS = frozenset(
    {
        "patch_decision",
        "replace_artifact_section",
        "replace_decision",
        "replace_evidence_ledger",
        "upsert_decision_section",
    }
)
DEFAULT_OBSERVATION_KINDS = frozenset(
    {
        "exact_reopen_observation",
        "source_observation",
    }
)


@dataclass(frozen=True)
class CausalForkActivation:
    qualified: bool
    candidate_sha256: str | None
    verification_transition_call: int | None
    current_check_call: int | None
    rejected_repair_call: int | None
    subsequent_observation_call: int | None
    treatment_decision_call: int | None
    failures: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "keystone-event-triggered-causal-activation-v0",
            "qualified": self.qualified,
            "candidate_sha256": self.candidate_sha256,
            "verification_transition_call": self.verification_transition_call,
            "current_check_call": self.current_check_call,
            "rejected_repair_call": self.rejected_repair_call,
            "subsequent_observation_call": self.subsequent_observation_call,
            "treatment_decision_call": self.treatment_decision_call,
            "failures": list(self.failures),
        }


def _call(row: dict[str, Any], fallback: int) -> int:
    value = row.get("actor_call")
    if value is None:
        value = row.get("logical_call")
    return int(value if value is not None else fallback)


def _action(row: dict[str, Any]) -> str | None:
    action = row.get("parsed_action")
    if not isinstance(action, dict):
        return None
    value = action.get("action")
    return value if isinstance(value, str) else None


def _candidate_before(row: dict[str, Any]) -> str | None:
    value = row.get("candidate_sha256_before")
    return value if isinstance(value, str) and value else None


def _candidate_after(row: dict[str, Any]) -> str | None:
    value = row.get("candidate_sha256_after")
    return value if isinstance(value, str) and value else None


def _candidate_is_unchanged(row: dict[str, Any], candidate: str) -> bool:
    return _candidate_before(row) == candidate and _candidate_after(row) == candidate


def _current_check_candidate(row: dict[str, Any]) -> str | None:
    binding = row.get("current_check_binding")
    if not isinstance(binding, dict):
        return None
    evaluated = binding.get("evaluated_candidate_sha256")
    return evaluated if isinstance(evaluated, str) and evaluated else None


def _all_unchanged(rows: Iterable[dict[str, Any]], candidate: str) -> bool:
    return all(_candidate_is_unchanged(row, candidate) for row in rows)


def detect_causal_fork_activation(
    trace: list[dict[str, Any]],
    *,
    initial_candidate_sha256: str,
    mutation_actions: frozenset[str] = DEFAULT_MUTATION_ACTIONS,
    observation_kinds: frozenset[str] = DEFAULT_OBSERVATION_KINDS,
) -> CausalForkActivation:
    """Find the first exact treatment-dependent decision boundary.

    The required live sequence is:

    nontrivial candidate -> admitted verification transition -> current check
    -> rejected mutation with no candidate change -> later exact observation
    acquired with the candidate still unchanged -> fork before the next actor
    decision, whose prompt delivers that pending observation.

    The function does not judge evidence quality, choose a repair, or infer
    readiness.  It only recognizes exact recorded lifecycle events.
    """

    if not trace:
        return CausalForkActivation(
            False, None, None, None, None, None, None, ("empty_trace",)
        )

    calls = [_call(row, index + 1) for index, row in enumerate(trace)]
    if any(right <= left for left, right in zip(calls, calls[1:], strict=False)):
        return CausalForkActivation(
            False,
            None,
            None,
            None,
            None,
            None,
            None,
            ("actor_calls_not_strictly_increasing",),
        )

    phase_seen = False
    current_check_seen = False
    rejected_repair_seen = False

    for phase_index, phase_row in enumerate(trace):
        if (
            _action(phase_row) != "begin_verification"
            or phase_row.get("rejection_code") is not None
            or phase_row.get("result_kind") != "phase_effect"
        ):
            continue
        phase_seen = True
        phase_candidate = _candidate_after(phase_row)
        if not phase_candidate or phase_candidate == initial_candidate_sha256:
            continue

        for check_index in range(phase_index + 1, len(trace)):
            check_row = trace[check_index]
            candidate = _current_check_candidate(check_row)
            if (
                check_row.get("result_kind") != "check_observation"
                or not candidate
                or candidate == initial_candidate_sha256
                or not _candidate_is_unchanged(check_row, candidate)
            ):
                continue
            current_check_seen = True

            for rejection_index in range(check_index + 1, len(trace)):
                rejection_row = trace[rejection_index]
                if (
                    _action(rejection_row) not in mutation_actions
                    or not rejection_row.get("rejection_code")
                    or not _candidate_is_unchanged(rejection_row, candidate)
                    or not _all_unchanged(
                        trace[check_index + 1 : rejection_index], candidate
                    )
                ):
                    continue
                rejected_repair_seen = True

                for observation_index in range(rejection_index + 1, len(trace)):
                    observation_row = trace[observation_index]
                    if (
                        observation_row.get("result_kind") not in observation_kinds
                        or not _candidate_is_unchanged(observation_row, candidate)
                        or not _all_unchanged(
                            trace[rejection_index + 1 : observation_index], candidate
                        )
                    ):
                        continue
                    observation_call = _call(observation_row, observation_index + 1)
                    return CausalForkActivation(
                        True,
                        candidate,
                        _call(phase_row, phase_index + 1),
                        _call(check_row, check_index + 1),
                        _call(rejection_row, rejection_index + 1),
                        observation_call,
                        observation_call + 1,
                        (),
                    )

    failures: list[str] = []
    if not phase_seen:
        failures.append("verification_transition_not_observed")
    if not current_check_seen:
        failures.append("current_candidate_bound_check_not_observed")
    if not rejected_repair_seen:
        failures.append("unchanged_candidate_rejected_repair_not_observed")
    failures.append("post_rejection_observation_not_observed")
    return CausalForkActivation(
        False, None, None, None, None, None, None, tuple(failures)
    )


def activation_tax(
    activation: CausalForkActivation,
    *,
    parent_calls: int,
    parent_serialized_tokens: int,
    continuation_trace: list[dict[str, Any]],
) -> dict[str, Any]:
    """Report cost before the first treatment-dependent actor decision."""

    cutoff = activation.subsequent_observation_call
    counted = [
        row
        for index, row in enumerate(continuation_trace)
        if cutoff is None or _call(row, index + 1) <= cutoff
    ]
    continuation_tokens = 0
    for row in counted:
        usage = row.get("usage")
        if isinstance(usage, dict):
            total = usage.get("total_tokens")
            if isinstance(total, int) and total >= 0:
                continuation_tokens += total
    return {
        "schema": "activation-tax-v0",
        "treatment_activated": activation.qualified,
        "parent_calls": parent_calls,
        "continuation_calls": len(counted),
        "calls_before_first_treatment_decision": parent_calls + len(counted),
        "parent_serialized_tokens": parent_serialized_tokens,
        "continuation_serialized_tokens": continuation_tokens,
        "serialized_tokens_before_first_treatment_decision": (
            parent_serialized_tokens + continuation_tokens
        ),
    }
