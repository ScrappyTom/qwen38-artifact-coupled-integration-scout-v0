from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reactive_runtime.actions import parse_action
from reactive_runtime.canonical import sha256_file
from reactive_runtime.configuration import bluehaven_actor_actions
from reactive_runtime.world import ArchitectureWorld
from tools import run_bluehaven_pressure_screen as runner


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "task_bluehaven"


class BluehavenStage0Tests(unittest.TestCase):
    def test_task_lock_and_ingress_geometry_are_exact(self) -> None:
        lock = json.loads((TASK / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
        self.assertEqual("bluehaven-water-restoration-package-v0", lock["task_id"])
        self.assertEqual(16, len(lock["source_custody"]))
        self.assertIn("SOURCE_CATALOG.json", {row["path"] for row in lock["files"]})
        for row in lock["files"]:
            self.assertEqual(row["sha256"], sha256_file(TASK / row["path"]))
        self.assertTrue(all(row["line_count"] == 70 for row in lock["source_custody"]))
        self.assertTrue(all(row["activation_min_lines"] == 55 for row in lock["source_custody"]))

    def test_world_contains_relation_level_traps_not_merely_keywords(self) -> None:
        catalog = json.loads((TASK / "SOURCE_CATALOG.json").read_text(encoding="utf-8"))
        sources = {
            row["source_id"]: (TASK / row["path"]).read_text(encoding="utf-8")
            for row in catalog["sources"]
        }
        self.assertIn("0.2 mg/L", sources["S02"])
        self.assertIn("38 percent", sources["S15"])
        self.assertIn("94 percent", sources["S03"])
        self.assertIn("six percent", sources["S03"])
        self.assertIn("15 ML/day", sources["S04"])
        self.assertIn("WQ-R7", sources["S15"])
        self.assertIn("seventeen-hour", sources["S06"])

    def test_task_contract_names_relation_classes_without_leaking_values(self) -> None:
        task = (TASK / "TASK.md").read_text(encoding="utf-8")
        self.assertIn("chemical threshold", task)
        self.assertIn("forecast probability", task)
        for exact_answer in (
            "0.2 mg/L",
            "38 percent",
            "94 percent",
            "15 ML/day",
            "seventeen-hour",
        ):
            self.assertNotIn(exact_answer, task)

    def test_activation_metadata_is_not_an_actor_hint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = ArchitectureWorld(TASK, Path(temporary))
            actor_catalog = json.loads(world.source_catalog_for_actor())
        for row in actor_catalog["sources"]:
            self.assertNotIn("activation_min_lines", row)
            self.assertNotIn("evidence_domain", row)

    def test_dynamic_decision_schema_uses_bluehaven_headings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            world = ArchitectureWorld(TASK, Path(temporary))
            accepted = parse_action(
                json.dumps(
                    {
                        "action": "upsert_decision_section",
                        "heading": world.decision_headings[1],
                        "body": "bounded exact work [S02]",
                    }
                ),
                ("upsert_decision_section",),
                decision_headings=world.decision_headings,
            )
            self.assertEqual(world.decision_headings[1], accepted["heading"])
            with self.assertRaises(ValueError):
                parse_action(
                    '{"action":"upsert_decision_section","heading":"Decision and trigger posture","body":"wrong task"}',
                    ("upsert_decision_section",),
                    decision_headings=world.decision_headings,
                )

    def test_complete_configuration_action_ownership_is_frozen(self) -> None:
        b1 = bluehaven_actor_actions("B1_BATCHED_COUPLED")
        w1 = bluehaven_actor_actions("W1_DIRECT_WORK")
        self.assertNotIn("replace_evidence_ledger", b1)
        self.assertIn("replace_evidence_ledger", w1)
        self.assertEqual(
            set(b1),
            set(w1) - {"replace_evidence_ledger"},
        )

    def test_relation_evaluator_rejects_prohibited_conversions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary)
            shutil.copy2(TASK / "candidate" / "EVIDENCE_INTEGRATION_LEDGER.md", candidate)
            decision = (
                (TASK / "candidate" / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md")
                .read_text(encoding="utf-8")
                + "\n0.2 hours; 38 percent humidity; six percent demand; "
                + "21 ML/day available; one WQ revision is permitted.\n"
            )
            (candidate / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md").write_text(
                decision, encoding="utf-8", newline=""
            )
            completed = subprocess.run(
                [sys.executable, str(TASK / "evaluator" / "evaluate.py"), str(candidate)],
                capture_output=True,
                text=True,
                check=True,
            )
            result = json.loads(completed.stdout)
        criteria = {row["criterion_id"]: row["status"] for row in result["criterion_results"]}
        for criterion in (
            "residual_unit_conversion",
            "probability_conversion",
            "coverage_conversion",
            "shared_capacity_sum",
            "revision_count_conversion",
        ):
            self.assertEqual("fail", criteria[criterion])
        self.assertEqual("not_ready", result["closure_readiness"])

    def test_mechanical_check_can_clear_without_self_authorizing_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary)
            source_citations = "".join(
                f"[S{ordinal:02d}]" for ordinal in (*range(1, 12), *range(13, 17))
            )
            ledger = ["# Evidence Integration Ledger", ""]
            for ordinal in range(1, 13):
                ledger.append(
                    f"R{ordinal:02d}: exact grounded disposition with unresolved "
                    f"falsifiers {source_citations}."
                )
            (candidate / "EVIDENCE_INTEGRATION_LEDGER.md").write_text(
                "\n".join(ledger) + "\n", encoding="utf-8", newline=""
            )
            evaluator = json.loads((TASK / "EVALUATOR.json").read_text(encoding="utf-8"))
            required_terms = " ".join(
                term for terms in evaluator["semantic_term_gates"].values() for term in terms
            )
            sections = [evaluator["decision_title"], ""]
            filler = (
                "The bounded operation assigns owners resources timing evidence "
                "contingencies qualifications dependencies and explicit falsifiers "
                "while preserving exact source relationships and candidate currency. "
            ) * 9
            for index, heading in enumerate(evaluator["decision_headings"]):
                sections.extend(
                    [
                        f"## {heading}",
                        "",
                        (required_terms + " " + source_citations + " " if index == 0 else "")
                        + filler,
                        "",
                    ]
                )
            (candidate / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md").write_text(
                "\n".join(sections).rstrip() + "\n", encoding="utf-8", newline=""
            )
            completed = subprocess.run(
                [sys.executable, str(TASK / "evaluator" / "evaluate.py"), str(candidate)],
                capture_output=True,
                text=True,
                check=True,
            )
            result = json.loads(completed.stdout)
        self.assertTrue(result["mechanical_precheck_passed"])
        self.assertTrue(result["passed"])
        self.assertEqual("not_adjudicated", result["closure_readiness"])
        self.assertEqual([], result["blocking_requirements"])
        self.assertTrue(result["external_readiness_adjudication_required"])
        self.assertFalse(result["independent_adjudication_supplied"])

    def test_stage0_exercises_complete_provider_free_system_loops(self) -> None:
        stage0 = json.loads((ROOT / "BLUEHAVEN_STAGE0_PREFLIGHT.json").read_text(encoding="utf-8"))
        self.assertFalse(stage0["authentic_activation_qualified"])
        self.assertFalse(stage0["gpu_authorized"])
        self.assertEqual(6, stage0["prospective_pressure_opportunity"]["step"])
        self.assertGreater(stage0["prospective_pressure_opportunity"]["overflow_tokens"], 0)
        self.assertTrue(stage0["prospective_pressure_opportunity"]["positive_relief_result_ids"])
        self.assertLessEqual(
            stage0["prospective_pressure_opportunity"]["positive_relief_after_tokens"],
            runner.PROMPT_LIMIT,
        )
        self.assertTrue(all(row["fits"] for row in stage0["batched_maintenance_prompt_geometry"]))
        self.assertEqual(
            2400, stage0["batched_maintenance_expression_budget"]["admission_tokens"]
        )
        self.assertEqual(
            2700,
            stage0["batched_maintenance_expression_budget"]["provider_completion_tokens"],
        )
        self.assertEqual("bluehaven_actor_action_v0", stage0["dynamic_action_schema_name"])
        fixtures = {
            row["configuration_id"]: row
            for row in stage0["provider_free_complete_system_fixtures"]
        }
        self.assertEqual({"B1_BATCHED_COUPLED", "W1_DIRECT_WORK"}, set(fixtures))
        for row in fixtures.values():
            self.assertTrue(row["candidate_changed"])
            self.assertFalse(row["first_check_passed"])
            self.assertEqual("not_ready", row["first_check_closure_readiness"])
            self.assertTrue(row["check_current_before_repair"])
            self.assertTrue(row["check_stale_after_repair"])
            self.assertTrue(row["recheck_current"])
            self.assertTrue(row["submitted"])

    def test_pressure_screen_contract_and_runner_match(self) -> None:
        contract = json.loads(
            (ROOT / "BLUEHAVEN_PRESSURE_SCREEN_CONTRACT.json").read_text(encoding="utf-8")
        )
        request = json.loads(
            (ROOT / "BLUEHAVEN_PRESSURE_SCREEN_AUTHORIZATION_REQUEST.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(runner.RUN_ID, contract["run_id"])
        self.assertEqual(runner.SCOPE, contract["scope"])
        self.assertEqual(runner.SEED, contract["seed"])
        self.assertEqual(runner.MAX_CALLS, contract["maximum_actor_calls"])
        self.assertEqual(runner.MAX_SERIALIZED, contract["maximum_serialized_tokens"])
        self.assertEqual(runner.MAX_WALL, contract["maximum_wall_seconds"])
        self.assertEqual(runner.PROMPT_LIMIT, contract["prompt_limit"])
        self.assertFalse(request["authorized"])
        self.assertEqual(runner.SCOPE, request["scope"])
        self.assertEqual(runner.MAX_CALLS, request["maximum_model_calls"])

    def test_live_screen_contains_no_treatment_or_semantic_maintenance(self) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")
        self.assertNotIn("batched_integration_messages", source)
        self.assertNotIn("apply_integration", source)
        self.assertNotIn("complete_custodied(provider_payload(maintenance", source)
        self.assertIn("positive_savings_first_fit_step", source)
        self.assertIn("counterfactual_positive_relief", source)


if __name__ == "__main__":
    unittest.main()
