from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from host_refactor.kernel import HostKernel
from host_refactor.model import DeliveryState
from host_refactor.packet import ModelPacket, PacketComposer


CountMessages = Callable[[list[dict[str, str]]], int]


@dataclass(frozen=True)
class ReliefAudit:
    result_id: str
    before_tokens: int
    prospective_tokens: int
    savings: int
    selected: bool
    reason: str


@dataclass(frozen=True)
class CapacityOutcome:
    kernel: HostKernel
    packet: ModelPacket
    prompt_tokens: int
    feasible: bool
    selected_result_ids: tuple[str, ...]
    audits: tuple[ReliefAudit, ...]
    blocker: str | None = None


class CapacityManager:
    """Deterministic, semantic-free, strictly-positive first-fit relief."""

    def __init__(
        self,
        *,
        composer: PacketComposer,
        count_messages: CountMessages,
        prompt_limit: int,
    ) -> None:
        if prompt_limit <= 0:
            raise ValueError("prompt limit must be positive")
        self.composer = composer
        self.count_messages = count_messages
        self.prompt_limit = prompt_limit

    def ensure_feasible(
        self,
        kernel: HostKernel,
        *,
        protected_result_ids: Sequence[str] = (),
    ) -> CapacityOutcome:
        current = kernel
        packet = self.composer.compose(current)
        tokens = self.count_messages(packet.message_list())
        if tokens <= self.prompt_limit:
            return CapacityOutcome(current, packet, tokens, True, (), ())
        protected = frozenset(protected_result_ids)
        selected: list[str] = []
        audits: list[ReliefAudit] = []
        attempted: set[str] = set()
        while tokens > self.prompt_limit:
            state = current.project()
            eligible = sorted(
                (
                    row
                    for row in state.results.values()
                    if row.delivery_state is DeliveryState.DELIVERED_RESIDENT
                    and row.result.relief_eligible
                    and row.result.result_id not in attempted
                ),
                key=lambda row: (
                    row.first_delivered_call
                    if row.first_delivered_call is not None
                    else 2**31,
                    row.result.result_id,
                ),
            )
            selected_this_pass = False
            for row in eligible:
                result_id = row.result.result_id
                attempted.add(result_id)
                if result_id in protected:
                    audits.append(
                        ReliefAudit(
                            result_id=result_id,
                            before_tokens=tokens,
                            prospective_tokens=tokens,
                            savings=0,
                            selected=False,
                            reason="protected_pending_result",
                        )
                    )
                    continue
                prospective_kernel = current.externalize(
                    result_id, reason="deterministic_first_fit_relief"
                )
                prospective_packet = self.composer.compose(prospective_kernel)
                prospective_tokens = self.count_messages(
                    prospective_packet.message_list()
                )
                savings = tokens - prospective_tokens
                if savings <= 0:
                    audits.append(
                        ReliefAudit(
                            result_id=result_id,
                            before_tokens=tokens,
                            prospective_tokens=prospective_tokens,
                            savings=savings,
                            selected=False,
                            reason="non_positive_savings",
                        )
                    )
                    continue
                audits.append(
                    ReliefAudit(
                        result_id=result_id,
                        before_tokens=tokens,
                        prospective_tokens=prospective_tokens,
                        savings=savings,
                        selected=True,
                        reason="first_positive_in_frozen_order",
                    )
                )
                current = prospective_kernel
                packet = prospective_packet
                tokens = prospective_tokens
                selected.append(result_id)
                selected_this_pass = True
                break
            if not selected_this_pass:
                return CapacityOutcome(
                    kernel=current,
                    packet=packet,
                    prompt_tokens=tokens,
                    feasible=False,
                    selected_result_ids=tuple(selected),
                    audits=tuple(audits),
                    blocker="no_strictly_positive_eligible_relief",
                )
        return CapacityOutcome(
            kernel=current,
            packet=packet,
            prompt_tokens=tokens,
            feasible=True,
            selected_result_ids=tuple(selected),
            audits=tuple(audits),
        )
