from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json  # noqa: E402


OUTPUT = ROOT / "MERIDIAN_SOURCE_RELATION_TOPOLOGY_AUDIT.json"
EXPECTED_FIRST_REJECTED = ("DRIFT", "EMBER", "HEATH", "NORTH")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def audit(repository_root: Path = ROOT, *, write_output: bool = True) -> dict[str, Any]:
    root = repository_root.resolve()
    catalog_path = root / "task_meridian" / "SOURCE_CATALOG.json"
    source_lock_path = root / "task_meridian" / "TASK_SOURCE_LOCK.json"
    result_path = root / "MERIDIAN_SOURCE_DELTA_QUALIFICATION_AUDIT.json"
    catalog = load(catalog_path)
    result = load(result_path)
    sources = catalog.get("sources")
    failures: list[str] = []
    if not isinstance(sources, list):
        sources = []
        failures.append("catalog_sources")
    source_ids = tuple(str(row["source_id"]) for row in sources)
    rows: list[dict[str, Any]] = []
    for row in sources:
        source_id = str(row["source_id"])
        source_path = root / "task_meridian" / str(row["path"])
        text = source_path.read_text(encoding="utf-8")
        references = tuple(
            candidate
            for candidate in source_ids
            if candidate != source_id
            and re.search(
                rf"(?<![A-Z0-9_-]){re.escape(candidate)}(?![A-Z0-9_-])", text
            )
        )
        rows.append(
            {
                "source_id": source_id,
                "source_sha256": sha256_file(source_path),
                "referenced_source_ids": list(references),
                "directed_reference_count": len(references),
            }
        )
    files_with_cross_references = sum(
        1 for row in rows if row["directed_reference_count"] > 0
    )
    directed_edges = sum(int(row["directed_reference_count"]) for row in rows)
    bramble = next((row for row in rows if row["source_id"] == "BRAMBLE"), None)
    if len(rows) != 16:
        failures.append("source_count")
    if files_with_cross_references != 16:
        failures.append("cross_reference_file_count")
    if directed_edges != 66:
        failures.append("directed_edge_count")
    if bramble is None or tuple(bramble["referenced_source_ids"]) != EXPECTED_FIRST_REJECTED:
        failures.append("bramble_reference_set")
    if tuple(result.get("disallowed_source_ids", [])) != EXPECTED_FIRST_REJECTED:
        failures.append("qualification_rejection_set")

    value = {
        "schema": "meridian-source-relation-topology-audit-v0",
        "passed": not failures,
        "failures": sorted(set(failures)),
        "task_id": "meridian-sterile-infusion-recovery-v0",
        "source_count": len(rows),
        "files_with_cross_source_references": files_with_cross_references,
        "directed_cross_source_reference_edges": directed_edges,
        "source_rows": rows,
        "first_expression_owner_source": "BRAMBLE",
        "first_expression_exact_relationship_object_ids": list(
            bramble["referenced_source_ids"] if bramble is not None else []
        ),
        "first_expression_rejected_ids": list(
            result.get("disallowed_source_ids", [])
        ),
        "sets_match": bramble is not None
        and tuple(bramble["referenced_source_ids"]) == tuple(
            result.get("disallowed_source_ids", [])
        ),
        "mechanical_finding": "every exact Meridian source contains at least one other source identity; lexical no-absent-source-reference admission is structurally incompatible with preserving named many-to-many relationships",
        "claim_limit": "post-run offline topology audit; no new model behavior and no retroactive change to the frozen qualification",
        "source_catalog_sha256": sha256_file(catalog_path),
        "task_source_lock_sha256": sha256_file(source_lock_path),
        "qualification_audit_sha256": sha256_file(result_path),
    }
    if write_output:
        write_json(OUTPUT, value)
    return value


def main() -> int:
    value = audit()
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
