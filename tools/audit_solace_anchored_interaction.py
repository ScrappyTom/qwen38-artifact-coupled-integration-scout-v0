from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_bytes, sha256_file, write_json  # noqa: E402
from reactive_runtime.seal import verify_tree_seal  # noqa: E402
from tools import run_solace_anchored_interaction as measured  # noqa: E402


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_object(path: Path) -> dict[str, Any]:
    value = load(path)
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def source_paths() -> dict[str, Path]:
    catalog = load_object(measured.TASK / "SOURCE_CATALOG.json")
    paths: dict[str, Path] = {}
    for row in catalog.get("sources", []):
        if not isinstance(row, dict):
            continue
        source_id = row.get("source_id")
        relative_path = row.get("path")
        if isinstance(source_id, str) and isinstance(relative_path, str):
            paths[source_id] = measured.TASK / relative_path
    return paths


def verify_claim_anchor(
    claim: dict[str, Any], paths: dict[str, Path]
) -> list[str]:
    failures: list[str] = []
    source_id = claim.get("source_id")
    anchor = claim.get("anchor")
    if not isinstance(source_id, str) or source_id not in paths:
        return ["source_id"]
    if not isinstance(anchor, dict):
        return ["anchor"]
    source_bytes = paths[source_id].read_bytes()
    anchor_text = anchor.get("anchor_text")
    context_text = anchor.get("context_text")
    if not isinstance(anchor_text, str) or not isinstance(context_text, str):
        return ["anchor_text"]
    anchor_bytes = anchor_text.encode("utf-8")
    context_bytes = context_text.encode("utf-8")
    start = anchor.get("anchor_start_byte")
    end = anchor.get("anchor_end_byte")
    if type(start) is not int or type(end) is not int:
        failures.append("anchor_offsets")
    elif source_bytes[start:end] != anchor_bytes:
        failures.append("anchor_offset_binding")
    if source_bytes.count(anchor_bytes) != 1:
        failures.append("anchor_not_unique")
    if context_bytes not in source_bytes:
        failures.append("context_absent")
    if sha256_bytes(anchor_bytes) != anchor.get("anchor_sha256"):
        failures.append("anchor_sha256")
    # Materialized context hashes bind the exact physical source line, including
    # its source newline.  The rendered context_text intentionally omits it.
    context_start_line = anchor.get("context_start_line")
    source_lines = source_bytes.splitlines(keepends=True)
    exact_context_bytes = None
    if type(context_start_line) is int and 1 <= context_start_line <= len(source_lines):
        exact_context_bytes = source_lines[context_start_line - 1]
    if exact_context_bytes is None or sha256_bytes(exact_context_bytes) != anchor.get(
        "context_sha256"
    ):
        failures.append("context_sha256")
    if anchor.get("source_id") != source_id:
        failures.append("anchor_source_id")
    if anchor.get("source_version") != claim.get("source_version"):
        failures.append("anchor_source_version")
    if anchor.get("result_id") != claim.get("evidence_result_id"):
        failures.append("anchor_result_id")
    return failures


def audit(run_root: Path) -> dict[str, Any]:
    failures: list[str] = []
    run_root = run_root.resolve()
    expected_root = (ROOT / "runs" / measured.RUN_ID).resolve()
    if run_root != expected_root:
        failures.append("run_root")

    result = load_object(run_root / "RUN_RESULT.json")
    authorization = load_object(run_root / "AUTHORIZATION_RECEIPT.json")
    freeze = load_object(run_root / "FREEZE_BINDING.json")
    aggregate_seal_errors = verify_tree_seal(run_root, run_root / "RUN_SEAL.json")
    failures.extend(f"aggregate_seal:{item}" for item in aggregate_seal_errors)

    expected_authorization = {
        "authorized": True,
        "authorized_run_id": measured.RUN_ID,
        "authorized_scope": measured.SCOPE,
        "configuration_order": list(measured.CONFIGURATION_ORDER),
        "maximum_actor_calls": 68,
        "maximum_maintenance_calls": measured.MAX_MAINTENANCE_CALLS_L1,
        "maximum_provider_calls": measured.MAX_PROVIDER_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, expected in expected_authorization.items():
        if authorization.get(key) != expected:
            failures.append(f"authorization:{key}")
    freeze_commit = authorization.get("authorized_freeze_commit")
    if result.get("freeze_commit") != freeze_commit:
        failures.append("result:freeze_commit")
    if freeze.get("commit") != freeze_commit:
        failures.append("freeze:commit")
    if result.get("configuration_order") != list(measured.CONFIGURATION_ORDER):
        failures.append("result:configuration_order")
    if result.get("failure") is not None:
        failures.append("result:failure")

    rows = result.get("cells")
    if not isinstance(rows, list) or len(rows) != len(measured.CONFIGURATION_ORDER):
        failures.append("result:cells")
        rows = []
    totals: Counter[str] = Counter()
    cell_receipts: list[dict[str, Any]] = []
    paths = source_paths()

    for configuration_id in measured.CONFIGURATION_ORDER:
        cell_root = run_root / "cells" / configuration_id
        cell = next(
            (
                row
                for row in rows
                if isinstance(row, dict)
                and row.get("configuration_id") == configuration_id
            ),
            None,
        )
        if cell is None:
            failures.append(f"cell:{configuration_id}:missing")
            continue
        cell_seal_errors = verify_tree_seal(cell_root, cell_root / "RUN_SEAL.json")
        failures.extend(
            f"cell:{configuration_id}:seal:{item}" for item in cell_seal_errors
        )
        stored = load_object(cell_root / "CELL_RESULT.json")
        if stored != cell:
            failures.append(f"cell:{configuration_id}:aggregate_mismatch")

        actor_trace = load(cell_root / "ACTOR_TRACE.json")
        maintenance_trace = load(cell_root / "MAINTENANCE_TRACE.json")
        relief_trace = load(cell_root / "RELIEF_TRACE.json")
        lifecycle = load(cell_root / "LIFECYCLE.json")
        if not isinstance(actor_trace, list):
            failures.append(f"cell:{configuration_id}:actor_trace_type")
            actor_trace = []
        if not isinstance(maintenance_trace, list):
            failures.append(f"cell:{configuration_id}:maintenance_trace_type")
            maintenance_trace = []
        if not isinstance(relief_trace, list):
            failures.append(f"cell:{configuration_id}:relief_trace_type")
            relief_trace = []
        if not isinstance(lifecycle, list):
            failures.append(f"cell:{configuration_id}:lifecycle_type")
            lifecycle = []

        actor_calls = int(cell.get("actor_calls", -1))
        maintenance_calls = int(cell.get("maintenance_calls", -1))
        provider_calls = int(cell.get("provider_calls", -1))
        serialized_tokens = int(cell.get("serialized_tokens", -1))
        if len(actor_trace) != actor_calls:
            failures.append(f"cell:{configuration_id}:actor_count")
        if len(maintenance_trace) != maintenance_calls:
            failures.append(f"cell:{configuration_id}:maintenance_count")
        if provider_calls != actor_calls + maintenance_calls:
            failures.append(f"cell:{configuration_id}:provider_arithmetic")
        if not 0 <= actor_calls <= measured.MAX_ACTOR_CALLS_PER_CELL:
            failures.append(f"cell:{configuration_id}:actor_budget")
        if configuration_id == "W0_DIRECT_EXACT_WORK_FRESH":
            if maintenance_calls != 0:
                failures.append("cell:W0:maintenance_present")
        elif not 0 <= maintenance_calls <= measured.MAX_MAINTENANCE_CALLS_L1:
            failures.append("cell:L1:maintenance_budget")
        if not 0 <= serialized_tokens <= measured.MAX_SERIALIZED_TOKENS_PER_CELL:
            failures.append(f"cell:{configuration_id}:serialized_budget")

        usage_total = sum(
            int((row.get("usage") or {}).get("total_tokens", -1))
            for row in actor_trace + maintenance_trace
        )
        if usage_total != serialized_tokens:
            failures.append(f"cell:{configuration_id}:serialized_arithmetic")
        attempt_roots = sorted(cell_root.glob("actor/call-*/provider_attempt"))
        attempt_roots += sorted(cell_root.glob("maintenance/call-*/provider_attempt"))
        if len(attempt_roots) != provider_calls:
            failures.append(f"cell:{configuration_id}:attempt_count")
        for attempt in attempt_roots:
            receipt = load_object(attempt / "PROVIDER_CALL_RECEIPT.json")
            if receipt.get("attempted") is not True:
                failures.append(f"cell:{configuration_id}:attempt:not_attempted")
            if receipt.get("outcome") != "valid_completion_response":
                failures.append(f"cell:{configuration_id}:attempt:outcome")
            if receipt.get("completion_response_valid") is not True:
                failures.append(f"cell:{configuration_id}:attempt:invalid")

        selected_results: list[str] = []
        for relief in relief_trace:
            selected = relief.get("selected_result_ids") or []
            if len(selected) > 1:
                failures.append(f"cell:{configuration_id}:relief_multi_select")
            for result_id in selected:
                selected_results.append(str(result_id))
                audit_row = next(
                    (
                        row
                        for row in relief.get("audits", [])
                        if row.get("result_id") == result_id
                    ),
                    None,
                )
                if (
                    not isinstance(audit_row, dict)
                    or audit_row.get("selected") is not True
                    or int(audit_row.get("prospective_savings", 0)) <= 0
                ):
                    failures.append(
                        f"cell:{configuration_id}:relief_nonpositive:{result_id}"
                    )
            before = relief.get("before_tokens")
            after = relief.get("after_tokens")
            if selected and (type(before) is not int or type(after) is not int or after >= before):
                failures.append(f"cell:{configuration_id}:relief_arithmetic")
        if not selected_results or selected_results[0] != "RESULT-001":
            failures.append(f"cell:{configuration_id}:common_fork_relief")

        if configuration_id == "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE":
            maintained = [
                result_id
                for row in maintenance_trace
                for result_id in row.get("input_result_ids", [])
            ]
            if maintained != selected_results:
                failures.append("cell:L1:maintenance_trigger_parity")
            previous_claims = 0
            for row in maintenance_trace:
                admission = row.get("admission") or {}
                transition = row.get("transition") or {}
                admitted = sum(
                    1
                    for record in admission.get("records", [])
                    if isinstance(record, dict) and record.get("admitted") is True
                )
                transition_admitted = len(transition.get("admitted_claim_ids", []))
                if transition.get("disposition") == "register_budget_reject":
                    if transition_admitted != 0 or transition.get("after_sha256") != transition.get(
                        "before_sha256"
                    ):
                        failures.append("cell:L1:register_budget_reject_transition")
                elif transition_admitted != admitted:
                    failures.append("cell:L1:transition_admission_count")
                claims_after = int(row.get("register_claims", -1))
                if claims_after < previous_claims and not transition.get("stale_claim_ids"):
                    failures.append("cell:L1:unexplained_register_shrink")
                previous_claims = claims_after
            register = load_object(cell_root / "CURRENT_REGISTER.json")
            claims = register.get("claims") or []
            if len(claims) != cell.get("register_claims"):
                failures.append("cell:L1:register_count")
            if register.get("sha256") != cell.get("register_sha256"):
                failures.append("cell:L1:register_hash")
            for claim in claims:
                if not isinstance(claim, dict):
                    failures.append("cell:L1:claim_type")
                    continue
                for issue in verify_claim_anchor(claim, paths):
                    failures.append(
                        f"cell:L1:claim:{claim.get('claim_id')}:{issue}"
                    )
        else:
            if cell.get("register_claims") != 0:
                failures.append("cell:W0:register_claims")

        evaluation = cell.get("external_evaluation") or {}
        projection = evaluation.get("projection") or {}
        if evaluation.get("candidate_sha256") != cell.get("candidate_sha256"):
            failures.append(f"cell:{configuration_id}:evaluation_candidate")
        if evaluation.get("evaluated_candidate_sha256") != cell.get("candidate_sha256"):
            failures.append(f"cell:{configuration_id}:evaluation_binding")
        if projection.get("evaluated_candidate_sha256") != cell.get("candidate_sha256"):
            failures.append(f"cell:{configuration_id}:projection_binding")
        release = load_object(cell_root / "model" / "RUNTIME_RELEASE.json")
        if release.get("released") is not True:
            failures.append(f"cell:{configuration_id}:runtime_release")

        action_counts = Counter(
            (row.get("parsed_action") or {}).get("action", "rejected")
            for row in actor_trace
        )
        totals.update(
            actor_calls=actor_calls,
            maintenance_calls=maintenance_calls,
            provider_calls=provider_calls,
            serialized_tokens=serialized_tokens,
        )
        cell_receipts.append(
            {
                "configuration_id": configuration_id,
                "cell_seal_verified": not cell_seal_errors,
                "actor_calls": actor_calls,
                "maintenance_calls": maintenance_calls,
                "provider_calls": provider_calls,
                "serialized_tokens": serialized_tokens,
                "action_counts": dict(sorted(action_counts.items())),
                "positive_relief_events": len(selected_results),
                "register_claims": cell.get("register_claims"),
                "candidate_sha256": cell.get("candidate_sha256"),
                "candidate_submitted": cell.get("candidate_submitted"),
                "closure_readiness": projection.get("closure_readiness"),
                "blocking_requirements": projection.get("blocking_requirements"),
                "terminal_disposition": cell.get("terminal_disposition"),
            }
        )

    for key in ("actor_calls", "maintenance_calls", "provider_calls", "serialized_tokens"):
        if result.get(key) != totals[key]:
            failures.append(f"result:{key}")
    if totals["provider_calls"] > measured.MAX_PROVIDER_CALLS:
        failures.append("result:provider_budget")

    return {
        "schema": "solace-anchored-interaction-audit-v0",
        "run_id": measured.RUN_ID,
        "freeze_commit": freeze_commit,
        "passed": not failures,
        "failures": failures,
        "aggregate_seal_verified": not aggregate_seal_errors,
        "attempts_per_call": 1,
        "retries": 0,
        "actor_calls": totals["actor_calls"],
        "maintenance_calls": totals["maintenance_calls"],
        "provider_calls": totals["provider_calls"],
        "serialized_tokens": totals["serialized_tokens"],
        "cells": cell_receipts,
        "run_result_sha256": sha256_file(run_root / "RUN_RESULT.json"),
        "run_seal_sha256": sha256_file(run_root / "RUN_SEAL.json"),
        "runtime_released": all(
            load_object(
                run_root / "cells" / configuration_id / "model" / "RUNTIME_RELEASE.json"
            ).get("released")
            is True
            for configuration_id in measured.CONFIGURATION_ORDER
        ),
        "semantic_fidelity": "requires independent review",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-root", type=Path, default=ROOT / "runs" / measured.RUN_ID
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
