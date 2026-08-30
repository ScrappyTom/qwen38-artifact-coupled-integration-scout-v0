from __future__ import annotations

from dataclasses import dataclass

from host_refactor.kernel import HostKernel, InvalidTransition
from host_refactor.model import DeliveryState


VERIFICATION_SLOT = "current_verification_frame"


@dataclass(frozen=True)
class VerificationResidencyOutcome:
    kernel: HostKernel
    externalized_result_ids: tuple[str, ...]
    represented_check_result_id: str | None


class VerificationResidencyLifecycle:
    """Turn over delivered checks already bound into current verification state.

    The policy is deliberately mechanical.  It does not decide which findings
    matter, whether the candidate improved, or whether the actor understood a
    check.  It requires one exact replaceable state slot to retain the complete
    latest check projection and its result/hash/candidate binding first.
    """

    def reconcile(self, kernel: HostKernel) -> VerificationResidencyOutcome:
        state = kernel.project()
        slot = state.state_slots.get(VERIFICATION_SLOT)
        if slot is None:
            return VerificationResidencyOutcome(kernel, (), None)
        represented_id = slot.metadata.get("check_result_id")
        if not isinstance(represented_id, str) or not represented_id:
            return VerificationResidencyOutcome(kernel, (), None)
        represented = state.results.get(represented_id)
        if represented is None:
            raise InvalidTransition("verification slot names unknown check result")
        if represented.first_delivered_call is None:
            return VerificationResidencyOutcome(kernel, (), represented_id)

        eligible = sorted(
            (
                row
                for row in state.results.values()
                if row.result.result_kind == "check_observation"
                and row.delivery_state is DeliveryState.DELIVERED_RESIDENT
                and row.result.acquired_call <= represented.result.acquired_call
            ),
            key=lambda row: (row.result.acquired_call, row.result.result_id),
        )
        current = kernel
        externalized: list[str] = []
        for row in eligible:
            current = current.externalize_check_observation(
                row.result.result_id,
                verification_slot_id=VERIFICATION_SLOT,
                verification_state_sha256=slot.content_sha256,
                represented_check_result_id=represented_id,
            )
            externalized.append(row.result.result_id)
        return VerificationResidencyOutcome(
            current,
            tuple(externalized),
            represented_id,
        )
