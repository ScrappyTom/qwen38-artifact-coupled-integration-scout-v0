from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Sequence

from reactive_runtime.records import ResultLedger


CountMessages = Callable[[list[dict[str, str]]], int]


@dataclass(frozen=True)
class ReliefCandidateAudit:
    result_id: str
    before_tokens: int
    prospective_tokens: int
    prospective_savings: int
    selected: bool
    reason: str


@dataclass(frozen=True)
class ReliefPass:
    prompt_tokens: int
    feasible: bool
    selected_result_ids: tuple[str, ...]
    audits: tuple[ReliefCandidateAudit, ...]


def positive_savings_first_fit_step(
    *,
    messages: list[dict[str, str]],
    ledger: ResultLedger,
    prompt_limit: int,
    count_messages: CountMessages,
    protected_result_ids: Sequence[str] = (),
) -> ReliefPass:
    """Apply at most one oldest-first strictly positive receipt substitution.

    The caller rerenders after every semantic or artifact effect and invokes
    this function again if needed. This makes maintenance growth part of the
    next complete feasibility decision and prevents a compact exact body from
    being replaced by a larger receipt.
    """
    before = count_messages(messages)
    if before <= prompt_limit:
        return ReliefPass(before, True, (), ())
    protected = frozenset(protected_result_ids)
    audits: list[ReliefCandidateAudit] = []
    for record in ledger.eligible(
        kinds=("source_observation", "exact_reopen_observation")
    ):
        if record.result_id in protected:
            audits.append(
                ReliefCandidateAudit(
                    record.result_id, before, before, 0, False, "protected_pending_result"
                )
            )
            continue
        index = record.message_index
        if index is None or messages[index] != {"role": "user", "content": record.exact_content}:
            raise RuntimeError(f"relief message binding failed: {record.result_id}")
        prospective = deepcopy(messages)
        prospective[index] = {"role": "user", "content": record.receipt()}
        after = count_messages(prospective)
        savings = before - after
        if savings <= 0:
            audits.append(
                ReliefCandidateAudit(
                    record.result_id, before, after, savings, False, "non_positive_savings"
                )
            )
            continue
        messages[index] = prospective[index]
        ledger.mark_external(record.result_id)
        audits.append(
            ReliefCandidateAudit(record.result_id, before, after, savings, True, "first_positive")
        )
        return ReliefPass(after, after <= prompt_limit, (record.result_id,), tuple(audits))
    return ReliefPass(before, False, (), tuple(audits))
