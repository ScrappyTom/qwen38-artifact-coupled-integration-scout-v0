from __future__ import annotations

import unittest
from pathlib import Path

from tools.audit_meridian_source_relation_topology import audit


ROOT = Path(__file__).resolve().parents[1]


class MeridianSourceRelationTopologyAuditTests(unittest.TestCase):
    def test_all_sources_have_named_cross_source_relations(self) -> None:
        result = audit(ROOT, write_output=False)
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual(16, result["source_count"])
        self.assertEqual(16, result["files_with_cross_source_references"])
        self.assertEqual(66, result["directed_cross_source_reference_edges"])

    def test_first_rejection_exactly_matches_bramble_relationship_objects(self) -> None:
        result = audit(ROOT, write_output=False)
        expected = ["DRIFT", "EMBER", "HEATH", "NORTH"]
        self.assertEqual(expected, result["first_expression_exact_relationship_object_ids"])
        self.assertEqual(expected, result["first_expression_rejected_ids"])
        self.assertTrue(result["sets_match"])

    def test_audit_does_not_regrade_or_authorize(self) -> None:
        result = audit(ROOT, write_output=False)
        self.assertIn("post-run offline topology audit", result["claim_limit"])
        self.assertIn("structurally incompatible", result["mechanical_finding"])


if __name__ == "__main__":
    unittest.main()
