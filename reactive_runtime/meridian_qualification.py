from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from reactive_runtime.meridian_boundary import verify_meridian_pressure_handoff
from reactive_runtime.records import ResultLedger
from reactive_runtime.source_delta import SourceEvidenceRegister, source_delta_messages


@dataclass(frozen=True)
class MeridianDeltaCase:
    case_id: str
    seed: int
    input_result_ids: tuple[str, ...]
    allowed_source_versions: dict[str, str]
    messages: list[dict[str, str]]


def build_meridian_delta_case(root: Path) -> MeridianDeltaCase:
    root = root.resolve()
    handoff = verify_meridian_pressure_handoff(root)
    run_root = root / str(handoff["run_root"])
    ledger_value = json.loads((run_root / "RESULT_LEDGER.json").read_text(encoding="utf-8"))
    ledger = ResultLedger.from_dict(ledger_value)
    selected = tuple(str(value) for value in handoff["positive_relief_result_ids"])
    if selected != ("RESULT-001",):
        raise RuntimeError("qualification requires the exact first live externalization")
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
    if tuple(source_ids) != ("AXIOM", "BRAMBLE"):
        raise RuntimeError("qualification sources differ from the sealed boundary")

    catalog = json.loads(
        (root / "task_meridian" / "SOURCE_CATALOG.json").read_text(encoding="utf-8")
    )
    versions = {str(row["source_id"]): str(row["sha256"]) for row in catalog["sources"]}
    allowed = {source_id: versions[source_id] for source_id in source_ids}
    model_lock = json.loads(
        (root / "MERIDIAN_MODEL_PROFILE_LOCK.json").read_text(encoding="utf-8")
    )
    seeds = model_lock.get("expression_seeds")
    if not isinstance(seeds, list) or not seeds:
        raise RuntimeError("expression seed is not frozen")
    register = SourceEvidenceRegister.parse(
        (
            run_root
            / "trajectory"
            / "candidate_versions"
            / "version-000"
            / "EVIDENCE_INTEGRATION_LEDGER.md"
        ).read_text(encoding="utf-8")
    )
    messages = source_delta_messages(
        task_text=(root / "task_meridian" / "TASK.md").read_text(encoding="utf-8"),
        register=register,
        newly_externalized=records,
        source_versions=versions,
    )
    return MeridianDeltaCase(
        case_id="Q1_FIRST_ACTUAL_EXTERNALIZATION",
        seed=int(seeds[0]),
        input_result_ids=selected,
        allowed_source_versions=allowed,
        messages=messages,
    )
