"""Whole-system interaction orchestration around the refactored host core."""

from interaction_scout.lifecycle import (
    BASELINE_CONFIGURATION,
    TREATMENT_CONFIGURATION,
    InteractionLifecycle,
    InteractionOrchestrator,
)

__all__ = [
    "BASELINE_CONFIGURATION",
    "TREATMENT_CONFIGURATION",
    "InteractionLifecycle",
    "InteractionOrchestrator",
]
