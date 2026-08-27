from __future__ import annotations

import json
from pathlib import Path

from reactive_runtime.verification_causal_frame import (
    apply_bound_section_replacement,
    build_verification_causal_frame,
    section_spans,
    sha256_text,
)
from tools import audit_cross_run_causal_continuity as audit
from tools import preflight_verification_causal_contract as preflight


ROOT = Path(__file__).resolve().parents[1]


def row(
    call: int,
    action: dict,
    *,
    before: str = "C0",
    after: str = "C0",
    rejection: str | None = None,
    result_id: str | None = None,
    result_kind: str | None = None,
) -> dict:
    return {
        "actor_call": call,
        "parsed_action": action,
        "candidate_sha256_before": before,
        "candidate_sha256_after": after,
        "rejection_code": rejection,
        "result_id": result_id,
        "result_kind": result_kind,
        "current_check_binding": None,
    }


def test_rejection_survives_later_observations_and_recurrence_is_counted() -> None:
    trace = [
        row(1, {"action": "patch_decision"}, rejection="patch_anchor_not_unique"),
        row(
            2,
            {"action": "read_source", "source_id": "CURRENT", "start_line": 1, "end_line": 64},
            result_id="RESULT-2",
            result_kind="source_observation",
        ),
        row(
            3,
            {"action": "read_source", "source_id": "CURRENT", "start_line": 1, "end_line": 64},
            result_id="RESULT-3",
            result_kind="source_observation",
        ),
    ]
    frame = build_verification_causal_frame(trace, history_handle="history://fixture")
    assert frame["active_rejected_action"]["rejection_code"] == "patch_anchor_not_unique"
    assert frame["latest_delivered_update"]["result_id"] == "RESULT-3"
    assert frame["recurrence"]["count_in_current_candidate_epoch"] == 2
    assert frame["recurrence"]["target"] == "CURRENT:1-64"


def test_candidate_effect_clears_prior_rejection_epoch() -> None:
    trace = [
        row(1, {"action": "patch_decision"}, rejection="patch_anchor_not_unique"),
        row(
            2,
            {"action": "replace_artifact_section"},
            before="C0",
            after="C1",
            result_id="RESULT-2",
            result_kind="candidate_effect",
        ),
    ]
    frame = build_verification_causal_frame(trace, history_handle="history://fixture")
    assert frame["current_candidate_sha256"] == "C1"
    assert frame["active_rejected_action"] is None
    assert frame["latest_candidate_effect"]["result_id"] == "RESULT-2"


def test_repeated_rejection_recurrence_survives_newer_observation() -> None:
    rejected = {"action": "replace_artifact_section", "section_heading": "Power"}
    trace = [
        row(1, rejected, rejection="section_version_mismatch"),
        row(
            2,
            {"action": "read_source", "source_id": "POWER", "start_line": 1, "end_line": 20},
            result_id="RESULT-2",
            result_kind="source_observation",
        ),
        row(3, rejected, rejection="section_version_mismatch"),
        row(
            4,
            {"action": "read_source", "source_id": "POWER", "start_line": 21, "end_line": 40},
            result_id="RESULT-4",
            result_kind="source_observation",
        ),
    ]
    frame = build_verification_causal_frame(trace, history_handle="history://fixture")
    assert frame["latest_attempt"]["action"] == "read_source"
    assert frame["active_rejected_action"]["actor_call"] == 3
    assert frame["recurrence"]["action"] == "replace_artifact_section"
    assert frame["recurrence"]["count_in_current_candidate_epoch"] == 2


def test_section_bound_repair_is_unique_versioned_and_exact() -> None:
    document = "# Decision\n\n## Alpha\nOld alpha.\n\n## Beta\nOld beta.\n"
    sections = {row["heading"]: row for row in section_spans(document)}
    replacement = "## Beta\nNew beta with exact evidence.\n"
    action = {
        "action": "replace_artifact_section",
        "candidate_sha256": sha256_text(document),
        "artifact_sha256": sha256_text(document),
        "section_heading": "Beta",
        "expected_section_sha256": sections["Beta"]["sha256"],
        "replacement_section": replacement,
    }
    updated, receipt = apply_bound_section_replacement(document, action)
    assert receipt["status"] == "admitted"
    assert "Old alpha." in updated
    assert "New beta with exact evidence." in updated
    assert receipt["artifact_sha256_after"] == sha256_text(updated)

    stale, stale_receipt = apply_bound_section_replacement(updated, action)
    assert stale == updated
    assert stale_receipt["code"] == "candidate_version_mismatch"


def test_section_bound_repair_rejects_duplicate_heading_without_mutation() -> None:
    document = "## Alpha\nOne.\n\n## Alpha\nTwo.\n"
    action = {
        "action": "replace_artifact_section",
        "candidate_sha256": sha256_text(document),
        "artifact_sha256": sha256_text(document),
        "section_heading": "Alpha",
        "expected_section_sha256": "unused",
        "replacement_section": "## Alpha\nReplacement.\n",
    }
    updated, receipt = apply_bound_section_replacement(document, action)
    assert updated == document
    assert receipt["code"] == "section_not_unique"


def test_cross_run_audit_passes_and_preserves_claim_limits() -> None:
    assert audit.main() == 0
    result = json.loads(
        (ROOT / "CROSS_RUN_CAUSAL_CONTINUITY_AUDIT.json").read_text(encoding="utf-8")
    )
    assert result["passed"] is True
    assert result["scope"] == {
        "independent_worlds": ["architecture_decision", "cedar", "orchard", "solace"],
        "cells": 10,
        "actor_calls": 157,
        "new_model_calls": 0,
    }
    findings = result["cross_world_findings"]
    assert findings["rejected_mutation_recurrence_worlds"] == [
        "architecture_decision",
        "orchard",
    ]
    assert "a causal frame alone improves model behavior" in findings["not_supported"]
    cases = {row["case_id"]: row for row in result["cases"]}
    assert cases["E76_ORCHARD_P1"]["final_frame"]["recurrence"][
        "count_in_current_candidate_epoch"
    ] == 4
    assert max(row["final_frame_tokens"] for row in result["cases"]) <= 1400


def test_provider_free_contract_preflight_passes_without_utility_claim() -> None:
    assert preflight.main() == 0
    result = json.loads(
        (ROOT / "VERIFICATION_CAUSAL_CONTRACT_PREFLIGHT.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["passed"] is True
    assert result["new_model_calls"] == 0
    assert result["mechanical_frame"]["initial_tokens"] <= 1400
    assert result["mechanical_frame"]["after_repair_recheck_tokens"] <= 1400
    assert result["mechanical_frame"]["after_repair_active_rejection"] is None
    assert result["mechanical_frame"]["after_repair_check_currency"] == "current"
    assert result["repair_transport"]["action_tokens"] <= 1200
    assert result["repair_transport"]["stale_candidate_rejection"]["code"] == (
        "candidate_version_mismatch"
    )
    assert "no evidence that the actor uses the frame" in result["claim_limits"]


def test_docs_select_fresh_whole_system_transfer_not_orchard_tuning() -> None:
    result = (ROOT / "CROSS_RUN_CAUSAL_CONTINUITY_AUDIT.md").read_text(
        encoding="utf-8"
    )
    plan = (
        ROOT / "NEXT_SYSTEM_INTERACTION_BOUNDED_CAUSAL_VERIFICATION_TRANSFER.md"
    ).read_text(encoding="utf-8")
    assert "four independent worlds" in result
    assert "It does not establish that showing this fact to Qwen changes behavior" in result
    assert "whole trajectory" in plan
    assert "Repair transport common to both" in plan
    assert "Do not tune Orchard" in plan
    assert "No GPU call is authorized" in plan
