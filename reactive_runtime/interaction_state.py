from __future__ import annotations

from typing import Any

from reactive_runtime.canonical import canonical_json_text, sha256_bytes
from reactive_runtime.configuration import configuration
from reactive_runtime.integration import IntegrationArtifact
from reactive_runtime.records import ResultLedger
from reactive_runtime.world import ArchitectureWorld


def current_interaction_state_message(
    *,
    configuration_id: str,
    world: ArchitectureWorld,
    integration: IntegrationArtifact | None,
    embed_integration_body: bool = True,
) -> dict[str, str]:
    config = configuration(configuration_id)
    if integration is None:
        body = "# Evidence Integration Ledger\n\nNo accepted integration maintenance exists."
        version = 0
        body_sha256 = None
        inputs: list[str] = []
        sources: list[str] = []
    else:
        body = integration.body
        version = integration.version
        body_sha256 = integration.body_sha256
        inputs = list(integration.input_result_ids)
        sources = list(integration.observed_source_ids)
        if config.artifact_coupled:
            exact_candidate_body = (
                world.candidate_root / "EVIDENCE_INTEGRATION_LEDGER.md"
            ).read_text(encoding="utf-8")
            # Maintenance crosses the candidate boundary in A1, after which
            # ordinary actor actions may revise the same exact task artifact.
            # The current state must expose the current file, not silently
            # overwrite or mislabel an actor-authored repair as maintenance.
            body = exact_candidate_body
        elif world.detached_integration != integration:
            raise RuntimeError("detached integration does not match world sidecar")
    binding: dict[str, Any] = {
        "artifact_coupled": config.artifact_coupled,
        "candidate_sha256": world.candidate_sha256,
        "candidate_version": world.candidate_version,
        "check_binding": world.current_check_binding(),
        "configuration_id": configuration_id,
        "integration_body_embedded_below": embed_integration_body,
        "integration_body_sha256": body_sha256,
        "integration_input_result_ids": inputs,
        "integration_source_ids": sources,
        "integration_version": version,
        "resident_body_sha256": sha256_bytes(body.encode("utf-8")),
        "model_authored_lossy": True,
        "readiness_authority": False,
        "residency_role": (
            "exact_task_candidate_file:EVIDENCE_INTEGRATION_LEDGER.md"
            if config.artifact_coupled
            else "non_authoritative_model_facing_sidecar"
        ),
        "schema": "artifact-coupled-current-interaction-state-v0",
    }
    content = "# Current exact interaction-state binding\n" + canonical_json_text(binding)
    if embed_integration_body:
        content += "\n--- current bounded model-authored integration body ---\n" + body
    return {"role": "user", "content": content}


def exact_history_directory(ledger: ResultLedger) -> str:
    rows = []
    for record in ledger.records():
        rows.append(
            {
                "content_sha256": record.content_sha256,
                "first_model_visible_call": record.first_model_visible_call,
                "object_id": record.object_id,
                "object_version": record.object_version,
                "reopen_action": (
                    {"action": "reopen_exact", "result_id": record.result_id}
                    if record.previously_visible and not record.resident
                    else None
                ),
                "resident": record.resident,
                "result_id": record.result_id,
                "result_kind": record.result_kind,
            }
        )
    return "# Exact external history directory\n" + canonical_json_text(
        {
            "full_exact_chronology": "externally_custodied",
            "records": rows,
            "schema": "artifact-coupled-exact-history-directory-v0",
        }
    )
