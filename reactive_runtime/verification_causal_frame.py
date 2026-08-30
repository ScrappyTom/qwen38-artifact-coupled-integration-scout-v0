"""Mechanical causal continuity and uniquely bound section repair primitives.

The frame deliberately contains no model-authored summary or host relevance
judgment.  It projects exact action, result, candidate, check, rejection, and
recurrence facts already present in the external event ledger.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any


HEADING_RE = re.compile(r"(?m)^## ([^\r\n]+)\r?$")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_action(action: dict[str, Any] | None) -> str | None:
    if not action:
        return None
    return json.dumps(action, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def action_signature(action: dict[str, Any] | None) -> str | None:
    canonical = canonical_action(action)
    return sha256_text(canonical) if canonical is not None else None


def action_target(action: dict[str, Any] | None) -> str | None:
    if not action:
        return None
    kind = action.get("action")
    if kind in {"read_source", "read_region"}:
        return f"{action.get('source_id')}:{action.get('start_line')}-{action.get('end_line')}"
    if kind == "read_batch":
        return "+".join(
            f"{row.get('source_id')}:{row.get('start_line')}-{row.get('end_line')}"
            for row in action.get("requests") or []
        )
    if kind == "reopen_exact":
        return str(action.get("result_id") or action.get("object_id") or "")
    if kind == "upsert_decision_section":
        return str(action.get("heading") or "")
    if kind in {"patch_decision", "replace_decision", "replace_evidence_ledger"}:
        edits = action.get("edits") or []
        return f"{kind}:{len(edits)}"
    return None


def _call_number(row: dict[str, Any], fallback: int) -> int:
    value = row.get("actor_call")
    if value is None:
        value = row.get("logical_call")
    return int(value if value is not None else fallback)


def _candidate_changed(row: dict[str, Any]) -> bool:
    before = row.get("candidate_sha256_before")
    after = row.get("candidate_sha256_after")
    return bool(before and after and before != after)


def _outcome(row: dict[str, Any]) -> str:
    if row.get("rejection_code"):
        return "rejected"
    if row.get("result_kind"):
        return "admitted"
    return "no_recorded_effect"


def _event(row: dict[str, Any], fallback: int) -> dict[str, Any]:
    action = row.get("parsed_action")
    return {
        "actor_call": _call_number(row, fallback),
        "action": (action or {}).get("action"),
        "action_signature": action_signature(action),
        "target": action_target(action),
        "outcome": _outcome(row),
        "rejection_code": row.get("rejection_code"),
        "result_id": row.get("result_id"),
        "result_kind": row.get("result_kind"),
        "candidate_changed": _candidate_changed(row),
    }


def _project_check(binding: dict[str, Any], current_candidate: str | None) -> dict[str, Any]:
    evaluated = binding.get("evaluated_candidate_sha256")
    failing = [
        row.get("criterion_id")
        for row in binding.get("criterion_results") or []
        if row.get("status") != "pass"
    ]
    return {
        "evaluator_id": binding.get("evaluator_id"),
        "evaluated_candidate_sha256": evaluated,
        "current_candidate_sha256": current_candidate,
        "mechanical_currency": (
            "current" if evaluated and evaluated == current_candidate else "stale"
        ),
        "passed": binding.get("passed"),
        "closure_readiness": binding.get("closure_readiness"),
        "failing_criterion_ids": failing,
        "blocking_requirement_count": len(binding.get("blocking_requirements") or []),
        "raw_result_handle": binding.get("raw_result_handle"),
    }


def build_verification_causal_frame(
    trace: list[dict[str, Any]], *, history_handle: str
) -> dict[str, Any]:
    """Build a bounded exact projection from an actor trace.

    The latest rejected action remains active until candidate state changes.
    Later source observations therefore cannot silently erase an unresolved
    mutation failure. Recurrence is computed only inside the current candidate
    epoch.
    """

    if not trace:
        raise ValueError("trace must not be empty")

    latest = trace[-1]
    current_candidate = latest.get("candidate_sha256_after")
    last_change_index = -1
    for index, row in enumerate(trace):
        if _candidate_changed(row):
            last_change_index = index
    epoch = trace[last_change_index + 1 :]

    active_rejections = [row for row in epoch if row.get("rejection_code")]
    latest_rejection = active_rejections[-1] if active_rejections else None
    delivered_updates = [row for row in trace if row.get("result_id")]
    latest_update = delivered_updates[-1] if delivered_updates else None
    effects = [row for row in trace if row.get("result_kind") == "candidate_effect"]
    latest_effect = effects[-1] if effects else None
    checks = [row for row in trace if row.get("current_check_binding")]
    latest_check = checks[-1].get("current_check_binding") if checks else None

    signatures = [action_signature(row.get("parsed_action")) for row in epoch]
    signature_counts = Counter(value for value in signatures if value)
    latest_signature = signatures[-1] if signatures else None
    active_rejection_signature = (
        action_signature(latest_rejection.get("parsed_action"))
        if latest_rejection
        else None
    )
    recurrence_signature = (
        active_rejection_signature
        if active_rejection_signature
        and signature_counts[active_rejection_signature] > 1
        else latest_signature
        if latest_signature and signature_counts[latest_signature] > 1
        else None
    )
    recurrence = None
    if recurrence_signature:
        matching = [
            _event(row, index + 1)
            for index, row in enumerate(trace)
            if action_signature(row.get("parsed_action")) == recurrence_signature
            and index > last_change_index
        ]
        recurrence = {
            "action_signature": recurrence_signature,
            "action": matching[-1]["action"],
            "target": matching[-1]["target"],
            "count_in_current_candidate_epoch": len(matching),
            "first_actor_call": matching[0]["actor_call"],
            "latest_actor_call": matching[-1]["actor_call"],
            "candidate_changed_during_recurrence": False,
        }

    if latest_check:
        latest_check = _project_check(latest_check, current_candidate)

    effect_event = _event(latest_effect, trace.index(latest_effect) + 1) if latest_effect else None
    if effect_event and latest_effect:
        effect_event["candidate_sha256_before"] = latest_effect.get("candidate_sha256_before")
        effect_event["candidate_sha256_after"] = latest_effect.get("candidate_sha256_after")

    return {
        "schema": "bounded-verification-causal-frame-v0",
        "current_candidate_sha256": current_candidate,
        "current_check": latest_check,
        "latest_attempt": _event(latest, len(trace)),
        "active_rejected_action": (
            _event(latest_rejection, trace.index(latest_rejection) + 1)
            if latest_rejection
            else None
        ),
        "latest_delivered_update": (
            _event(latest_update, trace.index(latest_update) + 1)
            if latest_update
            else None
        ),
        "latest_candidate_effect": effect_event,
        "recurrence": recurrence,
        "exact_history_handle": history_handle,
    }


def section_spans(document: str) -> list[dict[str, Any]]:
    matches = list(HEADING_RE.finditer(document))
    rows: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(document)
        value = document[start:end]
        rows.append(
            {
                "heading": match.group(1),
                "start": start,
                "end": end,
                "text": value,
                "sha256": sha256_text(value),
            }
        )
    return rows


def apply_bound_section_replacement(
    document: str,
    action: dict[str, Any],
    *,
    current_candidate_sha256: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Apply a candidate- and section-hash-bound replacement.

    The operation never searches for a free-form old substring.  The caller
    names one task-artifact section and binds both the complete candidate and
    the exact section bytes it intends to replace.
    """

    required = {
        "action",
        "candidate_sha256",
        "artifact_sha256",
        "section_heading",
        "expected_section_sha256",
        "replacement_section",
    }
    missing = sorted(required - set(action))
    if missing:
        return document, {"status": "rejected", "code": "missing_fields", "fields": missing}
    if action["action"] != "replace_artifact_section":
        return document, {"status": "rejected", "code": "wrong_action"}

    artifact_sha = sha256_text(document)
    candidate_sha = current_candidate_sha256 or artifact_sha
    if action["candidate_sha256"] != candidate_sha:
        return document, {
            "status": "rejected",
            "code": "candidate_version_mismatch",
            "current_candidate_sha256": candidate_sha,
        }
    if action["artifact_sha256"] != artifact_sha:
        return document, {
            "status": "rejected",
            "code": "artifact_version_mismatch",
            "current_artifact_sha256": artifact_sha,
        }

    matches = [row for row in section_spans(document) if row["heading"] == action["section_heading"]]
    if not matches:
        return document, {"status": "rejected", "code": "section_not_found"}
    if len(matches) != 1:
        return document, {"status": "rejected", "code": "section_not_unique"}
    section = matches[0]
    if action["expected_section_sha256"] != section["sha256"]:
        return document, {
            "status": "rejected",
            "code": "section_version_mismatch",
            "current_section_sha256": section["sha256"],
        }

    # A prior malformed replacement can glue a later Markdown heading to the
    # final paragraph of this section.  Such bytes are no longer a safely
    # isolated section: replacing them would also delete the hidden successor.
    # Stop instead of compounding the structural corruption.
    if re.search(r"(?<!^)(?<!\n)## [^\r\n]+", section["text"]):
        return document, {
            "status": "rejected",
            "code": "section_boundary_invalid",
        }

    replacement = str(action["replacement_section"])
    replacement_matches = list(HEADING_RE.finditer(replacement))
    if len(replacement_matches) != 1 or replacement_matches[0].group(1) != section["heading"]:
        return document, {"status": "rejected", "code": "replacement_heading_mismatch"}
    if replacement == section["text"]:
        return document, {"status": "rejected", "code": "no_effect"}

    # The action supplies one semantic section; the host owns the mechanical
    # Markdown boundary between that section and its successor.  Canonicalize
    # only trailing newlines so an otherwise valid replacement cannot glue the
    # next heading to its last sentence.
    replacement_body = replacement.rstrip("\r\n")
    suffix = document[section["end"] :]
    rendered_replacement = replacement_body + ("\n\n" if suffix else "\n")
    updated = document[: section["start"]] + rendered_replacement + suffix
    return updated, {
        "status": "admitted",
        "code": None,
        "candidate_sha256_before": candidate_sha,
        "artifact_sha256_before": artifact_sha,
        "artifact_sha256_after": sha256_text(updated),
        "section_heading": section["heading"],
        "section_sha256_before": section["sha256"],
        "section_sha256_after": sha256_text(rendered_replacement),
        "boundary_normalized": rendered_replacement != replacement,
    }
