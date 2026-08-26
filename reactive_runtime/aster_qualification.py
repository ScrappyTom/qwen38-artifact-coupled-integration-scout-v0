from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from reactive_runtime.aster_boundary import verify_aster_pressure_handoff
from reactive_runtime.records import ResultLedger, ResultRecord
from reactive_runtime.relational_delta import (
    ProvenanceRegister,
    relational_delta_messages,
)


@dataclass(frozen=True)
class AsterRelationalCase:
    case_id: str
    seed: int
    input_result_ids: tuple[str, ...]
    input_source_ids: tuple[str, ...]
    source_versions: dict[str, str]
    records: tuple[ResultRecord, ...]
    messages: list[dict[str, str]]


def build_aster_relational_case(root: Path) -> AsterRelationalCase:
    root = root.resolve()
    handoff = verify_aster_pressure_handoff(root)
    run_root = root / str(handoff["run_root"])
    ledger_value = json.loads(
        (run_root / "RESULT_LEDGER.json").read_text(encoding="utf-8")
    )
    ledger = ResultLedger.from_dict(ledger_value)
    selected = tuple(str(value) for value in handoff["externalized_source_result_ids"])
    if selected != ("RESULT-001",):
        raise RuntimeError(
            "qualification requires the first actual source externalization"
        )
    records = tuple(ledger.get(result_id) for result_id in selected)
    if any(not record.previously_visible for record in records):
        raise RuntimeError("qualification input did not cross an actor boundary")
    source_ids: list[str] = []
    for record in records:
        if record.result_kind != "source_observation":
            raise RuntimeError("qualification input is not a source observation")
        values = record.metadata.get("source_ids")
        if not isinstance(values, list):
            raise RuntimeError("qualification input lacks source identities")
        source_ids.extend(str(value) for value in values)
    if tuple(source_ids) != ("ANCHOR", "BRIDGE"):
        raise RuntimeError("qualification sources differ from the sealed boundary")

    catalog = json.loads(
        (root / "task_aster" / "SOURCE_CATALOG.json").read_text(encoding="utf-8")
    )
    versions = {str(row["source_id"]): str(row["sha256"]) for row in catalog["sources"]}
    model_lock = json.loads(
        (root / "ASTER_MODEL_PROFILE_LOCK.json").read_text(encoding="utf-8")
    )
    seed = model_lock.get("expression_seed")
    if not isinstance(seed, int):
        raise RuntimeError("expression seed is not frozen")
    messages = relational_delta_messages(
        task_text=(root / "task_aster" / "TASK.md").read_text(encoding="utf-8"),
        register=ProvenanceRegister(),
        newly_externalized=records,
        source_versions=versions,
    )
    return AsterRelationalCase(
        case_id="Q1_FIRST_ACTUAL_SOURCE_EXTERNALIZATION",
        seed=seed,
        input_result_ids=selected,
        input_source_ids=tuple(source_ids),
        source_versions=versions,
        records=records,
        messages=messages,
    )
