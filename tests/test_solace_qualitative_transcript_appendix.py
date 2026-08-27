"""Structural checks for the Solace qualitative transcript supplements."""

from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUN = REPO / "runs" / "2026-08-26-solace-anchored-provenance-interaction-measured-v0"
LEDGER_PATH = REPO / "SOLACE_ANCHORED_INTERACTION_CALL_LEDGER.json"
APPENDIX_PATH = REPO / "SOLACE_ANCHORED_INTERACTION_QUALITATIVE_TRANSCRIPT_APPENDIX.md"
LINEAGE_PATH = REPO / "SOLACE_ANCHORED_INTERACTION_REQUIREMENT_LINEAGE.md"


class SolaceQualitativeTranscriptAppendixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        cls.appendix = APPENDIX_PATH.read_text(encoding="utf-8")
        cls.lineage = LINEAGE_PATH.read_text(encoding="utf-8")

    def test_schema_and_provider_call_counts(self) -> None:
        self.assertEqual(self.ledger["schema"], "solace-anchored-interaction-call-ledger-v1")
        self.assertEqual(len(self.ledger["calls"]), 34)
        counts = Counter((item["cell"], item["role"]) for item in self.ledger["calls"])
        self.assertEqual(counts[("W0_DIRECT_EXACT_WORK_FRESH", "actor")], 18)
        self.assertEqual(counts[("L1_FAULT_TOLERANT_ANCHORED_PROVENANCE", "actor")], 9)
        self.assertEqual(counts[("L1_FAULT_TOLERANT_ANCHORED_PROVENANCE", "maintenance")], 7)

    def test_ids_and_turn_coverage(self) -> None:
        ids = [item["call_id"] for item in self.ledger["calls"]]
        expected = [f"W0-A{n:02d}" for n in range(1, 19)]
        expected += [f"L1-A{n:02d}" for n in range(1, 10)]
        expected += [f"L1-M{n:02d}" for n in range(1, 8)]
        self.assertEqual(ids, expected)
        for call_id in ids:
            self.assertIn(call_id, self.appendix)

    def test_evidence_paths_exist_and_cover_prompt_message_output_result(self) -> None:
        for item in self.ledger["calls"]:
            paths = item["evidence_paths"]
            self.assertGreaterEqual(len(paths), 4, item["call_id"])
            suffixes = {Path(path).name for path in paths}
            self.assertTrue({"messages.json", "rendered_prompt.txt", "assistant_content.txt", "RESULT.json"} <= suffixes)
            for relative_path in paths:
                self.assertTrue((REPO / relative_path).is_file(), relative_path)

    def test_classification_and_interpretation_labels(self) -> None:
        permitted = {
            "mechanical_source_read",
            "admitted_ledger_mutation",
            "mechanical_exact_reopen",
            "unadmitted_truncated_decision_attempt",
            "unadmitted_truncated_decision_retry",
            "admitted_incremental_decision_mutation",
            "admitted_global_decision_consolidation",
            "register_full_admission",
            "register_partial_admission",
            "register_no_change_rejection",
        }
        labels = {item["classification"] for item in self.ledger["calls"]}
        self.assertTrue(labels <= permitted)
        self.assertIn("unadmitted_truncated_decision_attempt", labels)
        self.assertIn("unadmitted_truncated_decision_retry", labels)
        for item in self.ledger["calls"]:
            self.assertIn("semantic_judgment", item)
            inference = item["demand_inference"]
            self.assertIn(inference["confidence"], {"low", "medium", "high"})
            self.assertTrue(inference["alternatives"], item["call_id"])

    def test_exact_lifecycle_order_and_actor_visibility(self) -> None:
        expected_l1_order = [
            "R1", "M1", "A1", "R2", "M2", "R3", "M3", "A2", "R4", "M4", "R5", "M5",
            "A3", "R6", "M6", "A4", "A5", "A6", "A7", "R7", "M7", "A8", "A9",
            "terminal_relief_failure",
        ]
        lifecycle = self.ledger["lifecycle_order"]["L1_FAULT_TOLERANT_ANCHORED_PROVENANCE"]
        self.assertEqual(lifecycle, expected_l1_order)
        self.assertTrue((REPO / self.ledger["lifecycle_order"]["source"]).is_file())
        visibility = self.ledger["visibility_sequence"]
        l1 = visibility["L1_FAULT_TOLERANT_ANCHORED_PROVENANCE"]
        self.assertEqual(l1["A01"], {"exact_result_ids": ["RESULT-002", "RESULT-003", "RESULT-004", "RESULT-005", "RESULT-006"], "receipt_result_ids": ["RESULT-001"], "register_claims": 6, "candidate_version": "version-000"})
        self.assertEqual(l1["A02"]["exact_result_ids"], ["RESULT-004", "RESULT-005", "RESULT-006", "RESULT-007"])
        self.assertEqual(l1["A02"]["register_claims"], 13)
        self.assertEqual(l1["A03"]["exact_result_ids"], ["RESULT-006", "RESULT-007"])
        self.assertEqual(l1["A03"]["register_claims"], 20)
        for call_id in ["A04", "A05", "A06", "A07"]:
            self.assertEqual(l1[call_id]["exact_result_ids"], ["RESULT-007"])
            self.assertEqual(l1[call_id]["register_claims"], 20)
        for call_id in ["A08", "A09"]:
            self.assertEqual(l1[call_id]["exact_result_ids"], [])
            self.assertEqual(l1[call_id]["receipt_result_ids"], [f"RESULT-{number:03d}" for number in range(1, 8)])
        w0 = visibility["W0_DIRECT_EXACT_WORK_FRESH"]
        expected_w0_exact = [[2, 3, 4, 5, 6], [3, 4, 5, 6, 7], [4, 5, 6, 7], [1, 5, 6, 7], [1, 2, 6, 7], [1, 2, 3, 7], [2, 3, 4], [3, 4, 5], [4, 5, 6], [5, 6, 7], [1, 6, 7], [1, 2, 7], [1, 2, 3], [2, 3, 4], [4, 5], [5, 6], [6, 7], [7]]
        for index, numbers in enumerate(expected_w0_exact, start=1):
            self.assertEqual(w0[f"A{index:02d}"]["exact_result_ids"], [f"RESULT-{number:03d}" for number in numbers])

        calls = {item["call_id"]: item for item in self.ledger["calls"]}
        self.assertIn("six-claim register", calls["L1-A01"]["pre_visibility"])
        self.assertIn("thirteen-claim register", calls["L1-A02"]["pre_visibility"])
        expected_maintenance_candidates = {
            "L1-M01": "v000",
            "L1-M02": "v000",
            "L1-M03": "v001",
            "L1-M04": "v001",
            "L1-M05": "v001",
            "L1-M06": "v002",
            "L1-M07": "v006",
        }
        for call_id, version in expected_maintenance_candidates.items():
            self.assertIn(f"candidate {version}", calls[call_id]["pre_visibility"])

    def test_direct_adjudication_is_eight_met_four_partial_with_q10_reconciled(self) -> None:
        adjudication = json.loads((REPO / "SOLACE_ANCHORED_INTERACTION_SEMANTIC_ADJUDICATION.json").read_text(encoding="utf-8"))
        l1 = next(record for record in adjudication["records"] if record["configuration_id"] == "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE")
        self.assertEqual(l1["requirement_summary"], {"met": 8, "partial": 4, "not_met": 0})
        q_statuses = {record["criterion_id"]: record["status"] for record in l1["criterion_dispositions"] if record["criterion_id"].startswith("Q")}
        self.assertEqual({q for q, status in q_statuses.items() if status == "partial"}, {"Q02", "Q03", "Q04", "Q09"})
        self.assertEqual(q_statuses["Q10"], "met")
        self.assertIn("surface-form false negative", self.lineage)

    def test_cross_file_run_register_candidate_and_requirement_coverage(self) -> None:
        # The supplements must bind to the sealed traces, final register, candidate versions,
        # task/evaluator, and the original result/adjudication without changing them.
        for path in [
            RUN / "cells" / "W0_DIRECT_EXACT_WORK_FRESH" / "ACTOR_TRACE.json",
            RUN / "cells" / "W0_DIRECT_EXACT_WORK_FRESH" / "MAINTENANCE_TRACE.json",
            RUN / "cells" / "W0_DIRECT_EXACT_WORK_FRESH" / "LIFECYCLE.json",
            RUN / "cells" / "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE" / "ACTOR_TRACE.json",
            RUN / "cells" / "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE" / "MAINTENANCE_TRACE.json",
            RUN / "cells" / "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE" / "LIFECYCLE.json",
            RUN / "cells" / "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE" / "CURRENT_REGISTER.json",
            REPO / "task_solace" / "TASK.md",
            REPO / "task_solace" / "EVALUATOR.json",
            REPO / "SOLACE_ANCHORED_INTERACTION_RESULT.md",
            REPO / "SOLACE_ANCHORED_INTERACTION_SEMANTIC_ADJUDICATION.json",
        ]:
            self.assertTrue(path.is_file(), path)
        w0_versions = RUN / "cells" / "W0_DIRECT_EXACT_WORK_FRESH" / "trajectory" / "candidate_versions"
        l1_versions = RUN / "cells" / "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE" / "trajectory" / "candidate_versions"
        self.assertEqual(sorted(path.name for path in w0_versions.iterdir() if path.is_dir()), ["version-000", "version-001"])
        self.assertEqual(sorted(path.name for path in l1_versions.iterdir() if path.is_dir()), [f"version-{number:03d}" for number in range(9)])
        for version_root in [w0_versions, l1_versions]:
            for version in version_root.iterdir():
                if version.is_dir():
                    self.assertTrue((version / "CANDIDATE_MANIFEST.json").is_file())
        for q_number in range(1, 13):
            self.assertIn(f"Q{q_number:02d}", self.lineage)
        self.assertIn("unadmitted", self.appendix.lower())
        self.assertIn("not ready", self.appendix.lower())

        result_text = (REPO / "SOLACE_ANCHORED_INTERACTION_RESULT.md").read_text(encoding="utf-8")
        readme_text = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("never constructed the required decision", result_text)
        self.assertNotIn("never\nconstructed the decision", readme_text)
        self.assertIn("two substantial global", result_text)
        self.assertIn("action granularity", result_text)


if __name__ == "__main__":
    unittest.main()
