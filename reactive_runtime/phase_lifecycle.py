from __future__ import annotations

from typing import Iterable

from reactive_runtime.canonical import canonical_json_text
from reactive_runtime.records import ResultLedger
from reactive_runtime.world import ArchitectureWorld


REGISTER_HEADER = "# Anchored provenance-local source register"
PROJECTION_HEADER = "# Current verification projection"


def without_register(messages: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    return [
        dict(message)
        for message in messages
        if not message.get("content", "").startswith(REGISTER_HEADER)
    ]


def verification_projection(
    *,
    world: ArchitectureWorld,
    ledger: ResultLedger,
    pending_result_id: str | None,
    latest_effect_result_id: str | None,
    full_history_handle: str,
    scaffold_handle: str,
) -> str:
    pending = None if pending_result_id is None else ledger.get(pending_result_id)
    latest_effect = None if latest_effect_result_id is None else ledger.get(latest_effect_result_id)
    external = [
        {
            "result_id": record.result_id,
            "kind": record.result_kind,
            "object_id": record.object_id,
            "object_version": record.object_version,
            "handle": f"result://{record.result_id}",
        }
        for record in ledger.records()
        if record.previously_visible and not record.resident
    ]
    check = world.current_check_binding()
    payload = {
        "schema": "orchard-current-verification-projection-v0",
        "current_candidate_sha256": world.candidate_sha256,
        "current_candidate_version": world.candidate_version,
        "phase": "verification",
        "latest_effect_result_id": latest_effect_result_id,
        "latest_effect_delivery": (
            None
            if latest_effect is None
            else "pending_in_this_projection"
            if pending_result_id == latest_effect_result_id
            else "previously_model_visible"
            if latest_effect.previously_visible
            else "not_yet_model_visible"
        ),
        "current_check": check,
        "current_candidate_verification_status": (
            "not_run"
            if check is None
            else "current"
            if check.get("currency") == "current"
            else "stale"
        ),
        "pending_result": None
        if pending is None
        else {
            "result_id": pending.result_id,
            "kind": pending.result_kind,
            "object_id": pending.object_id,
            "object_version": pending.object_version,
            "candidate_sha256_after": pending.candidate_sha256_after,
        },
        "external_result_handles": external,
        "semantic_scaffold_handle": scaffold_handle,
        "full_history_handle": full_history_handle,
        "semantic_readiness": "not_adjudicated",
    }
    chunks = [PROJECTION_HEADER, canonical_json_text(payload)]
    if pending is not None:
        chunks.extend(("--- exact pending result ---", pending.exact_content))
    return "\n".join(chunks)


def p1_verification_messages(
    *,
    task_system: str,
    task_text: str,
    action_text: str,
    source_catalog: str,
    world: ArchitectureWorld,
    ledger: ResultLedger,
    pending_result_id: str | None,
    latest_effect_result_id: str | None,
    full_history_handle: str,
    scaffold_handle: str,
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": task_system},
        {"role": "user", "content": task_text},
        {"role": "user", "content": action_text},
        {"role": "user", "content": "# Exact source catalog\n" + source_catalog},
        {"role": "user", "content": "# Exact current candidate\n" + world.candidate_packet()},
        {
            "role": "user",
            "content": verification_projection(
                world=world,
                ledger=ledger,
                pending_result_id=pending_result_id,
                latest_effect_result_id=latest_effect_result_id,
                full_history_handle=full_history_handle,
                scaffold_handle=scaffold_handle,
            ),
        },
    ]
