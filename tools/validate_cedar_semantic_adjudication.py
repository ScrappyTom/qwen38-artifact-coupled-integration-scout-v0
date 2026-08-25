from __future__ import annotations

import json
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "CEDAR_SEMANTIC_ADJUDICATION.json"
PROTOCOL = ROOT / "SEMANTIC_ADJUDICATION_PROTOCOL_TRANSFER.json"
RUN_ROOT = ROOT / "runs" / "2026-08-25-cedar-artifact-coupling-transfer-measured-v0"
ALLOWED_DISPOSITIONS = {"met", "partial", "not_met"}
ALLOWED_QUALITY = {"complete", "strong_partial", "weak_partial", "failed"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
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
        path = ROOT / str(binding.get("path", "missing"))
        if not path.is_file():
            failures.append(f"binding:{name}:missing")
            continue
        if path.stat().st_size != binding.get("bytes"):
            failures.append(f"binding:{name}:bytes")
        if digest(path) != binding.get("sha256"):
            failures.append(f"binding:{name}:sha256")

    aggregate_cells = {
        row.get("configuration_id"): row
        for row in aggregate.get("cells", [])
        if isinstance(row, dict)
    }
    expected_mapping = {
        configuration_id: f"C-{str(cell.get('candidate_sha256', ''))[:8].upper()}"
        for configuration_id, cell in aggregate_cells.items()
    }
    observed_mapping = {
        row.get("configuration_id"): row.get("candidate_label")
        for row in record.get("condition_mapping", [])
        if isinstance(row, dict)
    }
    if observed_mapping != expected_mapping:
        failures.append("condition_mapping")

    expected_criteria = [row["id"] for row in protocol.get("criteria", [])]
    derived: list[dict[str, Any]] = []
    candidates = record.get("candidates", [])
    if not isinstance(candidates, list) or len(candidates) != len(expected_mapping):
        failures.append("candidates")
        candidates = []
    for candidate in candidates:
        label = candidate.get("candidate_label")
        configuration_id = next(
            (key for key, value in expected_mapping.items() if value == label), None
        )
        if configuration_id is None:
            failures.append(f"candidate:{label}:mapping")
            continue
        cell = aggregate_cells[configuration_id]
        if candidate.get("candidate_sha256") != cell.get("candidate_sha256"):
            failures.append(f"candidate:{label}:candidate_sha256")
        for name, binding in candidate.get("files", {}).items():
            path = ROOT / str(binding.get("path", "missing"))
            if not path.is_file():
                failures.append(f"candidate:{label}:{name}:missing")
                continue
            if path.stat().st_size != binding.get("bytes"):
                failures.append(f"candidate:{label}:{name}:bytes")
            if digest(path) != binding.get("sha256"):
                failures.append(f"candidate:{label}:{name}:sha256")

        mechanical_path = ROOT / candidate["files"]["mechanical_evaluation"]["path"]
        projection = load(mechanical_path).get("projection", {})
        mechanical = candidate.get("mechanical_disposition", {})
        if mechanical.get("passed") != projection.get("passed"):
            failures.append(f"candidate:{label}:mechanical_pass")
        if mechanical.get("closure_readiness") != projection.get("closure_readiness"):
            failures.append(f"candidate:{label}:mechanical_readiness")
        if mechanical.get("blocking_requirements") != projection.get("blocking_requirements"):
            failures.append(f"candidate:{label}:mechanical_blockers")

        dispositions = candidate.get("criterion_dispositions", [])
        ids = [row.get("criterion_id") for row in dispositions]
        if ids != expected_criteria:
            failures.append(f"candidate:{label}:criterion_order")
        statuses = Counter(row.get("disposition") for row in dispositions)
        if not set(statuses).issubset(ALLOWED_DISPOSITIONS):
            failures.append(f"candidate:{label}:criterion_status")
        expected_score = {
            "met": statuses.get("met", 0),
            "partial": statuses.get("partial", 0),
            "not_met": statuses.get("not_met", 0),
            "total": len(dispositions),
        }
        if candidate.get("score") != expected_score:
            failures.append(f"candidate:{label}:score")
        if candidate.get("quality_class") not in ALLOWED_QUALITY:
            failures.append(f"candidate:{label}:quality")
        ready = (
            mechanical.get("passed") is True
            and statuses == Counter({"met": len(expected_criteria)})
            and not candidate.get("unsupported_or_contradictory_claims")
            and not candidate.get("blocking_requirements")
            and candidate.get("final_effect_current_or_independently_reconciled") is True
        )
        expected_readiness = "ready" if ready else "not_ready"
        if candidate.get("closure_readiness") != expected_readiness:
            failures.append(f"candidate:{label}:closure_readiness")
        if candidate.get("useful_completion") is not (
            expected_readiness == "ready"
        ):
            failures.append(f"candidate:{label}:useful_completion")
        derived.append(
            {
                "candidate_label": label,
                "configuration_id": configuration_id,
                "score": expected_score,
                "quality_class": candidate.get("quality_class"),
                "closure_readiness": expected_readiness,
                "useful_completion": candidate.get("useful_completion"),
            }
        )

    comparison = record.get("comparative_disposition", {})
    for configuration_id, label in expected_mapping.items():
        candidate = next(
            (row for row in candidates if row.get("candidate_label") == label), {}
        )
        row = comparison.get(configuration_id, {})
        for key in ("candidate_label", "quality_class", "closure_readiness", "useful_completion"):
            if row.get(key) != candidate.get(key):
                failures.append(f"comparison:{configuration_id}:{key}")

    return {
        "schema_version": "cedar-artifact-coupling-semantic-adjudication-validation-v0",
        "record_sha256": digest(RECORD),
        "protocol_sha256": digest(PROTOCOL),
        "run_id": record.get("run_id"),
        "derived_candidates": sorted(derived, key=lambda row: row["candidate_label"]),
        "passed": not failures,
        "failures": failures,
    }


def main() -> int:
    result = validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
