from __future__ import annotations

from pathlib import Path

from reactive_runtime.activation import activation_snapshot
from reactive_runtime.keystone_world import KeystoneWorld
from reactive_runtime.records import ResultLedger


ROOT = Path(__file__).resolve().parents[1]


def test_snapshot_serializes_the_thresholds_that_govern_admission(tmp_path: Path) -> None:
    world = KeystoneWorld(ROOT / "task_keystone", tmp_path / "world")
    ledger = ResultLedger()
    execution = world.execute(
        {
            "action": "read_source",
            "source_id": "MANDATE",
            "start_line": 1,
            "end_line": 20,
        },
        result_id="RESULT-001",
        ledger=ledger,
    )
    pending = world.make_result_record(
        execution, result_id="RESULT-001", acquired_call=1
    )
    snapshot = activation_snapshot(
        pending=pending,
        ledger=ledger,
        world=world,
        minimum_qualifying_sources=10,
        minimum_evidence_domains=10,
    ).as_dict()
    assert snapshot["minimum_qualifying_sources"] == 10
    assert snapshot["minimum_evidence_domains"] == 10
