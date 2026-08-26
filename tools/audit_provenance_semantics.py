from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import canonical_json_text  # noqa: E402
from reactive_runtime.provenance_claims import (  # noqa: E402
    validate_provenance_claim,
)


CASES_PATH = ROOT / "PROVENANCE_SEMANTICS_CASES.json"
AUDIT_PATH = ROOT / "PROVENANCE_SEMANTICS_AUDIT.json"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_catalog(
    root: Path, world: Mapping[str, object]
) -> tuple[Path, dict[str, dict[str, object]]]:
    source_root = root / str(world["source_root"])
    lock = _load_json(root / str(world["source_lock"]))
    rows = lock.get("source_custody")
    if not isinstance(rows, list):
        raise ValueError("source lock lacks source_custody")
    return source_root, {
        str(row["source_id"]): {
            "path": str(row["path"]),
            "sha256": str(row["sha256"]),
        }
        for row in rows
        if isinstance(row, dict)
    }


def _historical_bindings(
    root: Path, case: Mapping[str, object]
) -> tuple[list[dict[str, object]], list[str]]:
    receipts: list[dict[str, object]] = []
    failures: list[str] = []
    rows = case.get("historical_bindings", [])
    if not isinstance(rows, list):
        return receipts, [f"{case.get('case_id')}: historical_bindings invalid"]
    for row in rows:
        if not isinstance(row, dict):
            failures.append(f"{case.get('case_id')}: historical binding invalid")
            continue
        relative = str(row.get("path", ""))
        path = root / relative
        raw = path.read_bytes() if path.is_file() else b""
        actual_sha = sha256(raw).hexdigest() if raw else None
        expected_sha = str(row.get("sha256", ""))
        text = raw.decode("utf-8") if raw else ""
        required = [str(value) for value in row.get("required_substrings", [])]
        missing = [value for value in required if value not in text]
        passed = path.is_file() and actual_sha == expected_sha and not missing
        if not passed:
            failures.append(f"{case.get('case_id')}: historical binding failed: {relative}")
        receipts.append(
            {
                "path": relative,
                "expected_sha256": expected_sha,
                "actual_sha256": actual_sha,
                "required_substrings": required,
                "missing_substrings": missing,
                "passed": passed,
            }
        )
    return receipts, failures


def build_audit(root: Path = ROOT) -> dict[str, object]:
    specification = _load_json(root / CASES_PATH.name)
    worlds = specification.get("worlds")
    cases = specification.get("cases")
    if not isinstance(worlds, dict) or not isinstance(cases, list):
        raise ValueError("provenance case specification malformed")

    failures: list[str] = []
    case_rows: list[dict[str, object]] = []
    for case in cases:
        if not isinstance(case, dict):
            failures.append("non-object case")
            continue
        case_id = str(case.get("case_id", ""))
        world_id = str(case.get("world", ""))
        world = worlds.get(world_id)
        if not isinstance(world, dict):
            failures.append(f"{case_id}: unknown world")
            continue
        source_root, catalog = _source_catalog(root, world)
        admitted_ids = [str(value) for value in case.get("admitted_source_ids", [])]
        admitted = {
            source_id: str(catalog[source_id]["sha256"])
            for source_id in admitted_ids
            if source_id in catalog
        }
        if len(admitted) != len(admitted_ids):
            failures.append(f"{case_id}: admitted source missing from catalog")
        current = {source_id: str(row["sha256"]) for source_id, row in catalog.items()}
        overrides = case.get("current_version_overrides", {})
        if isinstance(overrides, dict):
            current.update({str(key): str(value) for key, value in overrides.items()})
        claim = case.get("claim")
        if not isinstance(claim, dict):
            failures.append(f"{case_id}: claim missing")
            continue
        validation = validate_provenance_claim(
            claim,
            source_catalog=catalog,
            source_root=source_root,
            admitted_source_versions=admitted,
            current_source_versions=current,
        )
        historical, binding_failures = _historical_bindings(root, case)
        failures.extend(binding_failures)
        expected = case.get("expected")
        if not isinstance(expected, dict):
            failures.append(f"{case_id}: expected disposition missing")
            continue
        required_issues = [str(value) for value in expected.get("required_issues", [])]
        missing_issues = [value for value in required_issues if value not in validation.issues]
        expectation_passed = (
            validation.valid is bool(expected.get("mechanical_valid"))
            and validation.currentness == str(expected.get("currentness"))
            and validation.active is bool(expected.get("active"))
            and not missing_issues
        )
        if not expectation_passed:
            failures.append(f"{case_id}: expected disposition mismatch")
        case_rows.append(
            {
                "case_id": case_id,
                "world": world_id,
                "mechanical_valid": validation.valid,
                "mechanical_code": validation.code,
                "mechanical_issues": list(validation.issues),
                "currentness": validation.currentness,
                "active": validation.active,
                "record_kind": validation.record_kind,
                "assertion_mode": validation.assertion_mode,
                "slot_source_id": validation.slot_source_id,
                "evidence_source_ids": list(validation.evidence_source_ids),
                "referent_source_ids": list(validation.referent_source_ids),
                "semantic_review_required": validation.semantic_review_required,
                "frozen_semantic_disposition": str(
                    expected.get("semantic_disposition", "not_adjudicated")
                ),
                "required_issues": required_issues,
                "missing_required_issues": missing_issues,
                "historical_bindings": historical,
                "expectation_passed": expectation_passed,
            }
        )

    row_by_id = {str(row["case_id"]): row for row in case_rows}
    mechanical_pass_semantic_fail = sorted(
        str(row["case_id"])
        for row in case_rows
        if row["mechanical_valid"]
        and str(row["frozen_semantic_disposition"]).startswith("fail_")
    )
    design_findings = {
        "owner_local_fact_admitted": bool(
            row_by_id.get("P01_MERIDIAN_OWNER_LOCAL_FACT", {}).get("mechanical_valid")
        ),
        "e61_relationship_objects_admitted_without_absent_slot_mutation": bool(
            row_by_id.get("P02_E61_BRAMBLE_RELATIONSHIP_OBJECTS", {}).get(
                "mechanical_valid"
            )
        ),
        "absent_source_slot_mutation_blocked": not bool(
            row_by_id.get("P03_MERIDIAN_ABSENT_SOURCE_SLOT_MUTATION", {}).get(
                "mechanical_valid", True
            )
        ),
        "bluehaven_unseen_slot_completion_blocked": not bool(
            row_by_id.get("P09_BLUEHAVEN_UNSEEN_S07_SLOT", {}).get(
                "mechanical_valid", True
            )
        ),
        "derived_multi_source_claim_requires_separate_work_record": bool(
            row_by_id.get("P06_MERIDIAN_DERIVED_MULTI_SOURCE_WORK", {}).get(
                "mechanical_valid"
            )
        )
        and not bool(
            row_by_id.get("P07_MERIDIAN_DERIVED_CLAIM_IN_SOURCE_SLOT", {}).get(
                "mechanical_valid", True
            )
        ),
        "source_version_change_makes_prior_claim_inactive_not_deleted": (
            row_by_id.get("P08_MERIDIAN_PRIOR_VERSION_RETAINED_STALE", {}).get(
                "currentness"
            )
            == "stale"
            and not bool(
                row_by_id.get("P08_MERIDIAN_PRIOR_VERSION_RETAINED_STALE", {}).get(
                    "active", True
                )
            )
        ),
        "mechanical_provenance_does_not_establish_semantic_truth": (
            mechanical_pass_semantic_fail
            == [
                "P05_MERIDIAN_RELATION_PREDICATE_REVERSAL",
                "P10_CEDAR_PROVENANCE_VALID_SEMANTIC_REVERSAL",
            ]
        ),
    }
    if not all(design_findings.values()):
        failures.append("one or more required design findings did not hold")

    return {
        "schema": "provenance-semantics-audit-v0",
        "date": "2026-08-25",
        "cases_sha256": sha256(CASES_PATH.read_bytes()).hexdigest(),
        "case_count": len(case_rows),
        "model_calls": 0,
        "serialized_tokens": 0,
        "case_rows": case_rows,
        "mechanical_pass_semantic_fail_cases": mechanical_pass_semantic_fail,
        "design_findings": design_findings,
        "claim_limit": "historical-fixture apparatus design audit only; it does not regrade E61, qualify model expression, prove semantic correctness, or establish whole-system utility",
        "next_live_operation_authorized": False,
        "failures": failures,
        "passed": not failures,
    }


def main() -> None:
    print(canonical_json_text(build_audit()))


if __name__ == "__main__":
    main()
