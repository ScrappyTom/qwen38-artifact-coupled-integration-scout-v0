from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reactive_runtime.configuration import delta_actor_actions, delta_common_actions
from reactive_runtime.meridian_world import MeridianWorld
from reactive_runtime.records import ResultLedger
from reactive_runtime.source_delta import (
    DELTA_PREFIX,
    SourceEvidenceRegister,
    SourceSlotRecord,
    validate_source_delta,
)
from tools import run_meridian_pressure_screen as runner
from tools.materialize_meridian_world import SOURCE_IDS, SPECS, document


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "task_meridian"


def delta_block(source_id: str, version: str, body_extra: str = "") -> str:
    return f"""{DELTA_PREFIX}
## SOURCE {source_id}
VERSION {version}
### REQUIREMENTS
Q01 Q02
### FINDINGS
Exact bounded finding for {source_id}. {body_extra}
### QUALIFICATIONS AND CONFLICTS
The source-local claim remains qualified and non-authoritative.
### UNKNOWNS AND REOPEN CONDITIONS
Reopen {source_id} after a version change or unresolved conflict.
"""


class MeridianStage0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads((TASK / "SOURCE_CATALOG.json").read_text(encoding="utf-8"))
        cls.evaluator = json.loads((TASK / "EVALUATOR.json").read_text(encoding="utf-8"))
        cls.preflight = json.loads((ROOT / "MERIDIAN_STAGE0_PREFLIGHT.json").read_text(encoding="utf-8"))

    def test_fresh_world_is_exact_and_source_ids_are_non_isomorphic(self) -> None:
        lock = json.loads((TASK / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
        self.assertEqual("meridian-sterile-infusion-recovery-v0", lock["task_id"])
        self.assertEqual(16, len(lock["source_custody"]))
        self.assertTrue(all(source_id.isalpha() for source_id in SOURCE_IDS))
        self.assertTrue(all(row["line_count"] == 70 for row in lock["source_custody"]))
        for source_id, spec in zip(SOURCE_IDS, SPECS, strict=True):
            path = TASK / "sources" / spec.filename
            self.assertEqual(document(spec), path.read_text(encoding="utf-8"), source_id)

    def test_requirement_source_geometry_is_many_to_many_and_actor_hidden(self) -> None:
        mapping = self.evaluator["gold_requirement_sources"]
        self.assertEqual(12, len(mapping))
        self.assertTrue(all(len(sources) >= 3 for sources in mapping.values()))
        represented = {source_id for sources in mapping.values() for source_id in sources}
        self.assertEqual(set(SOURCE_IDS), represented)
        task = (TASK / "TASK.md").read_text(encoding="utf-8")
        self.assertNotIn("gold_requirement_sources", task)
        self.assertNotIn('"Q01": ["AXIOM"', task)

    def test_actor_catalog_hides_activation_and_gold_domains(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = MeridianWorld(TASK, Path(temporary))
            actor_catalog = json.loads(world.source_catalog_for_actor())
        for row in actor_catalog["sources"]:
            self.assertNotIn("activation_min_lines", row)
            self.assertNotIn("evidence_domain", row)

    def test_complete_configuration_action_ownership_is_explicit(self) -> None:
        w0 = delta_actor_actions("W0_DIRECT_WORK")
        l1 = delta_actor_actions("L1_LOCAL_DELTA")
        self.assertIn("upsert_evidence_slot", w0)
        self.assertNotIn("upsert_evidence_slot", l1)
        self.assertEqual(set(l1), set(delta_common_actions()))
        self.assertEqual(set(w0) - {"upsert_evidence_slot"}, set(l1))

    def test_local_delta_accepts_exact_scope_and_rejects_global_or_unseen_scope(self) -> None:
        versions = {row["source_id"]: row["sha256"] for row in self.catalog["sources"]}
        accepted = validate_source_delta(
            delta_block("AXIOM", versions["AXIOM"]),
            count_text=lambda value: len(value.split()),
            allowed_source_versions={"AXIOM": versions["AXIOM"]},
            known_source_ids=versions,
        )
        self.assertTrue(accepted.valid, accepted.issues)
        unseen = validate_source_delta(
            delta_block("AXIOM", versions["AXIOM"], "Related BRAMBLE evidence is decisive."),
            count_text=lambda value: len(value.split()),
            allowed_source_versions={"AXIOM": versions["AXIOM"]},
            known_source_ids=versions,
        )
        self.assertIn("unobserved_source_reference", unseen.issues)
        incomplete = validate_source_delta(
            delta_block("AXIOM", versions["AXIOM"]),
            count_text=lambda value: len(value.split()),
            allowed_source_versions={
                "AXIOM": versions["AXIOM"],
                "BRAMBLE": versions["BRAMBLE"],
            },
            known_source_ids=versions,
        )
        self.assertIn("incomplete_current_batch_coverage", incomplete.issues)
        global_state = validate_source_delta(
            delta_block("AXIOM", versions["AXIOM"], "# Source Evidence Register"),
            count_text=lambda value: len(value.split()),
            allowed_source_versions={"AXIOM": versions["AXIOM"]},
            known_source_ids=versions,
        )
        self.assertIn("global_register_replacement_forbidden", global_state.issues)

    def test_source_version_replacement_preserves_unrelated_slots(self) -> None:
        first = SourceSlotRecord.create(
            source_id="AXIOM",
            source_version="a" * 64,
            body="Q01 exact local body AXIOM",
            origin="fixture",
            result_ids=("R1",),
        )
        other = SourceSlotRecord.create(
            source_id="BRAMBLE",
            source_version="b" * 64,
            body="Q02 exact local body BRAMBLE",
            origin="fixture",
            result_ids=("R2",),
        )
        register = SourceEvidenceRegister({"AXIOM": first, "BRAMBLE": other})
        revised = SourceSlotRecord.create(
            source_id="AXIOM",
            source_version="c" * 64,
            body="Q01 revised exact local body AXIOM",
            origin="fixture",
            result_ids=("R3",),
        )
        result = register.merge((revised,))
        self.assertEqual(revised, result.get("AXIOM"))
        self.assertEqual(other, result.get("BRAMBLE"))
        self.assertEqual(result.slots(), SourceEvidenceRegister.parse(result.render()).slots())

    def test_direct_slot_requires_visible_exact_provenance_and_equal_token_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = MeridianWorld(
                TASK,
                Path(temporary),
                count_text=lambda value: len(value.split()),
            )
            ledger = ResultLedger()
            version = world.sources["AXIOM"].sha256
            action = {
                "action": "upsert_evidence_slot",
                "source_id": "AXIOM",
                "source_version": version,
                "content": "Q01 bounded source-local AXIOM evidence",
            }
            with self.assertRaisesRegex(ValueError, "crossed a model boundary"):
                world.execute(action, result_id="RESULT-002", ledger=ledger)
            execution = world.execute(
                {
                    "action": "read_source",
                    "source_id": "AXIOM",
                    "start_line": 1,
                    "end_line": 70,
                },
                result_id="RESULT-001",
                ledger=ledger,
            )
            record = world.make_result_record(
                execution, result_id="RESULT-001", acquired_call=1
            )
            ledger.add(record)
            ledger.mark_model_visible(
                "RESULT-001", call_index=2, message_index=4
            )
            world.execute(action, result_id="RESULT-002", ledger=ledger)
            self.assertEqual(
                ("RESULT-001",),
                world.evidence_register().get("AXIOM").result_ids,
            )
            oversized = dict(action)
            oversized["content"] = "AXIOM " + "word " * 651
            with self.assertRaisesRegex(ValueError, "token slot budget"):
                world.execute(oversized, result_id="RESULT-003", ledger=ledger)

    def test_register_parser_rejects_unbound_trailing_content(self) -> None:
        rendered = SourceEvidenceRegister().render()
        with self.assertRaisesRegex(ValueError, "trailing"):
            SourceEvidenceRegister.parse(rendered + "unbound text\n")

    def test_preflight_uses_realized_packet_geometry_and_complete_loops(self) -> None:
        self.assertEqual(3049, self.preflight["base_actor_prompt_tokens"])
        self.assertEqual(23730, self.preflight["source_corpus_tokens"])
        ingress = self.preflight["permitted_ingress_geometry"]
        self.assertTrue(ingress["every_full_single_admissible"])
        self.assertTrue(ingress["every_full_pair_admissible"])
        pressure = self.preflight["prospective_pressure_opportunity"]
        self.assertEqual(6, pressure["step"])
        self.assertEqual(2636, pressure["overflow_tokens"])
        self.assertEqual(["RESULT-001"], pressure["positive_relief_result_ids"])
        self.assertLessEqual(pressure["positive_relief_after_tokens"], runner.PROMPT_LIMIT)
        self.assertTrue(all(row["fits"] for row in self.preflight["source_delta_prompt_geometry"]))
        fixtures = {
            row["configuration_id"]: row
            for row in self.preflight["provider_free_complete_system_fixtures"]
        }
        self.assertEqual({"W0_DIRECT_WORK", "L1_LOCAL_DELTA"}, set(fixtures))
        for row in fixtures.values():
            self.assertEqual(10, row["source_slots"])
            self.assertTrue(row["source_slot_result_provenance_complete"])
            self.assertLessEqual(row["maximum_source_slot_tokens"], 650)
            self.assertTrue(row["unrelated_slots_preserved"])
            self.assertTrue(row["version_replacement_preserved_unrelated"])
            self.assertFalse(row["first_check_passed"])
            self.assertTrue(row["check_stale_after_repair"])
            self.assertTrue(row["recheck_passed"])
            self.assertEqual("current", row["recheck_currency"])
            self.assertTrue(row["submitted"])
            self.assertEqual(
                "not_adjudicated",
                row["mechanical_final_evaluation"]["closure_readiness"],
            )

    def test_pressure_screen_is_common_and_treatment_free(self) -> None:
        contract = json.loads((ROOT / "MERIDIAN_PRESSURE_SCREEN_CONTRACT.json").read_text(encoding="utf-8"))
        request = json.loads((ROOT / "MERIDIAN_PRESSURE_SCREEN_AUTHORIZATION_REQUEST.json").read_text(encoding="utf-8"))
        self.assertEqual(runner.RUN_ID, contract["run_id"])
        self.assertEqual(runner.SCOPE, contract["scope"])
        self.assertEqual(runner.SEED, contract["seed"])
        self.assertEqual(runner.MAX_CALLS, contract["maximum_actor_calls"])
        self.assertFalse(contract["treatment_present"])
        self.assertFalse(contract["semantic_maintenance_present"])
        self.assertFalse(request["authorized"])
        source = Path(runner.__file__).read_text(encoding="utf-8")
        self.assertNotIn("source_delta_messages", source)
        self.assertNotIn("apply_source_delta", source)
        self.assertIn("positive_savings_first_fit_step", source)
        self.assertIn("boundary_eligibility_failures", source)


if __name__ == "__main__":
    unittest.main()
