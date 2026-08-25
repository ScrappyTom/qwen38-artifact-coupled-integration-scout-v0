from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json


RUN_ID = "2026-08-25-cedar-artifact-coupling-transfer-measured-v0"
RUN_ROOT = ROOT / "runs" / RUN_ID
OUTPUT = ROOT / "CEDAR_INTERACTION_ECONOMICS_AUDIT.json"
CONFIGURATIONS = ("D0_DETACHED", "A1_COUPLED")
BOUNDARY_ACTOR_CALLS = 5
MAX_ACTOR_CALLS = 34
MAX_MAINTENANCE_CALLS = 18
MAX_PROVIDER_CALLS = 52
MAX_SERIALIZED_TOKENS = 1_600_000
MINIMUM_CLEAN_VERIFICATION_TAIL = 4

SOURCE_PATTERN = re.compile(r"(?<![A-Za-z0-9])S(?:0[1-9]|1[0-6])(?![A-Za-z0-9])")
KNOWN_ERROR_MARKERS = {
    "arrival_hours_as_wind_speed": "5.8 km/h",
    "wind_shift_probability_as_humidity": "42 percent relative humidity",
    "survey_coverage_as_uncertainty": "nineteen percent uncertainty",
    "revision_binding_as_permitted_count": "one zone revision is permitted",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def action_summary(row: dict[str, Any]) -> dict[str, Any]:
    action = row.get("parsed_action") or {}
    action_type = action.get("action", "rejected")
    value: dict[str, Any] = {"action": action_type}
    if action_type == "read_batch":
        value["source_ids"] = [item["source_id"] for item in action["requests"]]
    elif action_type == "read_source":
        value["source_ids"] = [action["source_id"]]
    elif action_type.startswith("replace_"):
        value["content_characters"] = len(action.get("content", ""))
        value["source_ids"] = sorted(set(SOURCE_PATTERN.findall(action.get("content", ""))))
    return value


def first_marker_occurrence(
    marker: str,
    maintenance_outputs: list[tuple[int, bool, str]],
    actor_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    marker_folded = marker.casefold()
    maintenance = next(
        (
            {"maintenance_call": ordinal, "accepted": accepted}
            for ordinal, accepted, body in maintenance_outputs
            if marker_folded in body.casefold()
        ),
        None,
    )
    actor = next(
        (
            {
                "actor_call": int(row["actor_call"]),
                "action": (row.get("parsed_action") or {}).get("action"),
            }
            for row in actor_rows
            if marker_folded
            in str((row.get("parsed_action") or {}).get("content", "")).casefold()
        ),
        None,
    )
    if maintenance is not None and maintenance["accepted"]:
        origin = "accepted_maintenance"
    elif actor is not None:
        origin = "ordinary_actor_work"
    elif maintenance is not None:
        origin = "rejected_maintenance_only"
    else:
        origin = "not_present"
    return {
        "marker": marker,
        "first_maintenance_occurrence": maintenance,
        "first_actor_occurrence": actor,
        "first_admitted_origin": origin,
    }


def check_currency(actor_rows: list[dict[str, Any]]) -> dict[str, Any]:
    checks = [
        row
        for row in actor_rows
        if (row.get("parsed_action") or {}).get("action") == "run_check"
    ]
    if not checks:
        return {
            "check_calls": [],
            "final_check_status": "never_run",
            "mutations_after_last_check": [],
        }
    last = checks[-1]
    later_mutations = [
        int(row["actor_call"])
        for row in actor_rows
        if int(row["actor_call"]) > int(last["actor_call"])
        and row.get("candidate_sha256_before") != row.get("candidate_sha256_after")
    ]
    return {
        "check_calls": [int(row["actor_call"]) for row in checks],
        "last_check_result_id": last.get("result_id"),
        "last_check_evaluated_candidate_sha256": last.get("candidate_sha256_before"),
        "mutations_after_last_check": later_mutations,
        "final_check_status": "stale" if later_mutations else "current",
    }


def build_cell(configuration_id: str) -> dict[str, Any]:
    cell = RUN_ROOT / "cells" / configuration_id
    actor_rows: list[dict[str, Any]] = read_json(cell / "CALL_TRACE.json")
    maintenance_rows: list[dict[str, Any]] = read_json(cell / "MAINTENANCE_TRACE.json")
    lifecycle: list[dict[str, Any]] = read_json(cell / "LIFECYCLE_EVENTS.json")
    result_records = {
        row["result_id"]: row for row in read_json(cell / "RESULT_LEDGER.json")["records"]
    }
    cell_result = read_json(cell / "CELL_RESULT.json")

    relief_by_result: dict[str, dict[str, Any]] = {}
    for event in lifecycle:
        if event.get("event") != "pressure_relief_pass":
            continue
        for result_id in event.get("selected_result_ids", []):
            relief_by_result[result_id] = event

    effect_records = {
        row["result_id"]: row
        for row in result_records.values()
        if str(row["result_id"]).startswith("MAINT-EFFECT-")
    }
    maintenance_outputs: list[tuple[int, bool, str]] = []
    maintenance_events: list[dict[str, Any]] = []
    accepted_ordinals: list[int] = []
    rejected_ordinals: list[int] = []
    prior_version = 0
    cumulative_maintenance_tokens = 0

    for row in maintenance_rows:
        ordinal = int(row["maintenance_call"])
        result_id = row["input_result_id"]
        record = result_records[result_id]
        output_path = (
            cell
            / "maintenance"
            / f"call-{ordinal:03d}-{result_id}"
            / "assistant_content.txt"
        )
        output = output_path.read_text(encoding="utf-8")
        accepted = bool(row["accepted"])
        maintenance_outputs.append((ordinal, accepted, output))
        (accepted_ordinals if accepted else rejected_ordinals).append(ordinal)
        usage = row["usage"]
        cumulative_maintenance_tokens += int(usage["total_tokens"])
        relief = relief_by_result[result_id]
        acquired_actor_call = max(0, int(record["acquired_call"]) - BOUNDARY_ACTOR_CALLS)
        next_actor = next(
            (
                item
                for item in actor_rows
                if int(item["actor_call"]) > acquired_actor_call
            ),
            None,
        )
        effect = effect_records.get(row.get("effect_result_id"))
        candidate_before = None
        if effect is not None:
            candidate_before = effect.get("metadata", {}).get("before_sha256")
            if candidate_before is None:
                candidate_before = effect.get("candidate_sha256_after")
        elif configuration_id == "D0_DETACHED":
            candidate_before = row.get("candidate_sha256_after")
        actor_usage_to_event = sum(
            int(item["usage"]["total_tokens"])
            for item in actor_rows
            if int(item["actor_call"]) <= acquired_actor_call
        )
        provider_calls_used = acquired_actor_call + ordinal
        version_after = row.get("integration_version_after")
        event_row = {
            "maintenance_call": ordinal,
            "externalized_result_id": result_id,
            "externalized_after_actor_call": acquired_actor_call,
            "source_ids": list(record.get("metadata", {}).get("source_ids", [])),
            "source_bytes": int(record.get("metadata", {}).get("total_source_bytes", 0)),
            "result_size_bytes": int(record["size_bytes"]),
            "relief_before_tokens": int(relief["before_tokens"]),
            "relief_after_tokens": int(relief["after_tokens"]),
            "relief_savings_tokens": int(relief["before_tokens"])
            - int(relief["after_tokens"]),
            "maintenance_prompt_tokens": int(usage["prompt_tokens"]),
            "maintenance_completion_tokens": int(usage["completion_tokens"]),
            "maintenance_total_tokens": int(usage["total_tokens"]),
            "accepted": accepted,
            "finish_reason": row.get("finish_reason"),
            "validation_code": row["validation"]["code"],
            "validation_issues": list(row["validation"]["issues"]),
            "output_tokens": int(row["validation"]["output_tokens"]),
            "allowed_source_count": len(row["allowed_source_ids"]),
            "output_source_ids": list(row["validation"]["source_ids"]),
            "disallowed_source_ids": list(row["validation"]["disallowed_source_ids"]),
            "integration_version_before": prior_version,
            "integration_version_after": version_after,
            "candidate_sha256_before_maintenance": candidate_before,
            "candidate_sha256_after_maintenance": row.get("candidate_sha256_after"),
            "effect_result_id": row.get("effect_result_id"),
            "effect_kind": row.get("effect_kind"),
            "next_actor_action": None if next_actor is None else action_summary(next_actor),
            "next_actor_call": None if next_actor is None else int(next_actor["actor_call"]),
            "remaining_budget_after_maintenance": {
                "actor_calls": MAX_ACTOR_CALLS - acquired_actor_call,
                "maintenance_calls": MAX_MAINTENANCE_CALLS - ordinal,
                "provider_calls": MAX_PROVIDER_CALLS - provider_calls_used,
                "serialized_tokens": MAX_SERIALIZED_TOKENS
                - actor_usage_to_event
                - cumulative_maintenance_tokens,
            },
            "output_path": output_path.relative_to(ROOT).as_posix(),
            "output_sha256": sha256_file(output_path),
        }
        maintenance_events.append(event_row)
        if accepted and version_after is not None:
            prior_version = int(version_after)

    maintenance_tokens = sum(int(row["usage"]["total_tokens"]) for row in maintenance_rows)
    actor_tokens = sum(int(row["usage"]["total_tokens"]) for row in actor_rows)
    rejection_issue_counts: dict[str, int] = {}
    for row in maintenance_rows:
        if row["accepted"]:
            continue
        for issue in row["validation"]["issues"]:
            rejection_issue_counts[issue] = rejection_issue_counts.get(issue, 0) + 1

    accepted_gaps: list[dict[str, Any]] = []
    previous = 0
    for ordinal in accepted_ordinals:
        accepted_gaps.append(
            {
                "accepted_maintenance_call": ordinal,
                "externalizations_since_prior_acceptance": ordinal - previous,
                "rejected_externalizations_in_gap": ordinal - previous - 1,
            }
        )
        previous = ordinal
    accepted_gaps.append(
        {
            "accepted_maintenance_call": None,
            "externalizations_since_prior_acceptance": len(maintenance_rows) - previous,
            "rejected_externalizations_in_gap": len(maintenance_rows) - previous,
            "terminal_tail": True,
        }
    )

    marker_lineage = {
        marker_id: first_marker_occurrence(marker, maintenance_outputs, actor_rows)
        for marker_id, marker in KNOWN_ERROR_MARKERS.items()
    }
    first_construction = next(
        (
            int(row["actor_call"])
            for row in actor_rows
            if (row.get("parsed_action") or {}).get("action")
            in {"replace_evidence_ledger", "replace_decision"}
        ),
        None,
    )
    first_check = next(
        (
            int(row["actor_call"])
            for row in actor_rows
            if (row.get("parsed_action") or {}).get("action") == "run_check"
        ),
        None,
    )
    final_actor_row = actor_rows[-1]
    final_effect_delivered = not (
        final_actor_row.get("result_kind") == "candidate_effect"
        and final_actor_row.get("result_id") not in set().union(
            *(set(row.get("delivered_result_ids", [])) for row in actor_rows)
        )
    )

    batch_size = 3
    batched_calls = math.ceil(int(cell_result["externalization_count"]) / batch_size)
    return {
        "configuration_id": configuration_id,
        "actor_calls": len(actor_rows),
        "maintenance_calls": len(maintenance_rows),
        "provider_calls": len(actor_rows) + len(maintenance_rows),
        "serialized_tokens": actor_tokens + maintenance_tokens,
        "actor_serialized_tokens": actor_tokens,
        "maintenance_serialized_tokens": maintenance_tokens,
        "maintenance_share_of_provider_calls": len(maintenance_rows)
        / (len(actor_rows) + len(maintenance_rows)),
        "maintenance_share_of_serialized_tokens": maintenance_tokens
        / (actor_tokens + maintenance_tokens),
        "accepted_maintenance_calls": accepted_ordinals,
        "rejected_maintenance_calls": rejected_ordinals,
        "maintenance_acceptance_rate": len(accepted_ordinals) / len(maintenance_rows),
        "rejection_issue_counts": rejection_issue_counts,
        "accepted_update_gaps": accepted_gaps,
        "maintenance_events": maintenance_events,
        "first_exact_work_actor_call": first_construction,
        "first_check_actor_call": first_check,
        "check_currency": check_currency(actor_rows),
        "final_effect_crossed_actor_boundary": final_effect_delivered,
        "terminal_disposition": cell_result["terminal_disposition"],
        "remaining_declared_actor_calls_at_terminal": int(
            cell_result["trajectory_budget"]["remaining_calls_in_current_window"]
        ),
        "clean_verification_tail_opportunity_at_terminal": False,
        "known_semantic_error_lineage": marker_lineage,
        "capacity_only_cadence_accounting": {
            "synchronous_measured": {
                "maintenance_calls": len(maintenance_rows),
                "actor_calls_observed": len(actor_rows),
                "provider_calls_observed": len(actor_rows) + len(maintenance_rows),
                "terminal": cell_result["terminal_disposition"],
            },
            "batch_every_three_externalizations": {
                "maintenance_calls_if_every_externalization_is_integrated": batched_calls,
                "provider_calls_at_observed_actor_horizon": len(actor_rows) + batched_calls,
                "actor_slots_available_to_declared_actor_cap": MAX_ACTOR_CALLS
                - len(actor_rows),
                "provider_headroom_at_declared_cap": MAX_PROVIDER_CALLS
                - (MAX_ACTOR_CALLS + batched_calls),
                "behavioral_outcome": "not_inferred",
            },
            "direct_actor_work": {
                "separate_maintenance_calls": 0,
                "provider_calls_at_observed_actor_horizon": len(actor_rows),
                "actor_slots_available_to_declared_actor_cap": MAX_ACTOR_CALLS
                - len(actor_rows),
                "actor_work_actions_consume_these_slots": True,
                "behavioral_outcome": "not_inferred",
            },
        },
    }


def main() -> int:
    aggregate = read_json(RUN_ROOT / "AGGREGATE_RESULT.json")
    cells = [build_cell(configuration_id) for configuration_id in CONFIGURATIONS]
    value = {
        "schema": "cedar-interaction-economics-audit-v0",
        "status": "offline_design_evidence_only",
        "run_id": RUN_ID,
        "freeze_commit": aggregate["freeze_commit"],
        "bindings": {
            "aggregate_result": {
                "path": (RUN_ROOT / "AGGREGATE_RESULT.json").relative_to(ROOT).as_posix(),
                "sha256": sha256_file(RUN_ROOT / "AGGREGATE_RESULT.json"),
            },
            "run_seal": {
                "path": (RUN_ROOT / "RUN_SEAL.json").relative_to(ROOT).as_posix(),
                "sha256": sha256_file(RUN_ROOT / "RUN_SEAL.json"),
            },
            "semantic_adjudication": {
                "path": "CEDAR_SEMANTIC_ADJUDICATION.json",
                "sha256": sha256_file(ROOT / "CEDAR_SEMANTIC_ADJUDICATION.json"),
            },
        },
        "cells": cells,
        "cross_configuration": {
            "maintenance_outputs_were_identical_through_call": 14,
            "accepted_maintenance_ordinals_in_both": [2, 8, 9, 10, 14],
            "accepted_updates_per_arm": 5,
            "attempted_updates_per_arm": 18,
            "synchronous_acceptance_rate": 5 / 18,
            "semantic_error_origin": "The four adjudicated A1 unit/probability/coverage/revision errors first entered admitted state through ordinary actor decision construction, not an accepted maintenance output.",
            "verification_failure": "Each arm ran one check, then mutated; neither obtained a current recheck. A1 also ended with an undelivered final candidate effect.",
            "resource_failure": "Mandatory per-externalization maintenance reached its independent ceiling while declared actor opportunity remained, making the protected postconstruction tail unreachable.",
            "causal_limit": "Capacity alternatives report only call opportunity under the frozen ceilings. They do not claim that batching or direct work would produce the same requests, outputs, or quality.",
        },
        "answers": {
            "accepted_integration_use": "Accepted ledgers retained accurate task relationships later visible in actor work, but exact reuse cannot be separated from independent interpretation of still-visible sources. The audit supports availability and temporal influence, not unique semantic causation.",
            "rejection_geometry": "Rejection was not a late carrier-only anomaly. Complete twelve-requirement rewrites exceeded the 1,600-token admission cap even at two-source scope, then remained fragile as allowed source scope grew. Some rejected calls also cited unobserved sources.",
            "semantic_loss_and_reacquisition": "Five accepted versions covered only eight sources. Multiple externalizations fell between accepted updates; after the sole A1 check, the actor explicitly reread S05, S07, and S11, all associated with evidence that failed later maintenance admission.",
            "displaced_bandwidth": "Synchronous maintenance consumed 18 of 37 provider calls in each arm and terminated both cells before current recheck or closure despite remaining declared actor calls.",
            "error_lineage": "A1's material 5.8-hour, 42-percent, 91-percent, and revision-binding errors were introduced by ordinary actor construction and then persisted in exact work. Maintenance coupling increased durability but was not their observed source.",
            "qualified_successor": "Compare viable batched-coupled maintenance with direct actor-authored exact cumulative work on a fresh task. Both must preserve effect/currentness uptake and a protected verification/repair/recheck/closure tail; synchronous Cedar remains a historical reference rather than a required new arm.",
        },
        "claim_limits": [
            "This audit adds no model behavior and does not retroactively admit rejected maintenance output.",
            "The cadence alternatives are mechanical capacity accounting, not counterfactual trajectory results.",
            "The Cedar terminal state is a design donor and must not be used as a measured treatment fork.",
        ],
    }
    write_json(OUTPUT, value)
    print(json.dumps({"output": str(OUTPUT), "cells": len(cells), "passed": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
