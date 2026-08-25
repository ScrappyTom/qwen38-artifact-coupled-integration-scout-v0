import unittest

from reactive_runtime.trajectory_budget import ConstructionBudget


class ConstructionBudgetTests(unittest.TestCase):
    def test_frozen_default_doubles_the_clean_completion_tail(self) -> None:
        budget = ConstructionBudget()
        self.assertEqual(26, budget.maximum_preconstruction_calls)
        self.assertEqual(8, budget.postconstruction_calls)
        self.assertEqual(34, budget.maximum_total_calls)
        self.assertGreaterEqual(budget.postconstruction_calls, 2 * 4)

    def test_no_construction_stops_at_preconstruction_ceiling(self) -> None:
        budget = ConstructionBudget(maximum_preconstruction_calls=3, postconstruction_calls=2)
        for _ in range(3):
            budget.record_call(construction_milestone_passed=False)
        self.assertFalse(budget.can_call())
        self.assertEqual("construction_milestone_not_reached", budget.exhaustion_disposition())

    def test_milestone_grants_exact_postconstruction_tail(self) -> None:
        budget = ConstructionBudget(maximum_preconstruction_calls=5, postconstruction_calls=3)
        self.assertFalse(budget.record_call(construction_milestone_passed=False))
        self.assertTrue(budget.record_call(construction_milestone_passed=True))
        for _ in range(3):
            budget.record_call(construction_milestone_passed=True)
        self.assertEqual(2, budget.milestone_call)
        self.assertEqual(5, budget.actor_calls)
        self.assertFalse(budget.can_call())
        self.assertEqual("postconstruction_budget_exhausted", budget.exhaustion_disposition())

    def test_latest_eligible_milestone_still_receives_full_tail(self) -> None:
        budget = ConstructionBudget(maximum_preconstruction_calls=4, postconstruction_calls=2)
        for _ in range(3):
            budget.record_call(construction_milestone_passed=False)
        budget.record_call(construction_milestone_passed=True)
        budget.record_call(construction_milestone_passed=True)
        budget.record_call(construction_milestone_passed=True)
        self.assertEqual(6, budget.actor_calls)
        self.assertEqual(6, budget.maximum_total_calls)
        self.assertFalse(budget.can_call())


if __name__ == "__main__":
    unittest.main()
