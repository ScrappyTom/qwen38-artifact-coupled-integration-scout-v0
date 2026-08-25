from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from reactive_runtime.activation import boundary_eligibility_failures
from reactive_runtime.records import ResultLedger
from reactive_runtime.world import ArchitectureWorld
from tools.audit_pressure_screen import audit
from tools import run_pressure_screen as runner


ROOT = Path(__file__).resolve().parents[1]


def add_read(
    world: ArchitectureWorld,
    ledger: ResultLedger,
    result_id: str,
    source_id: str,
    start: int,
    end: int,
    *,
    visible: bool,
) -> object:
    execution = world.execute(
        {"action": "read_source", "source_id": source_id, "start_line": start, "end_line": end},
        result_id=result_id,
        ledger=ledger,
    )
    record = world.make_result_record(execution, result_id=result_id, acquired_call=len(ledger.records()) + 1)
    ledger.add(record)
    if visible:
        ledger.mark_model_visible(
            result_id, call_index=len(ledger.records()) + 1, message_index=len(ledger.records())
        )
    return record


class PressureScreenEligibilityTests(unittest.TestCase):
    def test_auditor_accepts_exact_live_boundary(self) -> None:
        result = audit(ROOT, write_outputs=False)
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual([], result["failures"])
        self.assertEqual(5, result["actor_calls"])
        self.assertEqual("RESULT-005", result["pending_result_id"])
        self.assertEqual(2384, result["overflow_tokens"])
        self.assertEqual(["RESULT-001"], result["positive_relief_result_ids"])

    def test_live_gate_uses_coverage_not_result_objects_or_world_size(self) -> None:
        source = inspect.getsource(boundary_eligibility_failures)
        self.assertIn("insufficient_delivered_source_coverage", source)
        self.assertIn("insufficient_delivered_evidence_domains", source)
        self.assertIn("pending_observation_has_no_novel_source_lines", source)
        self.assertNotIn("source_corpus_tokens", source)
        self.assertNotIn("result object", source.casefold())
        runner_source = inspect.getsource(runner)
        self.assertIn("activation.as_dict()", runner_source)

    def test_four_covered_sources_across_domains_qualify(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = ArchitectureWorld(ROOT / "task", Path(temporary))
            initial = world.candidate_sha256
            ledger = ResultLedger()
            for ordinal, source_id in enumerate(("S01", "S02", "S03", "S06"), 1):
                add_read(world, ledger, f"RESULT-{ordinal:03d}", source_id, 1, 55, visible=True)
            pending = add_read(world, ledger, "RESULT-005", "S04", 1, 70, visible=False)
            failures, snapshot = boundary_eligibility_failures(
                pending=pending,
                ledger=ledger,
                world=world,
                initial_candidate_sha256=initial,
            )
            self.assertEqual([], failures)
            self.assertEqual(("S01", "S02", "S03", "S06"), snapshot.qualifying_sources)
            self.assertEqual(("authority", "demand", "hazard", "shelter_care"), snapshot.qualifying_domains)
            self.assertEqual(70, snapshot.pending_novel_lines)

    def test_four_probe_results_do_not_qualify(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = ArchitectureWorld(ROOT / "task", Path(temporary))
            ledger = ResultLedger()
            for ordinal, source_id in enumerate(("S01", "S02", "S03", "S06"), 1):
                add_read(world, ledger, f"RESULT-{ordinal:03d}", source_id, 1, 10, visible=True)
            pending = add_read(world, ledger, "RESULT-005", "S04", 1, 70, visible=False)
            failures, _ = boundary_eligibility_failures(
                pending=pending,
                ledger=ledger,
                world=world,
                initial_candidate_sha256=world.candidate_sha256,
            )
            self.assertIn("insufficient_delivered_source_coverage", failures)

    def test_two_batch_objects_can_carry_four_qualifying_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = ArchitectureWorld(ROOT / "task", Path(temporary))
            ledger = ResultLedger()
            for ordinal, pair in enumerate((("S01", "S02"), ("S03", "S06")), 1):
                action = {
                    "action": "read_batch",
                    "requests": [
                        {"source_id": source_id, "start_line": 1, "end_line": 70}
                        for source_id in pair
                    ],
                }
                result_id = f"RESULT-{ordinal:03d}"
                execution = world.execute(action, result_id=result_id, ledger=ledger)
                record = world.make_result_record(execution, result_id=result_id, acquired_call=ordinal)
                ledger.add(record)
                ledger.mark_model_visible(result_id, call_index=ordinal + 1, message_index=ordinal)
            pending = add_read(world, ledger, "RESULT-003", "S04", 1, 70, visible=False)
            failures, snapshot = boundary_eligibility_failures(
                pending=pending,
                ledger=ledger,
                world=world,
                initial_candidate_sha256=world.candidate_sha256,
            )
            self.assertEqual([], failures)
            self.assertEqual(4, len(snapshot.qualifying_sources))
            self.assertEqual(2, sum(row.result_kind == "source_observation" for row in ledger.records()[:-1]))


if __name__ == "__main__":
    unittest.main()
