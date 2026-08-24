from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConstructionBudget:
    """Event-contingent actor budget with a protected completion tail.

    The milestone is mechanical and grants time; it is not evidence of quality
    or readiness.  Every arm receives the same maximum pre-construction window
    and exactly the same post-milestone decision allowance.
    """

    maximum_preconstruction_calls: int = 22
    postconstruction_calls: int = 8
    actor_calls: int = 0
    milestone_call: int | None = None

    @property
    def maximum_total_calls(self) -> int:
        return self.maximum_preconstruction_calls + self.postconstruction_calls

    def can_call(self) -> bool:
        if self.milestone_call is None:
            return self.actor_calls < self.maximum_preconstruction_calls
        return self.actor_calls < self.milestone_call + self.postconstruction_calls

    def record_call(self, *, construction_milestone_passed: bool) -> bool:
        if not self.can_call():
            raise RuntimeError("actor call admitted after trajectory budget exhausted")
        self.actor_calls += 1
        crossed = self.milestone_call is None and construction_milestone_passed
        if crossed:
            self.milestone_call = self.actor_calls
        return crossed

    def exhaustion_disposition(self) -> str:
        if self.can_call():
            raise RuntimeError("trajectory budget is not exhausted")
        if self.milestone_call is None:
            return "construction_milestone_not_reached"
        return "postconstruction_budget_exhausted"

    def as_dict(self) -> dict[str, int | None]:
        remaining = (
            self.maximum_preconstruction_calls - self.actor_calls
            if self.milestone_call is None
            else self.milestone_call + self.postconstruction_calls - self.actor_calls
        )
        return {
            "actor_calls": self.actor_calls,
            "maximum_preconstruction_calls": self.maximum_preconstruction_calls,
            "postconstruction_calls": self.postconstruction_calls,
            "maximum_total_calls": self.maximum_total_calls,
            "milestone_call": self.milestone_call,
            "remaining_calls_in_current_window": max(0, remaining),
        }
