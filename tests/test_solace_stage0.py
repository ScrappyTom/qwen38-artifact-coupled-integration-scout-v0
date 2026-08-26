from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reactive_runtime.anchored_provenance import (
    DELTA_PREFIX,
    AnchoredProvenanceRegister,
    admit_anchored_delta,
)
from reactive_runtime.configuration import anchored_relational_actor_actions
from reactive_runtime.records import ResultLedger
from reactive_runtime.solace_world import SolaceWorld
from tools import run_solace_pressure_screen as runner
from tools.materialize_solace_world import SOURCE_IDS, SPECS, document
from tools.solace_stage0 import TASK, batch_action, catalog, fixture_delta


ROOT = Path(__file__).resolve().parents[1]


class SolaceStage0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preflight = json.loads((ROOT / "SOLACE_STAGE0_PREFLIGHT.json").read_text(encoding="utf-8"))
        cls.catalog = catalog()

    def test_fresh_exact_world_and_task_lock(self) -> None:
        lock = json.loads((TASK / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
        self.assertEqual("solace-water-recovery-decision-v0", lock["task_id"])
        self.assertEqual(14, len(lock["source_custody"]))
        self.assertEqual(SOURCE_IDS, tuple(row["source_id"] for row in lock["source_custody"]))
        for spec in SPECS:
            self.assertEqual(document(spec), (TASK / "sources" / spec.filename).read_text(encoding="utf-8"))

    def test_hidden_requirement_graph_is_many_to_many(self) -> None:
        evaluator = json.loads((TASK / "EVALUATOR.json").read_text(encoding="utf-8"))
        mapping = evaluator["gold_requirement_sources"]
        self.assertEqual(12, len(mapping))
        self.assertTrue(all(len(sources) >= 4 for sources in mapping.values()))
        self.assertEqual(set(SOURCE_IDS), {source_id for sources in mapping.values() for source_id in sources})
        self.assertNotIn("gold_requirement_sources", (TASK / "TASK.md").read_text(encoding="utf-8"))

    def test_both_arms_share_exact_work_surface(self) -> None:
        self.assertEqual(
            anchored_relational_actor_actions("W0_DIRECT_EXACT_WORK_FRESH"),
            anchored_relational_actor_actions("L1_FAULT_TOLERANT_ANCHORED_PROVENANCE"),
        )

    def test_prospective_pressure_and_fallible_admission_geometry(self) -> None:
        pressure = self.preflight["prospective_pressure_opportunity"]
        self.assertEqual(6, pressure["step"])
        self.assertGreater(pressure["ordinary_prompt_tokens"], runner.PROMPT_LIMIT)
        self.assertLessEqual(pressure["relieved_prompt_tokens"], runner.PROMPT_LIMIT)
        self.assertEqual(["RESULT-001"], pressure["externalized_source_result_ids"])
        self.assertTrue(all(row["fits"] for row in self.preflight["maintenance_geometry"]))
        self.assertEqual("partial_admission", self.preflight["partial_admission_fixture"]["disposition"])
        self.assertEqual("zero_valid", self.preflight["zero_valid_fallback"]["disposition"])
        self.assertFalse(self.preflight["zero_valid_fallback"]["register_changed"])

    def test_provider_free_lifecycles_reach_same_candidate(self) -> None:
        fixtures = self.preflight["provider_free_complete_system_fixtures"]
        self.assertEqual(2, len(fixtures))
        self.assertEqual(fixtures[0]["candidate_sha256"], fixtures[1]["candidate_sha256"])
        self.assertEqual([0, 2], [row["register_claims"] for row in fixtures])
        self.assertTrue(all(row["check_stale_after_repair"] for row in fixtures))
        self.assertTrue(all(row["recheck_passed"] and row["submitted"] for row in fixtures))

    def test_anchored_relationship_admits_and_invalid_sibling_does_not_block(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = SolaceWorld(TASK, Path(temporary))
            ledger = ResultLedger()
            execution = world.execute(batch_action(("AURORA", "BASTION"), world), result_id="RESULT-001", ledger=ledger)
            record = world.make_result_record(execution, result_id="RESULT-001", acquired_call=1)
            valid = fixture_delta(world, record.result_id, ("AURORA",))
            invalid = fixture_delta(world, record.result_id, ("BASTION",)).split("\n", 1)[1].replace(
                "EVIDENCE_ANCHOR: ", "EVIDENCE_ANCHOR: absent ", 1
            )
            admission = admit_anchored_delta(
                valid + "\n" + invalid,
                count_text=lambda value: len(value.split()),
                source_catalog=self.catalog,
                task_root=TASK,
                newly_externalized=(record,),
                current_source_versions=world.source_versions,
            )
            self.assertEqual("partial_admission", admission.disposition)
            transition = AnchoredProvenanceRegister().apply(
                admission,
                current_source_versions=world.source_versions,
                count_text=lambda value: len(value.split()),
            )
        self.assertTrue(transition.changed)
        self.assertEqual(("AURORA_FIXTURE",), transition.admitted_claim_ids)
        self.assertEqual(("BASTION_FIXTURE",), transition.rejected_claim_ids)

    def test_screen_is_treatment_free_and_authorization_bound(self) -> None:
        source = (ROOT / "tools" / "run_solace_pressure_screen.py").read_text(encoding="utf-8")
        self.assertNotIn("anchored_delta_messages", source)
        self.assertNotIn("admit_anchored_delta", source)
        contract = json.loads((ROOT / "SOLACE_PRESSURE_SCREEN_CONTRACT.json").read_text(encoding="utf-8"))
        self.assertFalse(contract["semantic_maintenance_present"])
        self.assertFalse(contract["gpu_authorized"])
        self.assertEqual(28, contract["maximum_actor_calls"])


if __name__ == "__main__":
    unittest.main()
