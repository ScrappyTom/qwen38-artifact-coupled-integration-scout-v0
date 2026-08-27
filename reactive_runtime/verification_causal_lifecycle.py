from __future__ import annotations

from typing import Any

from reactive_runtime.canonical import canonical_json_text
from reactive_runtime.verification_causal_frame import build_verification_causal_frame


def build_current_only_frame(
    trace: list[dict[str, Any]], *, history_handle: str
) -> dict[str, Any]:
    """Render current state without rejection or recurrence continuity."""

    frame = build_verification_causal_frame(trace, history_handle=history_handle)
    frame["schema"] = "current-verification-frame-v0"
    frame["active_rejected_action"] = None
    frame["recurrence"] = None
    return frame


def verification_frame(
    configuration_id: str,
    trace: list[dict[str, Any]],
    *,
    history_handle: str,
) -> dict[str, Any]:
    if configuration_id == "V0_CURRENT_ONLY":
        return build_current_only_frame(trace, history_handle=history_handle)
    if configuration_id == "V1_BOUNDED_CAUSAL_CONTINUITY":
        return build_verification_causal_frame(trace, history_handle=history_handle)
    raise ValueError(f"unknown causal verification configuration: {configuration_id}")


def verification_messages(
    configuration_id: str,
    *,
    system_text: str,
    task_text: str,
    action_text: str,
    source_catalog: str,
    candidate_packet: str,
    trace: list[dict[str, Any]],
    history_handle: str,
    scaffold_handle: str,
    pending_exact_result: str | None = None,
) -> list[dict[str, str]]:
    frame = verification_frame(
        configuration_id,
        trace,
        history_handle=history_handle,
    )
    frame["semantic_scaffold_handle"] = scaffold_handle
    frame["semantic_readiness"] = "not_adjudicated"
    if pending_exact_result is not None:
        frame["pending_exact_result_delivery"] = "included_below"
    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": task_text},
        {"role": "user", "content": action_text},
        {"role": "user", "content": "# Exact source catalog\n" + source_catalog},
        {"role": "user", "content": "# Exact current candidate\n" + candidate_packet},
        {
            "role": "user",
            "content": "# Exact current verification and causal frame\n"
            + canonical_json_text(frame),
        },
    ]
    if pending_exact_result is not None:
        messages.append(
            {
                "role": "user",
                "content": "# Exact pending result\n" + pending_exact_result,
            }
        )
    return messages
