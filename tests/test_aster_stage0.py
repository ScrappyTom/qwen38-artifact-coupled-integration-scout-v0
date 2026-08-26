from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reactive_runtime.aster_world import AsterWorld
from reactive_runtime.configuration import relational_actor_actions
from reactive_runtime.records import ResultLedger
from reactive_runtime.relational_delta import (
    ProvenanceRegister,
    validate_relational_delta,
)
from tools import run_aster_pressure_screen as runner
from tools.aster_stage0 import batch_action, fixture_delta
from tools.materialize_aster_world import SOURCE_IDS, SPECS, document


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "task_aster"


class AsterStage0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog_value = json.loads(
            (TASK / "SOURCE_CATALOG.json").read_text(encoding="utf-8")
        )
        cls.catalog = {
            row["source_id"]: row for row in cls.catalog_value["sources"]
        }
        cls.evaluator = json.loads(
            (TASK / "EVALUATOR.json").read_text(encoding="utf-8")
        )
        cls.preflight = json.loads(
            (ROOT / "ASTER_STAGE0_PREFLIGHT.json").read_text(encoding="utf-8")
        )

    def test_fresh_world_is_exact_and_source_ids_are_non_isomorphic(self) -> None:
        lock = json.loads(
            (TASK / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8")
        )
        self.assertEqual("aster-payment-recovery-decision-v0", lock["task_id"])
        self.assertEqual(16, len(lock["source_custody"]))
        self.assertTrue(all(source_id.isalpha() for source_id in SOURCE_IDS))
        self.assertTrue(all(row["line_count"] == 64 for row in lock["source_custody"]))
        for source_id, spec in zip(SOURCE_IDS, SPECS, strict=True):
            path = TASK / "sources" / spec.filename
            self.assertEqual(document(spec), path.read_text(encoding="utf-8"), source_id)

    def test_requirement_graph_is_many_to_many_and_actor_hidden(self) -> None:
        mapping = self.evaluator["gold_requirement_sources"]
        self.assertEqual(12, len(mapping))
        self.assertTrue(all(len(sources) >= 4 for sources in mapping.values()))
        represented = {source_id for sources in mapping.values() for source_id in sources}
        self.assertEqual(set(SOURCE_IDS), represented)
        task = (TASK / "TASK.md").read_text(encoding="utf-8")
        self.assertNotIn("gold_requirement_sources", task)
        self.assertNotIn('"Q01": ["ANCHOR"', task)

    def test_actor_catalog_hides_activation_and_gold_domains(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = AsterWorld(TASK, Path(temporary))
            actor_catalog = json.loads(world.source_catalog_for_actor())
        for row in actor_catalog["sources"]:
            self.assertNotIn("activation_min_lines", row)
            self.assertNotIn("evidence_domain", row)

    def test_declared_read_examples_are_in_range(self) -> None:
        action_text = (TASK / "ACTIONS.md").read_text(encoding="utf-8")
        self.assertIn('"end_line":64', action_text)
        self.assertNotIn('"end_line":65', action_text)
        self.assertTrue(all(row["line_count"] == 64 for row in self.catalog.values()))

    def test_both_configurations_share_ordinary_exact_work_surface(self) -> None:
        w0 = relational_actor_actions("W0_DIRECT_EXACT_WORK")
        l1 = relational_actor_actions("L1_PROVENANCE_LOCAL_RELATIONAL")
        self.assertEqual(w0, l1)
        self.assertIn("replace_evidence_ledger", w0)
        self.assertIn("upsert_decision_section", w0)
        self.assertIn("run_check", w0)
        self.assertIn("submit", w0)

    def _record_fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        world = AsterWorld(TASK, Path(temporary.name))
        ledger = ResultLedger()
        execution = world.execute(
            batch_action(("ANCHOR", "BRIDGE"), world),
            result_id="RESULT-001",
            ledger=ledger,
        )
        record = world.make_result_record(
            execution, result_id="RESULT-001", acquired_call=1
        )
        ledger.add(record)
        ledger.mark_model_visible("RESULT-001", call_index=2, message_index=4)
        return world, record

    def test_grounded_relation_is_admitted_without_referent_authority(self) -> None:
        world, record = self._record_fixture()
        output = fixture_delta(world, record.result_id, ("ANCHOR", "BRIDGE"))
        validation = validate_relational_delta(
            output,
            count_text=lambda value: len(value.split()),
            source_catalog=self.catalog,
            task_root=TASK,
            newly_externalized=(record,),
            current_source_versions=world.source_versions,
        )
        self.assertTrue(validation.valid, validation.issues)
        anchor = next(claim for claim in validation.claims if claim.source_id == "ANCHOR")
        self.assertIn("BRIDGE", anchor.referents)
        self.assertIn("CIRRUS", anchor.referents)
        self.assertEqual("ANCHOR", validation.provenance[0].slot_source_id)

    def test_absent_slot_mutation_and_derived_mode_are_rejected(self) -> None:
        world, record = self._record_fixture()
        output = fixture_delta(world, record.result_id, ("ANCHOR", "BRIDGE"))
        absent = output.replace(
            "SLOT_SOURCE: ANCHOR",
            "SLOT_SOURCE: CIRRUS",
            1,
        ).replace(
            f"SOURCE_VERSION: {world.sources['ANCHOR'].sha256}",
            f"SOURCE_VERSION: {world.sources['CIRRUS'].sha256}",
            1,
        )
        invalid = validate_relational_delta(
            absent,
            count_text=lambda value: len(value.split()),
            source_catalog=self.catalog,
            task_root=TASK,
            newly_externalized=(record,),
            current_source_versions=world.source_versions,
        )
        self.assertFalse(invalid.valid)
        self.assertIn("evidence_quote_not_unique_exact_line", invalid.issues)
        self.assertIn("externalized_source_unrepresented:ANCHOR", invalid.issues)

        derived = output.replace(
            "MODE: source_reported_relationship",
            "MODE: derived_cross_source",
            1,
        )
        derived_validation = validate_relational_delta(
            derived,
            count_text=lambda value: len(value.split()),
            source_catalog=self.catalog,
            task_root=TASK,
            newly_externalized=(record,),
            current_source_versions=world.source_versions,
        )
        self.assertIn("derived_claim_requires_derived_work_slot", derived_validation.issues)

    def test_host_derives_span_hash_and_register_drops_stale_source(self) -> None:
        world, first = self._record_fixture()
        first_validation = validate_relational_delta(
            fixture_delta(world, first.result_id, ("ANCHOR", "BRIDGE")),
            count_text=lambda value: len(value.split()),
            source_catalog=self.catalog,
            task_root=TASK,
            newly_externalized=(first,),
            current_source_versions=world.source_versions,
        )
        register = ProvenanceRegister().merge(
            first_validation,
            current_source_versions=world.source_versions,
            count_text=lambda value: len(value.split()),
        )
        self.assertTrue(all(len(claim.span_sha256) == 64 for claim in register.claims))
        self.assertIn("EVIDENCE_SHA256", register.render())
        self.assertNotIn("EVIDENCE_SHA256", register.render_for_maintenance(("ANCHOR",)))

        execution = world.execute(
            batch_action(("CIRRUS", "DUSK"), world),
            result_id="RESULT-002",
            ledger=ResultLedger(),
        )
        second = world.make_result_record(execution, result_id="RESULT-002", acquired_call=2)
        second_validation = validate_relational_delta(
            fixture_delta(world, second.result_id, ("CIRRUS", "DUSK")),
            count_text=lambda value: len(value.split()),
            source_catalog=self.catalog,
            task_root=TASK,
            newly_externalized=(second,),
            current_source_versions=world.source_versions,
        )
        changed = dict(world.source_versions)
        changed["ANCHOR"] = "f" * 64
        revised = register.merge(
            second_validation,
            current_source_versions=changed,
            count_text=lambda value: len(value.split()),
        )
        self.assertNotIn("ANCHOR", {claim.source_id for claim in revised.claims})
        self.assertIn("BRIDGE", {claim.source_id for claim in revised.claims})

    def test_preflight_uses_permitted_ingress_and_complete_loops(self) -> None:
        self.assertEqual(3052, self.preflight["base_actor_prompt_tokens"])
        self.assertEqual(20993, self.preflight["source_corpus_tokens"])
        ingress = self.preflight["permitted_ingress_geometry"]
        self.assertTrue(ingress["every_full_single_admissible"])
        self.assertTrue(ingress["every_full_pair_admissible"])
        pressure = self.preflight["prospective_pressure_opportunity"]
        self.assertEqual(6, pressure["step"])
        self.assertEqual(881, pressure["overflow_tokens"])
        self.assertEqual(["RESULT-001"], pressure["externalized_source_result_ids"])
        self.assertLessEqual(pressure["positive_relief_after_tokens"], runner.PROMPT_LIMIT)
        self.assertTrue(
            all(row["fits"] for row in self.preflight["provenance_maintenance_geometry"])
        )
        transition = self.preflight["first_treatment_transition"]
        self.assertEqual(["RESULT-001"], transition["externalized_result_ids"])
        self.assertTrue(transition["fits"])
        self.assertLessEqual(
            transition["actor_prompt_tokens_after_register"], runner.PROMPT_LIMIT
        )
        self.assertLessEqual(
            self.preflight["provenance_contract"]["maximum_register_fixture_tokens"],
            self.preflight["provenance_contract"]["register_token_budget"],
        )
        fixtures = {
            row["configuration_id"]: row
            for row in self.preflight["provider_free_complete_system_fixtures"]
        }
        self.assertEqual(
            {"W0_DIRECT_EXACT_WORK", "L1_PROVENANCE_LOCAL_RELATIONAL"},
            set(fixtures),
        )
        self.assertEqual(0, fixtures["W0_DIRECT_EXACT_WORK"]["semantic_register_claims"])
        self.assertEqual(10, fixtures["L1_PROVENANCE_LOCAL_RELATIONAL"]["semantic_register_claims"])
        self.assertEqual(
            fixtures["W0_DIRECT_EXACT_WORK"]["candidate_sha256"],
            fixtures["L1_PROVENANCE_LOCAL_RELATIONAL"]["candidate_sha256"],
        )
        for row in fixtures.values():
            self.assertFalse(row["first_check_passed"])
            self.assertTrue(row["check_stale_after_repair"])
            self.assertTrue(row["recheck_passed"])
            self.assertEqual("current", row["recheck_currency"])
            self.assertTrue(row["submitted"])
            self.assertEqual(
                "not_adjudicated",
                row["mechanical_final_evaluation"]["closure_readiness"],
            )

    def test_pressure_screen_is_common_and_allows_prior_task_work(self) -> None:
        contract = json.loads(
            (ROOT / "ASTER_PRESSURE_SCREEN_CONTRACT.json").read_text(encoding="utf-8")
        )
        request = json.loads(
            (ROOT / "ASTER_PRESSURE_SCREEN_AUTHORIZATION_REQUEST.json").read_text(encoding="utf-8")
        )
        self.assertEqual(runner.RUN_ID, contract["run_id"])
        self.assertEqual(runner.SCOPE, contract["scope"])
        self.assertEqual(runner.SEED, contract["seed"])
        self.assertEqual(runner.MAX_CALLS, contract["maximum_actor_calls"])
        self.assertTrue(contract["eligible_boundary"]["candidate_effects_before_pressure_allowed"])
        self.assertTrue(contract["eligible_boundary"]["checks_before_pressure_allowed"])
        self.assertFalse(contract["treatment_present"])
        self.assertFalse(contract["semantic_maintenance_present"])
        self.assertFalse(request["authorized"])
        source = Path(runner.__file__).read_text(encoding="utf-8")
        self.assertNotIn("relational_delta_messages", source)
        self.assertNotIn("validate_relational_delta", source)
        self.assertIn("positive_savings_first_fit_step", source)
        self.assertNotIn('terminal = "candidate_changed_before_pressure"', source)
        self.assertNotIn('terminal = "check_ran_before_pressure"', source)


if __name__ == "__main__":
    unittest.main()
