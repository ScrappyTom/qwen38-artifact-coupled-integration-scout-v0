"""Bounded model-facing lifecycle for exact candidate mutation effects."""

from host_refactor.effect_lifecycle.policy import (
    CURRENT_EFFECT_SLOT,
    CandidateEffectLifecycle,
    EffectLifecycleOutcome,
)
from host_refactor.effect_lifecycle.orchestrator import (
    EffectLifecycleInteractionOrchestrator,
)
from host_refactor.effect_lifecycle.verification import (
    VerificationResidencyLifecycle,
    VerificationResidencyOutcome,
)

__all__ = [
    "CURRENT_EFFECT_SLOT",
    "CandidateEffectLifecycle",
    "EffectLifecycleOutcome",
    "EffectLifecycleInteractionOrchestrator",
    "VerificationResidencyLifecycle",
    "VerificationResidencyOutcome",
]
