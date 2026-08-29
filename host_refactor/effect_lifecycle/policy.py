from __future__ import annotations

from dataclasses import dataclass

from reactive_runtime.canonical import canonical_json_text

from host_refactor.kernel import HostKernel, InvalidTransition
from host_refactor.model import (
    DeliveryState,
    ExactStateObject,
    ResultProjection,
    TranscriptEntry,
)


CURRENT_EFFECT_SLOT = "current_candidate_effect"
CURRENT_EFFECT_ENTRY = "HOST-CURRENT-CANDIDATE-EFFECT"


@dataclass(frozen=True)
class EffectLifecycleOutcome:
    kernel: HostKernel
    externalized_result_ids: tuple[str, ...]
    latest_effect_result_id: str | None
    latest_effect_delivery_state: str | None


class CandidateEffectLifecycle:
    """Bound candidate effects without inferring semantic uptake or readiness."""

    def reconcile(self, kernel: HostKernel) -> EffectLifecycleOutcome:
        state = kernel.project()
        effects = sorted(
            (
                row
                for row in state.results.values()
                if row.result.result_kind == "candidate_effect"
            ),
            key=lambda row: (row.result.acquired_call, row.result.result_id),
        )
        if not effects:
            return EffectLifecycleOutcome(kernel, (), None, None)

        candidate = state.state_slots.get("current_candidate")
        if candidate is None:
            raise InvalidTransition("candidate effects require current_candidate state")
        current_sha = candidate.metadata.get("candidate_sha256")
        if not isinstance(current_sha, str) or not current_sha:
            raise InvalidTransition("current_candidate lacks candidate_sha256")
        self._validate_linear_lineage(effects, current_sha)

        externalized: list[str] = []
        current = kernel
        for row in effects:
            if row.delivery_state is not DeliveryState.DELIVERED_RESIDENT:
                continue
            current = current.externalize_applied_candidate_effect(
                row.result.result_id,
                current_candidate_sha256=current_sha,
            )
            externalized.append(row.result.result_id)

        latest = current.project().results[effects[-1].result.result_id]
        state_object = self._state_object(latest, current_sha)
        projected = current.project()
        prior = projected.state_slots.get(CURRENT_EFFECT_SLOT)
        if prior is None or prior.as_dict() != state_object.as_dict():
            current = current.set_state_object(state_object)
        if not any(
            entry.state_slot_id == CURRENT_EFFECT_SLOT
            for entry in current.project().transcript
        ):
            current = current.append_transcript(
                TranscriptEntry(
                    entry_id=CURRENT_EFFECT_ENTRY,
                    role="user",
                    content=state_object.exact_content,
                    state_slot_id=CURRENT_EFFECT_SLOT,
                    entry_kind="exact_state_slot",
                )
            )
        latest_state = current.project().results[latest.result.result_id].delivery_state
        return EffectLifecycleOutcome(
            kernel=current,
            externalized_result_ids=tuple(externalized),
            latest_effect_result_id=latest.result.result_id,
            latest_effect_delivery_state=latest_state.value,
        )

    @staticmethod
    def _validate_linear_lineage(
        effects: list[ResultProjection], current_sha: str
    ) -> None:
        previous_after: str | None = None
        for projected in effects:
            result = projected.result
            before = result.metadata.get("before_sha256")
            after = result.candidate_sha256_after
            if not isinstance(before, str) or not before:
                raise InvalidTransition(
                    f"candidate effect lacks before_sha256: {result.result_id}"
                )
            if previous_after is not None and before != previous_after:
                raise InvalidTransition(
                    f"candidate effect lineage is not linear: {result.result_id}"
                )
            previous_after = after
        if previous_after != current_sha:
            raise InvalidTransition(
                "latest candidate effect does not produce current candidate"
            )

    @staticmethod
    def _state_object(
        projected: ResultProjection, current_sha: str
    ) -> ExactStateObject:
        result = projected.result
        delivery_state = projected.delivery_state
        content = canonical_json_text(
            {
                "candidate_sha256_after": result.candidate_sha256_after,
                "candidate_sha256_before": result.metadata.get("before_sha256"),
                "current_candidate_contains_effect": (
                    result.candidate_sha256_after == current_sha
                ),
                "current_candidate_sha256": current_sha,
                "delivery_state": delivery_state.value,
                "exact_effect_reopen_action": {
                    "action": "reopen_exact",
                    "result_id": result.result_id,
                },
                "exact_effect_sha256": result.exact_content_sha256,
                "exact_effect_size_bytes": len(result.exact_content.encode("utf-8")),
                "first_delivered_call": projected.first_delivered_call,
                "last_delivered_call": projected.last_delivered_call,
                "result_id": result.result_id,
                "schema": "bounded-host-current-candidate-effect-v0",
                "semantic_uptake": "not_inferred_from_delivery",
            }
        )
        return ExactStateObject(
            slot_id=CURRENT_EFFECT_SLOT,
            object_id="candidate-effect-currentness",
            object_version=(
                f"{result.result_id}:{delivery_state.value}:"
                f"{result.exact_content_sha256}"
            ),
            exact_content=content,
            metadata={
                "candidate_sha256_after": result.candidate_sha256_after,
                "current_candidate_sha256": current_sha,
                "delivery_state": delivery_state.value,
                "result_id": result.result_id,
                "semantic_uptake_inferred": False,
            },
        )
