from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reactive_runtime.integration import next_artifact, validate_integration
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
from reactive_runtime.world import ArchitectureWorld


ROOT = Path(__file__).resolve().parents[1]


class FullLoopTests(unittest.TestCase):
    def _exercise(self, configuration_id: str) -> tuple[str, str, str]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        world = ArchitectureWorld(ROOT / "task", Path(temporary.name))
        ledger = ResultLedger()
        execution = world.execute({"action": "read_source", "source_id": "S02", "start_line": 1, "end_line": 70}, result_id="RESULT-001", ledger=ledger)
        record = world.make_result_record(execution, result_id="RESULT-001", acquired_call=1)
        ledger.add(record)
        messages = [{"role": "system", "content": "contract"}, {"role": "user", "content": record.exact_content}]
        ledger.mark_model_visible("RESULT-001", call_index=2, message_index=1)
        count = lambda rows: sum(len(row["content"]) for row in rows)
        before = count(messages)
        relief = positive_savings_first_fit_step(messages=messages, ledger=ledger, prompt_limit=before - 1, count_messages=count)
        self.assertEqual(("RESULT-001",), relief.selected_result_ids)
        body = "# Evidence Integration Ledger\n\nR02 conservative fire-arrival gates are supported by [S02].\n"
        validation = validate_integration(body, count_text=lambda value: len(value.split()), allowed_source_ids=("S02",))
        self.assertTrue(validation.valid)
        artifact = next_artifact(prior=None, body=body, body_tokens=validation.output_tokens, result=record)
        candidate_before = world.candidate_sha256
        maintenance_effect = world.apply_integration(configuration_id, artifact)
        actor_effect = world.execute({"action": "upsert_decision_section", "heading": "Decision, scope, and authority", "body": "Use a conservative Cedar Valley evacuation [S02]."}, result_id="RESULT-003")
        check = world.execute({"action": "run_check"}, result_id="RESULT-004")
        world.execute({"action": "upsert_decision_section", "heading": "Verification, readiness, blockers, and falsifiers", "body": "The evacuation decision remains blocked and falsifiable [S02]."}, result_id="RESULT-005")
        self.assertEqual("stale", world.current_check_binding()["currency"])
        world.execute({"action": "run_check"}, result_id="RESULT-006")
        self.assertEqual("current", world.current_check_binding()["currency"])
        submission = world.execute({"action": "submit"}, result_id="RESULT-007")
        self.assertEqual("submission_effect", submission.result_kind)
        self.assertEqual("candidate_effect", actor_effect.result_kind)
        self.assertEqual("check_observation", check.result_kind)
        return candidate_before, maintenance_effect.result_kind, world.candidate_sha256

    def test_detached_full_loop(self) -> None:
        before, kind, after = self._exercise("D0_DETACHED")
        self.assertEqual("semantic_state_effect", kind)
        self.assertNotEqual(before, after)  # ordinary actor section effect, not maintenance

    def test_coupled_full_loop(self) -> None:
        before, kind, after = self._exercise("A1_COUPLED")
        self.assertEqual("candidate_effect", kind)
        self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
