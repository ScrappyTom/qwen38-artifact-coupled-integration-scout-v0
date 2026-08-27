from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json  # noqa: E402
from tools import run_solace_anchored_interaction as measured  # noqa: E402
from tools.audit_solace_anchored_interaction import audit as audit_mechanics  # noqa: E402


RUN_ROOT = ROOT / "runs" / measured.RUN_ID
OUTPUT = ROOT / "SOLACE_ANCHORED_INTERACTION_ECONOMICS_AUDIT.json"
ADJUDICATION = ROOT / "SOLACE_ANCHORED_INTERACTION_SEMANTIC_ADJUDICATION.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def usage(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        key: sum(int((row.get("usage") or {}).get(key, 0) or 0) for row in rows)
        for key in ("prompt_tokens", "completion_tokens", "total_tokens", "cached_tokens")
    }


def cell_summary(configuration_id: str) -> dict[str, Any]:
    cell_root = RUN_ROOT / "cells" / configuration_id
    cell = load(cell_root / "CELL_RESULT.json")
    actors: list[dict[str, Any]] = load(cell_root / "ACTOR_TRACE.json")
    maintenance: list[dict[str, Any]] = load(cell_root / "MAINTENANCE_TRACE.json")
    relief: list[dict[str, Any]] = load(cell_root / "RELIEF_TRACE.json")
    actor_usage = usage(actors)
    maintenance_usage = usage(maintenance)
    actions = Counter(
        (row.get("parsed_action") or {}).get("action", "rejected") for row in actors
    )
    mutations = [
        int(row["actor_call"])
        for row in actors
        if row.get("candidate_sha256_before") != row.get("candidate_sha256_after")
    ]
    decision_mutations = [
        int(row["actor_call"])
        for row in actors
        if (row.get("parsed_action") or {}).get("action")
        in {"replace_decision", "upsert_decision_section"}
        and row.get("rejection_code") is None
    ]
    reopened = [
        str((row.get("parsed_action") or {}).get("result_id"))
        for row in actors
        if (row.get("parsed_action") or {}).get("action") == "reopen_exact"
    ]
    last_result_id = actors[-1].get("result_id") if actors else None
    delivered_ids = {
        row.get("result_id")
        for row in load(cell_root / "LIFECYCLE.json")
        if row.get("event") == "result_delivery"
    }
    last_relief = relief[-1] if relief else {}
    prompt_total = actor_usage["prompt_tokens"] + maintenance_usage["prompt_tokens"]
    cached_total = actor_usage["cached_tokens"] + maintenance_usage["cached_tokens"]
    return {
        "configuration_id": configuration_id,
        "actor_calls": len(actors),
        "maintenance_calls": len(maintenance),
        "provider_calls": len(actors) + len(maintenance),
        "actor_usage": actor_usage,
        "maintenance_usage": maintenance_usage,
        "combined_total_tokens": actor_usage["total_tokens"]
        + maintenance_usage["total_tokens"],
        "combined_cache_ratio": 0 if not prompt_total else cached_total / prompt_total,
        "action_counts": dict(sorted(actions.items())),
        "candidate_mutation_calls": mutations,
        "decision_mutation_calls": decision_mutations,
        "reopened_result_ids": reopened,
        "last_effect_result_id": last_result_id,
        "last_effect_crossed_later_model_boundary": last_result_id in delivered_ids,
        "check_calls": [
            int(row["actor_call"])
            for row in actors
            if (row.get("parsed_action") or {}).get("action") == "run_check"
        ],
        "submit_calls": [
            int(row["actor_call"])
            for row in actors
            if (row.get("parsed_action") or {}).get("action") == "submit"
        ],
        "positive_relief_events": sum(bool(row.get("selected_result_ids")) for row in relief),
        "terminal_prompt_tokens": last_relief.get("after_tokens"),
        "terminal_prompt_overage": (
            None
            if type(last_relief.get("after_tokens")) is not int
            else int(last_relief["after_tokens"]) - measured.PROMPT_LIMIT
        ),
        "terminal_disposition": cell.get("terminal_disposition"),
        "candidate_sha256": cell.get("candidate_sha256"),
        "candidate_submitted": cell.get("candidate_submitted"),
    }


def maintenance_summary() -> dict[str, Any]:
    cell_root = RUN_ROOT / "cells" / "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE"
    rows: list[dict[str, Any]] = load(cell_root / "MAINTENANCE_TRACE.json")
    records_proposed = 0
    claim_admitted = 0
    claim_rejected = 0
    transaction_admitted = 0
    budget_rejected_claims = 0
    productive_tokens = 0
    unchanged_tokens = 0
    events: list[dict[str, Any]] = []
    for row in rows:
        records = row.get("admission", {}).get("records", [])
        admitted_here = sum(record.get("admitted") is True for record in records)
        rejected_here = len(records) - admitted_here
        transitioned = len(row.get("transition", {}).get("admitted_claim_ids", []))
        total_tokens = int((row.get("usage") or {}).get("total_tokens", 0))
        disposition = row.get("transition", {}).get("disposition")
        records_proposed += len(records)
        claim_admitted += admitted_here
        claim_rejected += rejected_here
        transaction_admitted += transitioned
        if disposition == "register_budget_reject":
            budget_rejected_claims += admitted_here
            unchanged_tokens += total_tokens
        else:
            productive_tokens += total_tokens
        events.append(
            {
                "maintenance_call": row.get("maintenance_call"),
                "input_result_ids": row.get("input_result_ids"),
                "input_source_ids": row.get("input_source_ids"),
                "claim_records": len(records),
                "claim_level_admitted": admitted_here,
                "claim_level_rejected": rejected_here,
                "transition_admitted": transitioned,
                "transition_disposition": disposition,
                "register_claims_after": row.get("register_claims"),
                "total_tokens": total_tokens,
            }
        )
    register = load(cell_root / "CURRENT_REGISTER.json")
    relation_claims = sum(
        claim.get("assertion_mode") == "source_reported_relationship"
        for claim in register.get("claims", [])
    )
    return {
        "calls": len(rows),
        "claim_records_proposed": records_proposed,
        "claim_level_admitted": claim_admitted,
        "claim_level_rejected": claim_rejected,
        "transactionally_admitted": transaction_admitted,
        "admissible_but_register_budget_rejected": budget_rejected_claims,
        "final_register_claims": len(register.get("claims", [])),
        "final_relationship_claims": relation_claims,
        "productive_transition_tokens": productive_tokens,
        "unchanged_register_tokens": unchanged_tokens,
        "events": events,
    }


def artifact_metrics(configuration_id: str) -> dict[str, Any]:
    candidate = (
        RUN_ROOT
        / "cells"
        / configuration_id
        / "trajectory"
        / "world"
        / "candidate"
    )
    decision = (candidate / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md").read_text(
        encoding="utf-8"
    )
    ledger = (candidate / "EVIDENCE_INTEGRATION_LEDGER.md").read_text(encoding="utf-8")
    source_pattern = re.compile(
        r"\[(AURORA|BASTION|CIPHER|DELTA|ECHO|FALCON|GARNET|HELIX|INDIGO|JASPER|KESTREL|LUMEN|MOSAIC|NEXUS)\]"
    )
    return {
        "decision_word_count": len(re.findall(r"\b[\w’-]+\b", source_pattern.sub("", decision))),
        "decision_source_count": len(set(source_pattern.findall(decision))),
        "ledger_source_count": len(set(source_pattern.findall(ledger))),
        "decision_heading_count": len(re.findall(r"(?m)^## ", decision)),
        "decision_sha256": sha256_file(candidate / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"),
        "ledger_sha256": sha256_file(candidate / "EVIDENCE_INTEGRATION_LEDGER.md"),
    }


def main() -> int:
    mechanical = audit_mechanics(RUN_ROOT)
    if not mechanical.get("passed"):
        raise RuntimeError(f"mechanical audit failed: {mechanical.get('failures')}")
    adjudication = load(ADJUDICATION)
    w0 = cell_summary("W0_DIRECT_EXACT_WORK_FRESH")
    l1 = cell_summary("L1_FAULT_TOLERANT_ANCHORED_PROVENANCE")
    w0_tokens = int(w0["combined_total_tokens"])
    l1_tokens = int(l1["combined_total_tokens"])
    output = {
        "schema": "solace-anchored-interaction-economics-audit-v0",
        "run_id": measured.RUN_ID,
        "freeze_commit": mechanical["freeze_commit"],
        "mechanical_audit_passed": True,
        "mechanical_audit_sha256": sha256_file(ROOT / "SOLACE_ANCHORED_INTERACTION_AUDIT.json"),
        "semantic_adjudication_sha256": sha256_file(ADJUDICATION),
        "cells": [w0, l1],
        "artifacts": {
            "W0_DIRECT_EXACT_WORK_FRESH": artifact_metrics(
                "W0_DIRECT_EXACT_WORK_FRESH"
            ),
            "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE": artifact_metrics(
                "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE"
            ),
        },
        "maintenance": maintenance_summary(),
        "comparison": {
            "total_token_difference_L1_minus_W0": l1_tokens - w0_tokens,
            "L1_total_token_reduction_fraction": (w0_tokens - l1_tokens) / w0_tokens,
            "provider_call_difference_L1_minus_W0": int(l1["provider_calls"])
            - int(w0["provider_calls"]),
            "actor_call_difference_L1_minus_W0": int(l1["actor_calls"])
            - int(w0["actor_calls"]),
            "W0_quality_class": adjudication["records"][0]["quality_class"],
            "L1_quality_class": adjudication["records"][1]["quality_class"],
            "W0_useful_completion": adjudication["records"][0]["useful_completion"],
            "L1_useful_completion": adjudication["records"][1]["useful_completion"],
        },
        "disposition": {
            "behavioral_influence": "strong_local_positive",
            "artifact_progress": "L1_strongly_better_but_incomplete",
            "useful_completion": "neither_arm",
            "semantic_expression": "32_of_32_claim_level_admissions_materially_faithful_under_direct_review; 20_entered_register",
            "transport": "partial_admission_worked; source_slot_and_global_register_budgets_discarded_other_grounded_claims",
            "effect_uptake": "all_but_final_L1_candidate_effect_crossed_a_later_actor_boundary",
            "verification_and_closure": "not_reached",
            "architecture_promotion": "not_earned",
        },
        "claim_limits": [
            "This is one paired trajectory from one task/model/seed configuration.",
            "The treatment jointly changes semantic residue, prompt stock, and downstream actor behavior; it does not isolate a claim-level causal effect.",
            "The condition-aware semantic adjudication is not an independent replication.",
            "Neither arm achieved useful completion, current verification, repair, recheck, or closure.",
        ],
    }
    write_json(OUTPUT, output)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
