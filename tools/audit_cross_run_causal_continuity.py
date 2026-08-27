from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import write_json  # noqa: E402
from reactive_runtime.verification_causal_frame import (  # noqa: E402
    action_signature,
    action_target,
    build_verification_causal_frame,
)
from tools.offline_tokenizer import OfflineTokenizer  # noqa: E402


OUTPUT = ROOT / "CROSS_RUN_CAUSAL_CONTINUITY_AUDIT.json"

CASES = [
    {
        "case_id": "E46_ARCHITECTURE_A1",
        "world": "architecture_decision",
        "role": "interaction_cell",
        "path": "runs/2026-08-24-artifact-coupled-interaction-measured-v0/cells/A1_COUPLED/CALL_TRACE.json",
    },
    {
        "case_id": "E46_ARCHITECTURE_D0",
        "world": "architecture_decision",
        "role": "interaction_cell",
        "path": "runs/2026-08-24-artifact-coupled-interaction-measured-v0/cells/D0_DETACHED/CALL_TRACE.json",
    },
    {
        "case_id": "E52_CEDAR_A1",
        "world": "cedar",
        "role": "negative_control_no_rejection",
        "path": "runs/2026-08-25-cedar-artifact-coupling-transfer-measured-v0/cells/A1_COUPLED/CALL_TRACE.json",
    },
    {
        "case_id": "E52_CEDAR_D0",
        "world": "cedar",
        "role": "negative_control_no_rejection",
        "path": "runs/2026-08-25-cedar-artifact-coupling-transfer-measured-v0/cells/D0_DETACHED/CALL_TRACE.json",
    },
    {
        "case_id": "E69_SOLACE_L1",
        "world": "solace",
        "role": "construction_interaction",
        "path": "runs/2026-08-26-solace-anchored-provenance-interaction-measured-v0/cells/L1_FAULT_TOLERANT_ANCHORED_PROVENANCE/ACTOR_TRACE.json",
    },
    {
        "case_id": "E69_SOLACE_W0",
        "world": "solace",
        "role": "transport_failure_case",
        "path": "runs/2026-08-26-solace-anchored-provenance-interaction-measured-v0/cells/W0_DIRECT_EXACT_WORK_FRESH/ACTOR_TRACE.json",
    },
    {
        "case_id": "E72_SOLACE_A0",
        "world": "solace",
        "role": "successful_patch_check_loop_control",
        "path": "runs/2026-08-27-solace-verification-lifecycle-measured-v0/cells/A0_EXACT_ARTIFACT_ONLY/ACTOR_TRACE.json",
    },
    {
        "case_id": "E72_SOLACE_A1",
        "world": "solace",
        "role": "successful_patch_check_loop_control",
        "path": "runs/2026-08-27-solace-verification-lifecycle-measured-v0/cells/A1_EXACT_ARTIFACT_PLUS_FROZEN_REGISTER/ACTOR_TRACE.json",
    },
    {
        "case_id": "E76_ORCHARD_F0",
        "world": "orchard",
        "role": "fixed_state_control",
        "path": "runs/2026-08-27-orchard-phase-lifecycle-measured-v0/cells/F0_FIXED_SCAFFOLD_APPEND_ONLY_VERIFICATION/ACTOR_TRACE.json",
    },
    {
        "case_id": "E76_ORCHARD_P1",
        "world": "orchard",
        "role": "current_state_recurrence_case",
        "path": "runs/2026-08-27-orchard-phase-lifecycle-measured-v0/cells/P1_PHASE_CONDITIONAL_CURRENT_VERIFICATION/ACTOR_TRACE.json",
    },
]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def call_number(row: dict[str, Any], fallback: int) -> int:
    value = row.get("actor_call")
    if value is None:
        value = row.get("logical_call")
    return int(value if value is not None else fallback)


def changed(row: dict[str, Any]) -> bool:
    before = row.get("candidate_sha256_before")
    after = row.get("candidate_sha256_after")
    return bool(before and after and before != after)


def exact_event_signature(row: dict[str, Any]) -> str | None:
    signature = action_signature(row.get("parsed_action"))
    if signature:
        return f"action:{signature}"
    if row.get("rejection_code"):
        return f"unparsed-rejection:{row['rejection_code']}"
    return None


def consecutive_recurrence(trace: list[dict[str, Any]]) -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    index = 0
    while index < len(trace):
        signature = exact_event_signature(trace[index])
        end = index + 1
        while signature and end < len(trace) and exact_event_signature(trace[end]) == signature:
            end += 1
        if signature and end - index > 1:
            group = trace[index:end]
            episodes.append(
                {
                    "first_actor_call": call_number(group[0], index + 1),
                    "last_actor_call": call_number(group[-1], end),
                    "count": len(group),
                    "event_signature": signature,
                    "action": (group[-1].get("parsed_action") or {}).get("action"),
                    "target": action_target(group[-1].get("parsed_action")),
                    "rejection_codes": [row.get("rejection_code") for row in group],
                    "candidate_changed": any(changed(row) for row in group),
                }
            )
        index = end
    return episodes


def rejection_episodes(trace: list[dict[str, Any]]) -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    for index, row in enumerate(trace):
        if not row.get("rejection_code"):
            continue
        candidate = row.get("candidate_sha256_after")
        resolution = None
        for later_index, later in enumerate(trace[index + 1 :], start=index + 1):
            if changed(later):
                resolution = {
                    "actor_call": call_number(later, later_index + 1),
                    "result_kind": later.get("result_kind"),
                    "action": (later.get("parsed_action") or {}).get("action"),
                }
                break
        intervening = trace[index + 1 :]
        if resolution:
            resolution_index = next(
                idx
                for idx, candidate_row in enumerate(trace)
                if call_number(candidate_row, idx + 1) == resolution["actor_call"]
            )
            intervening = trace[index + 1 : resolution_index]
        episodes.append(
            {
                "actor_call": call_number(row, index + 1),
                "code": row.get("rejection_code"),
                "action": (row.get("parsed_action") or {}).get("action"),
                "action_signature": action_signature(row.get("parsed_action")),
                "candidate_sha256": candidate,
                "resolved_by_later_candidate_effect": resolution,
                "intervening_actions": [
                    (later.get("parsed_action") or {}).get("action") for later in intervening
                ],
                "endpoint_candidate_unchanged": not any(changed(later) for later in trace[index + 1 :]),
            }
        )
    return episodes


def case_audit(spec: dict[str, str], tokenizer: OfflineTokenizer) -> dict[str, Any]:
    path = ROOT / spec["path"]
    trace: list[dict[str, Any]] = load(path)
    rejection_rows = [row for row in trace if row.get("rejection_code")]
    effects = [row for row in trace if row.get("result_kind") == "candidate_effect"]
    checks = [row for row in trace if row.get("result_kind") == "check_observation"]
    frame = build_verification_causal_frame(
        trace, history_handle=f"history://{spec['case_id']}"
    )
    frame_text = json.dumps(frame, ensure_ascii=False, sort_keys=True, indent=2)
    return {
        **spec,
        "trace_sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
        "actor_calls": len(trace),
        "candidate_effects": len(effects),
        "checks": len(checks),
        "rejections": Counter(str(row["rejection_code"]) for row in rejection_rows),
        "rejection_episodes": rejection_episodes(trace),
        "consecutive_recurrence": consecutive_recurrence(trace),
        "final_candidate_sha256": trace[-1].get("candidate_sha256_after"),
        "final_frame": frame,
        "final_frame_tokens": tokenizer.count_text(frame_text),
        "final_frame_bytes": len(frame_text.encode("utf-8")),
    }


def main() -> int:
    failures: list[str] = []
    tokenizer = OfflineTokenizer()
    cases = [case_audit(spec, tokenizer) for spec in CASES]

    missing = [row["case_id"] for row in cases if row["actor_calls"] < 1]
    failures.extend(f"empty_trace:{value}" for value in missing)
    by_id = {row["case_id"]: row for row in cases}

    e46_repeat = by_id["E46_ARCHITECTURE_D0"]["consecutive_recurrence"]
    solace_repeat = by_id["E69_SOLACE_W0"]["consecutive_recurrence"]
    orchard_repeat = by_id["E76_ORCHARD_P1"]["consecutive_recurrence"]
    if not any(row["count"] == 2 and row["action"] == "upsert_decision_section" for row in e46_repeat):
        failures.append("missing:E46 rejected exact action recurrence")
    if not any(row["count"] == 2 and row["event_signature"] == "unparsed-rejection:invalid_json" for row in solace_repeat):
        failures.append("missing:Solace transport recurrence")
    if not any(row["count"] == 4 and row["target"] == "CURRENT:1-64" for row in orchard_repeat):
        failures.append("missing:Orchard read recurrence")

    orchard_frame = by_id["E76_ORCHARD_P1"]["final_frame"]
    if (orchard_frame.get("active_rejected_action") or {}).get("rejection_code") != "patch_anchor_not_unique":
        failures.append("frame:Orchard rejection was displaced")
    if (orchard_frame.get("recurrence") or {}).get("count_in_current_candidate_epoch") != 4:
        failures.append("frame:Orchard recurrence count")
    if max(row["final_frame_tokens"] for row in cases) > 1400:
        failures.append("frame:token ceiling exceeded")

    output = {
        "schema": "cross-run-causal-continuity-audit-v0",
        "date": "2026-08-27",
        "passed": not failures,
        "failures": failures,
        "scope": {
            "independent_worlds": sorted({row["world"] for row in cases}),
            "cells": len(cases),
            "actor_calls": sum(row["actor_calls"] for row in cases),
            "new_model_calls": 0,
        },
        "cases": cases,
        "cross_world_findings": {
            "action_transport_failure_worlds": [
                "architecture_decision",
                "solace",
                "orchard",
            ],
            "exact_or_functional_nonprogress_recurrence_worlds": [
                "architecture_decision",
                "solace",
                "orchard",
            ],
            "rejected_mutation_recurrence_worlds": [
                "architecture_decision",
                "orchard",
            ],
            "negative_or_successful_controls": {
                "cedar": "no action rejection or exact consecutive recurrence in either measured cell",
                "solace_verification": "patch/check alternation admitted repairs without rejection until final undelivered effects",
                "orchard_call_16": "a non-unique patch rejection followed by targeted evidence recovery and an admitted repair while the rejection remained recent",
            },
            "supported": [
                "action transport and rejection continuity are cross-world system boundaries",
                "an unresolved rejected mutation must not be erased merely because a later source observation arrives",
                "candidate-bound current checks and exact artifacts are necessary but not sufficient for non-repeating repair",
                "candidate-and-section-hash-bound repair is a justified apparatus correction because ambiguous free-form anchors failed live",
            ],
            "not_supported": [
                "a causal frame alone improves model behavior",
                "the proposed frame fields are minimal or sufficient",
                "recurrence should automatically authorize a semantic intervention or closure",
                "Orchard should be rerun or extended",
            ],
        },
        "prospective_contract": {
            "frame_schema": "bounded-verification-causal-frame-v0",
            "frame_ownership": "host_mechanical_projection_only",
            "persistent_slots": [
                "current_candidate",
                "current_check_and_currency",
                "latest_attempt",
                "active_rejected_action_until_candidate_change",
                "latest_delivered_update",
                "latest_candidate_effect",
                "current_candidate_epoch_recurrence",
                "exact_history_handle",
            ],
            "repair_action": "replace_artifact_section",
            "repair_bindings": [
                "current_candidate_sha256",
                "current_artifact_sha256",
                "unique_section_heading",
                "expected_section_sha256",
                "complete_replacement_section",
            ],
            "semantic_host_judgment": False,
            "automatic_recurrence_intervention": False,
        },
    }
    write_json(OUTPUT, output)
    print(
        json.dumps(
            {
                "schema": output["schema"],
                "passed": output["passed"],
                "failures": output["failures"],
                "scope": output["scope"],
                "maximum_frame_tokens": max(row["final_frame_tokens"] for row in cases),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if output["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
