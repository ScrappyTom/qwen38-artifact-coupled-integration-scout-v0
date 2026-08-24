from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_transfer_adjudication_protocol_is_bound_to_the_fresh_task() -> None:
    protocol = json.loads(
        (ROOT / "SEMANTIC_ADJUDICATION_PROTOCOL_TRANSFER.json").read_text(
            encoding="utf-8"
        )
    )
    evaluator = json.loads(
        (ROOT / "task" / "EVALUATOR.json").read_text(encoding="utf-8")
    )
    task_lock = json.loads(
        (ROOT / "task" / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8")
    )

    assert protocol["task_id"] == evaluator["task_id"] == task_lock["task_id"]
    assert protocol["task_source_lock_sha256"] == sha256(
        (ROOT / "task" / "TASK_SOURCE_LOCK.json").read_bytes()
    ).hexdigest()
    assert protocol["mechanical_evaluator_sha256"] == sha256(
        (ROOT / "task" / "evaluator" / "evaluate.py").read_bytes()
    ).hexdigest()
    assert protocol["world_spec_sha256"] == sha256(
        (ROOT / "task" / "WORLD_SPEC.json").read_bytes()
    ).hexdigest()
    assert [row["id"] for row in protocol["criteria"]] == [
        f"R{index:02d}" for index in range(1, 13)
    ]
    assert evaluator["required_ledger_requirements"] == [
        row["id"] for row in protocol["criteria"]
    ]
    assert protocol["readiness_values"] == ["ready", "not_ready"]
    readiness = protocol["readiness_rule"]
    for required_term in (
        "mechanical precheck",
        "all R01-R12 met",
        "no unsupported source claim",
        "no forbidden shortcut",
        "no unresolved blocking requirement",
        "current candidate-bound final check",
    ):
        assert required_term in readiness
    assert "Submission behavior never changes this rule" in readiness
    assert "Exact composite SHA-256" in protocol["candidate_binding"]
