from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json  # noqa: E402
from reactive_runtime.seal import verify_tree_seal  # noqa: E402
from tools import run_measured_interaction as measured  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def audit(run_root: Path) -> dict[str, Any]:
    failures: list[str] = []
    run_root = run_root.resolve()
    if run_root != (ROOT / "runs" / measured.RUN_ID).resolve():
        failures.append("run_root")
    seal_errors = verify_tree_seal(run_root, run_root / "RUN_SEAL.json")
    failures.extend(f"aggregate_seal:{item}" for item in seal_errors)
    aggregate = load(run_root / "AGGREGATE_RESULT.json")
    authorization = load(run_root / "AUTHORIZATION_RECEIPT.json")
    freeze = load(run_root / "FREEZE_BINDING.json")
    if aggregate.get("configuration_order") != list(measured.CONFIGURATION_ORDER):
        failures.append("aggregate:configuration_order")
    if freeze.get("configuration_order") != list(measured.CONFIGURATION_ORDER):
        failures.append("freeze:configuration_order")
    freeze_commit = authorization.get("authorized_freeze_commit")
    if not isinstance(freeze_commit, str) or aggregate.get("freeze_commit") != freeze_commit:
        failures.append("freeze:commit")
    if freeze.get("commit") != freeze_commit:
        failures.append("freeze:binding_commit")
    expected_authorization = {
        "authorized": True,
        "authorized_run_id": measured.RUN_ID,
        "authorized_scope": measured.SCOPE,
        "configuration_order": list(measured.CONFIGURATION_ORDER),
        "maximum_actor_calls": measured.MAX_ACTOR_CALLS_PER_CELL
        * len(measured.CONFIGURATION_ORDER),
        "maximum_maintenance_calls": measured.MAX_MAINTENANCE_CALLS_PER_CELL
        * len(measured.CONFIGURATION_ORDER),
        "maximum_provider_calls": measured.MAX_PROVIDER_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, expected in expected_authorization.items():
        if authorization.get(key) != expected:
            failures.append(f"authorization:{key}")

    rows = aggregate.get("cells")
    if not isinstance(rows, list) or len(rows) != 2:
        failures.append("aggregate:cells")
        rows = []
    totals = Counter()
    cell_receipts: list[dict[str, Any]] = []
    boundary_hash = "eb63671008e22987e37ff1ebc26a8ddb29f92ec55ee1d3d1ad0d7d1d64ae181e"
    for configuration_id in measured.CONFIGURATION_ORDER:
        cell_root = run_root / "cells" / configuration_id
        cell = next(
            (row for row in rows if isinstance(row, dict) and row.get("configuration_id") == configuration_id),
            None,
        )
        if cell is None:
            failures.append(f"cell:{configuration_id}:missing")
            continue
        cell_seal_errors = verify_tree_seal(cell_root, cell_root / "RUN_SEAL.json")
        failures.extend(f"cell:{configuration_id}:seal:{item}" for item in cell_seal_errors)
        stored = load(cell_root / "CELL_RESULT.json")
        if stored != cell:
            failures.append(f"cell:{configuration_id}:aggregate_mismatch")
        trace = json.loads((cell_root / "CALL_TRACE.json").read_text(encoding="utf-8"))
        maintenance = json.loads(
            (cell_root / "MAINTENANCE_TRACE.json").read_text(encoding="utf-8")
        )
        lifecycle = json.loads(
            (cell_root / "LIFECYCLE_EVENTS.json").read_text(encoding="utf-8")
        )
        if not isinstance(trace, list) or len(trace) != cell.get("actor_calls"):
            failures.append(f"cell:{configuration_id}:actor_trace")
            trace = []
        if not isinstance(maintenance, list) or len(maintenance) != cell.get("maintenance_calls"):
            failures.append(f"cell:{configuration_id}:maintenance_trace")
            maintenance = []
        if not isinstance(lifecycle, list):
            failures.append(f"cell:{configuration_id}:lifecycle")
            lifecycle = []
        actor_calls = int(cell.get("actor_calls", -1))
        maintenance_calls = int(cell.get("maintenance_calls", -1))
        provider_calls = int(cell.get("provider_calls", -1))
        serialized = int(cell.get("serialized_tokens", -1))
        if not 0 <= actor_calls <= measured.MAX_ACTOR_CALLS_PER_CELL:
            failures.append(f"cell:{configuration_id}:actor_budget")
        if not 0 <= maintenance_calls <= measured.MAX_MAINTENANCE_CALLS_PER_CELL:
            failures.append(f"cell:{configuration_id}:maintenance_budget")
        if provider_calls != actor_calls + maintenance_calls:
            failures.append(f"cell:{configuration_id}:provider_arithmetic")
        if not 0 <= serialized <= measured.MAX_SERIALIZED_TOKENS_PER_CELL:
            failures.append(f"cell:{configuration_id}:serialized_budget")
        totals.update(
            actor_calls=actor_calls,
            maintenance_calls=maintenance_calls,
            provider_calls=provider_calls,
            serialized_tokens=serialized,
        )
        attempt_roots = sorted(cell_root.glob("actor/call-*/provider_attempt")) + sorted(
            cell_root.glob("maintenance/call-*/provider_attempt")
        )
        if len(attempt_roots) != provider_calls:
            failures.append(f"cell:{configuration_id}:provider_attempt_count")
        for attempt in attempt_roots:
            receipt = load(attempt / "PROVIDER_CALL_RECEIPT.json")
            if receipt.get("attempted") is not True:
                failures.append(f"cell:{configuration_id}:provider_not_attempted")
            if receipt.get("outcome") != "valid_completion_response":
                failures.append(f"cell:{configuration_id}:provider_outcome")
            if receipt.get("completion_response_valid") is not True:
                failures.append(f"cell:{configuration_id}:provider_invalid")
        selected = []
        for event in lifecycle:
            if not isinstance(event, dict) or event.get("event") != "pressure_relief_pass":
                continue
            picked = event.get("selected_result_ids") or []
            if len(picked) > 1:
                failures.append(f"cell:{configuration_id}:multi_select_relief")
            for result_id in picked:
                selected.append(result_id)
                audit_row = next(
                    (
                        item
                        for item in event.get("candidate_audits", [])
                        if item.get("result_id") == result_id
                    ),
                    None,
                )
                if audit_row is None or int(audit_row.get("prospective_savings", 0)) <= 0:
                    failures.append(f"cell:{configuration_id}:nonpositive_relief:{result_id}")
        maintenance_inputs = [row.get("input_result_id") for row in maintenance]
        if Counter(selected) != Counter(maintenance_inputs):
            failures.append(f"cell:{configuration_id}:maintenance_trigger_parity")
        expected_effects = (
            {"semantic_state_effect"}
            if configuration_id == "D0_DETACHED"
            else {"candidate_effect", "candidate_state_confirmation"}
        )
        for row in maintenance:
            validation = row.get("validation") or {}
            if row.get("accepted"):
                if validation.get("valid") is not True:
                    failures.append(f"cell:{configuration_id}:accepted_invalid_maintenance")
                if row.get("effect_kind") not in expected_effects:
                    failures.append(f"cell:{configuration_id}:maintenance_effect_kind")
                if validation.get("disallowed_source_ids"):
                    failures.append(f"cell:{configuration_id}:maintenance_source_injection")
        initial = load(cell_root / "INITIAL_CONTINUATION_STATE.json")
        if configuration_id == "D0_DETACHED" and initial.get("candidate_sha256") != boundary_hash:
            failures.append("cell:D0_DETACHED:maintenance_mutated_candidate")
        evaluation = cell.get("mechanical_final_evaluation") or {}
        if evaluation.get("candidate_sha256") != cell.get("candidate_sha256"):
            failures.append(f"cell:{configuration_id}:evaluation_binding")
        release = load(cell_root / "model" / "RUNTIME_RELEASE.json")
        if release.get("released") is not True:
            failures.append(f"cell:{configuration_id}:runtime_release")
        cell_receipts.append(
            {
                "configuration_id": configuration_id,
                "cell_seal_verified": not cell_seal_errors,
                "actor_calls": actor_calls,
                "maintenance_calls": maintenance_calls,
                "provider_calls": provider_calls,
                "serialized_tokens": serialized,
                "positive_externalizations": len(selected),
                "candidate_changed": cell.get("candidate_changed"),
                "candidate_submitted": cell.get("candidate_submitted"),
                "terminal_disposition": cell.get("terminal_disposition"),
            }
        )
    aggregate_expected = {
        "actor_calls": totals["actor_calls"],
        "maintenance_calls": totals["maintenance_calls"],
        "provider_calls": totals["provider_calls"],
        "serialized_tokens": totals["serialized_tokens"],
    }
    for key, expected in aggregate_expected.items():
        if aggregate.get(key) != expected:
            failures.append(f"aggregate:{key}")
    if totals["provider_calls"] > measured.MAX_PROVIDER_CALLS:
        failures.append("aggregate:provider_budget")
    return {
        "schema": "artifact-coupled-interaction-measured-audit-v0",
        "run_id": measured.RUN_ID,
        "freeze_commit": freeze_commit,
        "passed": not failures,
        "failures": failures,
        "aggregate_seal_verified": not seal_errors,
        "attempts_per_call": 1,
        "retries": 0,
        **aggregate_expected,
        "cells": cell_receipts,
        "aggregate_result_sha256": sha256_file(run_root / "AGGREGATE_RESULT.json"),
        "run_seal_sha256": sha256_file(run_root / "RUN_SEAL.json"),
        "runtime_released": all(
            load(run_root / "cells" / configuration_id / "model" / "RUNTIME_RELEASE.json").get(
                "released"
            )
            is True
            for configuration_id in measured.CONFIGURATION_ORDER
            if (run_root / "cells" / configuration_id / "model" / "RUNTIME_RELEASE.json").is_file()
        ),
        "independent_semantic_adjudication": "not_performed_by_this_audit",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-root",
        type=Path,
        default=ROOT / "runs" / measured.RUN_ID,
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.run_root)
    if args.output is not None:
        write_json(args.output.resolve(), result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
