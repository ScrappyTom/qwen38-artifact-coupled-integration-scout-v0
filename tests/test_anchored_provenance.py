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
from reactive_runtime.aster_world import AsterWorld
from reactive_runtime.records import ResultLedger
from tools.aster_stage0 import batch_action


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "task_aster"


class AnchoredProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        value = json.loads((TASK / "SOURCE_CATALOG.json").read_text(encoding="utf-8"))
        cls.catalog = {row["source_id"]: row for row in value["sources"]}

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.world = AsterWorld(TASK, Path(self.temporary.name))
        ledger = ResultLedger()
        execution = self.world.execute(
            batch_action(("ANCHOR", "BRIDGE"), self.world),
            result_id="RESULT-001",
            ledger=ledger,
        )
        self.record = self.world.make_result_record(
            execution, result_id="RESULT-001", acquired_call=1
        )

    def _claim(
        self,
        claim_id: str,
        source_id: str,
        anchor: str,
        statement: str,
        *,
        mode: str = "source_reported_fact",
        referents: str = "NONE",
    ) -> str:
        return "\n".join(
            (
                f"## CLAIM {claim_id}",
                f"SLOT_SOURCE: {source_id}",
                f"SOURCE_VERSION: {self.world.source_versions[source_id]}",
                "EVIDENCE_RESULT: RESULT-001",
                f"EVIDENCE_ANCHOR: {anchor}",
                f"MODE: {mode}",
                "ATTRIBUTION: owner_source_reported",
                f"REFERENTS: {referents}",
                "AUTHORITY: non_authoritative_derivative",
                f"STATEMENT: {statement}",
            )
        )

    def _admit(self, text: str):
        return admit_anchored_delta(
            text,
            count_text=lambda value: len(value.split()),
            source_catalog=self.catalog,
            task_root=TASK,
            newly_externalized=(self.record,),
            current_source_versions=self.world.source_versions,
        )

    def test_sentence_anchor_is_materialized_with_complete_line_context(self) -> None:
        anchor = "Current cross-region ledger replication lag is 1,800 milliseconds at p95."
        text = DELTA_PREFIX + "\n" + self._claim(
            "BRIDGE_LAG",
            "BRIDGE",
            anchor,
            "BRIDGE reports current cross-region ledger replication lag of 1,800 milliseconds at p95.",
        )
        admission = self._admit(text)
        self.assertEqual("full_admission", admission.disposition)
        claim = admission.admitted_claims[0]
        self.assertEqual(anchor, claim.anchor.anchor_text)
        self.assertIn("traffic-restoration block is 2.5 seconds", claim.anchor.context_text)
        self.assertEqual(64, len(claim.anchor.anchor_sha256))
        self.assertEqual(64, len(claim.anchor.context_sha256))
        source_bytes = (TASK / "sources" / "BRIDGE_LEDGER.md").read_bytes()
        self.assertEqual(
            anchor.encode("utf-8"),
            source_bytes[claim.anchor.anchor_start_byte : claim.anchor.anchor_end_byte],
        )

    def test_relationship_referents_do_not_mutate_referent_slots(self) -> None:
        text = DELTA_PREFIX + "\n" + self._claim(
            "ANCHOR_REL",
            "ANCHOR",
            "BRIDGE and CIRRUS supply ledger and retry evidence but cannot authorize restoration.",
            "ANCHOR reports that BRIDGE and CIRRUS supply evidence but cannot authorize restoration.",
            mode="source_reported_relationship",
            referents="BRIDGE,CIRRUS",
        )
        admission = self._admit(text)
        self.assertEqual("full_admission", admission.disposition)
        claim = admission.admitted_claims[0]
        self.assertEqual("ANCHOR", claim.source_id)
        self.assertEqual(("BRIDGE", "CIRRUS"), claim.referents)

    def test_valid_subset_merges_and_invalid_claim_is_charged_but_discarded(self) -> None:
        valid = self._claim(
            "ANCHOR_AUTH",
            "ANCHOR",
            "Only the payment risk owner may authorize customer-traffic restoration",
            "ANCHOR reports that only the payment risk owner may authorize customer-traffic restoration.",
        )
        invalid = self._claim(
            "BRIDGE_BAD",
            "BRIDGE",
            "This exact anchor does not exist.",
            "BRIDGE reports a nonexistent assertion.",
        )
        admission = self._admit(DELTA_PREFIX + "\n" + valid + "\n" + invalid)
        self.assertEqual("partial_admission", admission.disposition)
        self.assertEqual(("ANCHOR_AUTH",), tuple(c.claim_id for c in admission.admitted_claims))
        self.assertEqual("evidence_anchor_not_unique_in_result", admission.rejected_claims[0].code)

        before = AnchoredProvenanceRegister()
        transition = before.apply(
            admission,
            current_source_versions=self.world.source_versions,
            count_text=lambda value: len(value.split()),
        )
        self.assertTrue(transition.changed)
        self.assertEqual(("ANCHOR_AUTH",), transition.admitted_claim_ids)
        self.assertEqual(("BRIDGE_BAD",), transition.rejected_claim_ids)
        self.assertIn("INCOMPLETE SEMANTIC RESIDUE", transition.register.render())

    def test_zero_valid_and_global_reject_leave_register_unchanged(self) -> None:
        seed = self._admit(
            DELTA_PREFIX
            + "\n"
            + self._claim(
                "ANCHOR_SEED",
                "ANCHOR",
                "Only the payment risk owner may authorize customer-traffic restoration",
                "ANCHOR reports that only the payment risk owner may authorize customer-traffic restoration.",
            )
        )
        register = AnchoredProvenanceRegister().apply(
            seed,
            current_source_versions=self.world.source_versions,
            count_text=lambda value: len(value.split()),
        ).register
        zero = self._admit(
            DELTA_PREFIX
            + "\n"
            + self._claim(
                "BRIDGE_ZERO",
                "BRIDGE",
                "absent anchor",
                "BRIDGE reports an absent fact.",
            )
        )
        zero_transition = register.apply(
            zero,
            current_source_versions=self.world.source_versions,
            count_text=lambda value: len(value.split()),
        )
        self.assertEqual("zero_valid", zero_transition.disposition)
        self.assertFalse(zero_transition.changed)

        global_reject = self._admit("wrong prefix\n## CLAIM BAD\n")
        global_transition = register.apply(
            global_reject,
            current_source_versions=self.world.source_versions,
            count_text=lambda value: len(value.split()),
        )
        self.assertEqual("global_reject", global_transition.disposition)
        self.assertFalse(global_transition.changed)

    def test_duplicate_ids_are_rejected_atomically(self) -> None:
        first = self._claim(
            "DUPLICATE",
            "ANCHOR",
            "Only the payment risk owner may authorize customer-traffic restoration",
            "ANCHOR reports that only the payment risk owner may authorize customer-traffic restoration.",
        )
        second = self._claim(
            "DUPLICATE",
            "BRIDGE",
            "Current cross-region ledger replication lag is 1,800 milliseconds at p95.",
            "BRIDGE reports current cross-region ledger replication lag of 1,800 milliseconds at p95.",
        )
        admission = self._admit(DELTA_PREFIX + "\n" + first + "\n" + second)
        self.assertEqual("zero_valid", admission.disposition)
        self.assertEqual(2, len(admission.rejected_claims))
        self.assertTrue(all("claim_id_duplicate" in row.issues for row in admission.records))

    def test_context_cannot_supply_an_undeclared_statement_referent(self) -> None:
        text = DELTA_PREFIX + "\n" + self._claim(
            "BAD_FACT",
            "ANCHOR",
            "BRIDGE and CIRRUS supply ledger and retry evidence but cannot authorize restoration.",
            "ANCHOR reports that BRIDGE cannot authorize restoration.",
            mode="source_reported_fact",
            referents="NONE",
        )
        admission = self._admit(text)
        self.assertEqual("zero_valid", admission.disposition)
        self.assertIn("undeclared_source_reference", admission.records[0].issues)


if __name__ == "__main__":
    unittest.main()
