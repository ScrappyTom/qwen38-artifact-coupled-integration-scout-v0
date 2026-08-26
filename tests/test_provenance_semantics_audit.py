from __future__ import annotations

import json
import unittest

from reactive_runtime.provenance_claims import (
    DERIVED_CROSS_SOURCE,
    DERIVED_WORK_SLOT,
    SOURCE_REPORTED_RELATIONSHIP,
    SOURCE_SLOT,
)
from tools.audit_provenance_semantics import AUDIT_PATH, ROOT, build_audit


class ProvenanceSemanticsAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = build_audit(ROOT)
        cls.committed = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        cls.rows = {row["case_id"]: row for row in cls.audit["case_rows"]}

    def test_committed_audit_reproduces_exactly(self) -> None:
        self.assertEqual(self.committed, self.audit)
        self.assertTrue(self.audit["passed"], self.audit["failures"])
        self.assertEqual(10, self.audit["case_count"])
        self.assertEqual(0, self.audit["model_calls"])
        self.assertFalse(self.audit["next_live_operation_authorized"])

    def test_e61_relation_is_allowed_without_absent_slot_mutation(self) -> None:
        row = self.rows["P02_E61_BRAMBLE_RELATIONSHIP_OBJECTS"]
        self.assertTrue(row["mechanical_valid"])
        self.assertEqual(SOURCE_SLOT, row["record_kind"])
        self.assertEqual(SOURCE_REPORTED_RELATIONSHIP, row["assertion_mode"])
        self.assertEqual("BRAMBLE", row["slot_source_id"])
        self.assertEqual(["BRAMBLE"], row["evidence_source_ids"])
        self.assertEqual(["DRIFT", "EMBER", "HEATH", "NORTH"], row["referent_source_ids"])
        self.assertTrue(row["historical_bindings"][0]["passed"])

    def test_absent_slot_and_bluehaven_completion_remain_blocked(self) -> None:
        absent = self.rows["P03_MERIDIAN_ABSENT_SOURCE_SLOT_MUTATION"]
        bluehaven = self.rows["P09_BLUEHAVEN_UNSEEN_S07_SLOT"]
        self.assertFalse(absent["mechanical_valid"])
        self.assertIn("slot_source_not_admitted", absent["mechanical_issues"])
        self.assertFalse(bluehaven["mechanical_valid"])
        self.assertIn("slot_source_not_admitted", bluehaven["mechanical_issues"])
        self.assertTrue(bluehaven["historical_bindings"][0]["passed"])

    def test_joint_claim_uses_derived_work_not_a_source_slot(self) -> None:
        derived = self.rows["P06_MERIDIAN_DERIVED_MULTI_SOURCE_WORK"]
        wrong_slot = self.rows["P07_MERIDIAN_DERIVED_CLAIM_IN_SOURCE_SLOT"]
        self.assertTrue(derived["mechanical_valid"])
        self.assertEqual(DERIVED_WORK_SLOT, derived["record_kind"])
        self.assertEqual(DERIVED_CROSS_SOURCE, derived["assertion_mode"])
        self.assertFalse(wrong_slot["mechanical_valid"])
        self.assertIn(
            "derived_claim_requires_derived_work_slot",
            wrong_slot["mechanical_issues"],
        )

    def test_currentness_is_separate_from_historical_validity(self) -> None:
        stale = self.rows["P08_MERIDIAN_PRIOR_VERSION_RETAINED_STALE"]
        self.assertTrue(stale["mechanical_valid"])
        self.assertEqual("stale", stale["currentness"])
        self.assertFalse(stale["active"])

    def test_provenance_transport_never_establishes_semantic_truth(self) -> None:
        expected = [
            "P05_MERIDIAN_RELATION_PREDICATE_REVERSAL",
            "P10_CEDAR_PROVENANCE_VALID_SEMANTIC_REVERSAL",
        ]
        self.assertEqual(expected, self.audit["mechanical_pass_semantic_fail_cases"])
        for case_id in expected:
            self.assertTrue(self.rows[case_id]["mechanical_valid"])
            self.assertTrue(self.rows[case_id]["semantic_review_required"])


if __name__ == "__main__":
    unittest.main()
