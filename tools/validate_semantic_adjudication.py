from __future__ import annotations

import json
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "SEMANTIC_ADJUDICATION.json"
PROTOCOL = ROOT / "SEMANTIC_ADJUDICATION_PROTOCOL.json"
RUN_ROOT = ROOT / "runs" / "2026-08-24-artifact-coupled-interaction-measured-v0"
ALLOWED = {"met", "partial", "not_met", "ambiguous"}
EXPECTED_MAPPING = {
    "D0_DETACHED": "C-17426844",
    "A1_COUPLED": "C-45ED2D1E",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def validate() -> dict[str, Any]:
    failures: list[str] = []
    record = load(RECORD)
    protocol = load(PROTOCOL)
    aggregate = load(RUN_ROOT / "AGGREGATE_RESULT.json")

    if record.get("run_id") != aggregate.get("run_id"):
        failures.append("run_id")
    if record.get("freeze_commit") != aggregate.get("freeze_commit"):
        failures.append("freeze_commit")
    if record.get("evaluator_id") != protocol.get("evaluator_id"):
        failures.append("evaluator_id")
    if record.get("protocol", {}).get("sha256") != digest(PROTOCOL):
        failures.append("protocol_hash")

    for name, binding in record.get("bindings", {}).items():
        path = ROOT / binding.get("path", "missing")
        if not path.is_file():
            failures.append(f"binding:{name}:missing")
            continue
        if path.stat().st_size != binding.get("bytes"):
            failures.append(f"binding:{name}:bytes")
        if digest(path) != binding.get("sha256"):
            failures.append(f"binding:{name}:sha256")

    mapping = {
        row.get("configuration_id"): row.get("candidate_label")
        for row in record.get("condition_mapping", [])
        if isinstance(row, dict)
    }
    if mapping != EXPECTED_MAPPING:
        failures.append("condition_mapping")

    candidate_rows = record.get("candidates", [])
    labels = [row.get("candidate_label") for row in candidate_rows if isinstance(row, dict)]
    if set(labels) != set(EXPECTED_MAPPING.values()) or len(labels) != 2:
        failures.append("candidate_labels")

    aggregate_cells = {
        row.get("configuration_id"): row
        for row in aggregate.get("cells", [])
        if isinstance(row, dict)
    }
    derived: list[dict[str, Any]] = []
    expected_criteria = protocol.get("criterion_order", [])
    for row in candidate_rows:
        label = row.get("candidate_label")
        configuration_id = next(
            (key for key, value in EXPECTED_MAPPING.items() if value == label), None
        )
        if configuration_id is None:
            failures.append(f"candidate:{label}:mapping")
            continue
        cell = aggregate_cells.get(configuration_id, {})
        if row.get("candidate_sha256") != cell.get("candidate_sha256"):
            failures.append(f"candidate:{label}:candidate_sha256")

        for name, binding in row.get("files", {}).items():
            path = ROOT / binding.get("path", "missing")
            if not path.is_file():
                failures.append(f"candidate:{label}:{name}:missing")
                continue
            if path.stat().st_size != binding.get("bytes"):
                failures.append(f"candidate:{label}:{name}:bytes")
            if digest(path) != binding.get("sha256"):
                failures.append(f"candidate:{label}:{name}:sha256")

        mechanical = row.get("mechanical_disposition", {})
        mechanical_record = load(ROOT / row["files"]["mechanical_evaluation"]["path"])
        projection = mechanical_record.get("projection", {})
        if mechanical.get("passed") != projection.get("passed"):
            failures.append(f"candidate:{label}:mechanical_pass")
        word_text = " ".join(projection.get("blocking_requirements", []))
        if str(mechanical.get("decision_word_count")) not in word_text:
            failures.append(f"candidate:{label}:word_count")

        dispositions = row.get("criterion_dispositions", [])
        ids = [item.get("criterion_id") for item in dispositions]
        if ids != expected_criteria:
            failures.append(f"candidate:{label}:criterion_order")
        statuses = Counter(item.get("disposition") for item in dispositions)
        if not set(statuses).issubset(ALLOWED):
            failures.append(f"candidate:{label}:criterion_status")
        expected_score = {
            "met": statuses.get("met", 0),
            "partial": statuses.get("partial", 0),
            "not_met": statuses.get("not_met", 0),
            "ambiguous": statuses.get("ambiguous", 0),
            "total": len(dispositions),
        }
        if row.get("score") != expected_score:
            failures.append(f"candidate:{label}:score")
        ready = (
            mechanical.get("passed") is True
            and statuses == Counter({"met": len(expected_criteria)})
            and not row.get("blocking_requirements")
        )
        expected_readiness = "ready" if ready else "not_ready"
        if row.get("closure_readiness") != expected_readiness:
            failures.append(f"candidate:{label}:readiness")
        if expected_readiness == "not_ready" and not row.get("blocking_requirements"):
            failures.append(f"candidate:{label}:blockers")
        derived.append(
            {
                "candidate_label": label,
                "configuration_id": configuration_id,
                "score": expected_score,
                "closure_readiness": expected_readiness,
            }
        )

    comparison = record.get("comparative_disposition", {})
    for configuration_id, label in EXPECTED_MAPPING.items():
        candidate = next((row for row in candidate_rows if row.get("candidate_label") == label), {})
        comparison_row = comparison.get(configuration_id, {})
        if comparison_row.get("closure_readiness") != candidate.get("closure_readiness"):
            failures.append(f"comparison:{configuration_id}:readiness")
        if comparison_row.get("quality_class") != candidate.get("quality_class"):
            failures.append(f"comparison:{configuration_id}:quality")
        if comparison_row.get("useful_completion") is not False:
            failures.append(f"comparison:{configuration_id}:useful_completion")

    return {
        "schema_version": "artifact-coupled-semantic-adjudication-validation-v0",
        "record_sha256": digest(RECORD),
        "protocol_sha256": digest(PROTOCOL),
        "run_id": record.get("run_id"),
        "derived_candidates": derived,
        "passed": not failures,
        "failures": failures,
    }


def main() -> int:
    result = validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
