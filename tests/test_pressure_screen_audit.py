from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from reactive_runtime.records import ResultLedger
from reactive_runtime.world import ArchitectureWorld
from tools.audit_pressure_screen import audit
from tools import run_pressure_screen as runner


ROOT = Path(__file__).resolve().parents[1]


class PressureScreenEligibilityTests(unittest.TestCase):
    def test_auditor_refuses_to_manufacture_a_pre_run_boundary(self) -> None:
        result = audit(ROOT, write_outputs=False)
        self.assertFalse(result["passed"])
        self.assertIn("missing:AUTHORIZATION_RECEIPT.json", result["failures"])

    def test_live_screen_requires_realized_demand_and_clean_pretreatment_state(self) -> None:
        source = inspect.getsource(runner)
        self.assertIn("delivered_sources < 4", source)
        self.assertIn("candidate_changed_before_pressure", source)
        self.assertIn("check_ran_before_pressure", source)
        self.assertIn("pending_result_is_not_source_observation", source)
        self.assertNotIn("source_corpus_tokens >", source)

    def test_pure_eligibility_gate_accepts_only_a_clean_acquisition_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = ArchitectureWorld(ROOT / "task", Path(temporary))
            initial = world.candidate_sha256
            ledger = ResultLedger()
            for ordinal, source_id in enumerate(("S01", "S03", "S06", "S07", "S08"), 1):
                execution = world.execute(
                    {"action": "read_source", "source_id": source_id, "start_line": 1, "end_line": 10},
                    result_id=f"RESULT-{ordinal:03d}",
                    ledger=ledger,
                )
                record = world.make_result_record(
                    execution, result_id=f"RESULT-{ordinal:03d}", acquired_call=ordinal
                )
                ledger.add(record)
                if ordinal < 5:
                    ledger.mark_model_visible(
                        record.result_id, call_index=ordinal + 1, message_index=ordinal
                    )
            pending = ledger.get("RESULT-005")
            self.assertEqual(
                [],
                runner.boundary_eligibility_failures(
                    pending=pending,
                    ledger=ledger,
                    world=world,
                    initial_candidate_sha256=initial,
                ),
            )


if __name__ == "__main__":
    unittest.main()
