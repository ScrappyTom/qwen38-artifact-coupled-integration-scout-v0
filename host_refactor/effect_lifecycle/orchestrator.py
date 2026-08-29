from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable, Mapping, Any

from host_refactor.checkpoint import RuntimeCounters
from host_refactor.effect_lifecycle.policy import CandidateEffectLifecycle
from host_refactor.kernel import HostKernel
from interaction_scout.lifecycle import InteractionOrchestrator, InteractionStep


class EffectLifecycleInteractionOrchestrator(InteractionOrchestrator):
    """Future-only Trellis path with bounded candidate-effect residency."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.effect_lifecycle = CandidateEffectLifecycle()

    def prepare(
        self,
        kernel: HostKernel,
        counters: RuntimeCounters,
        *,
        custody_root: Path | None = None,
    ) -> tuple[HostKernel, RuntimeCounters]:
        reconciled = self.effect_lifecycle.reconcile(kernel)
        return super().prepare(
            reconciled.kernel,
            counters,
            custody_root=custody_root,
        )

    def step(
        self,
        *,
        kernel: HostKernel,
        counters: RuntimeCounters,
        actor_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        custody_root: Path | None = None,
    ) -> InteractionStep:
        step = super().step(
            kernel=kernel,
            counters=counters,
            actor_complete=actor_complete,
            custody_root=custody_root,
        )
        if step.runner_step.kernel.project().terminal is not None:
            return step
        reconciled = self.effect_lifecycle.reconcile(step.runner_step.kernel)
        return replace(
            step,
            runner_step=replace(step.runner_step, kernel=reconciled.kernel),
        )
