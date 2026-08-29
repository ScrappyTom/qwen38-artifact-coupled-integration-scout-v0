from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from host_refactor.checkpoint import RuntimeCounters
from host_refactor.effect_lifecycle import CandidateEffectLifecycle
from host_refactor.kernel import HostKernel
from host_refactor.lifecycle_scout.system import (
    DONOR_PROVIDER_ATTEMPTS,
    DONOR_SERIALIZED_TOKENS,
    build_lifecycle_scout_system,
)
from host_refactor.model import DeliveryState, HostEvent
from interaction_scout.lifecycle import InteractionLifecycle
from reactive_runtime.canonical import (
    canonical_json_bytes,
    load_json,
    sha256_bytes,
    sha256_file,
    write_json,
)


DONOR_RUN_ID = "2026-08-29-trellis-refactored-interaction-continuation-v0"
DONOR_CHECKPOINT_SHA256 = (
    "1be26e7d366f4c6f14c1f5975cb70c317768b0702fd36a53b1cc1f224546b955"
)
DONOR_CONFIGURATION_SHA256 = (
    "23cf2425d4c84c9cc3f9c04278a582831f6c4604fe1a586433e730769a5feaaa"
)
DONOR_CANDIDATE_SHA256 = (
    "d133a537f9aef2b3635359316743f39196095c0be3dc6a4b5c86444cdc8a52d9"
)
EXPECTED_EXTERNALIZED_EFFECTS = tuple(f"RESULT-{index:03d}" for index in range(13, 18))
EXPECTED_PENDING_EFFECT = "RESULT-018"


def donor_checkpoint_path(repository_root: Path) -> Path:
    return (
        repository_root
        / "qualification_runs"
        / DONOR_RUN_ID
        / "cells"
        / "V1_TEMPORARY_PROVENANCE_SCAFFOLD"
        / "tranche-002"
        / "CHECKPOINT.json"
    )


@dataclass(frozen=True)
class MigrationOutcome:
    host: Any
    adapter: Any
    orchestrator: Any
    kernel: HostKernel
    counters: RuntimeCounters
    checkpoint: Mapping[str, Any]
    receipt: Mapping[str, Any]


def _verify_checkpoint(value: Mapping[str, Any]) -> None:
    if value.get("schema") != "bounded-host-checkpoint-v0":
        raise ValueError("unsupported donor checkpoint schema")
    payload = dict(value)
    observed = str(payload.pop("checkpoint_sha256", ""))
    actual = sha256_bytes(canonical_json_bytes(payload))
    if observed != DONOR_CHECKPOINT_SHA256 or actual != observed:
        raise ValueError("donor checkpoint hash mismatch")
    if value.get("configuration_sha256") != DONOR_CONFIGURATION_SHA256:
        raise ValueError("donor configuration identity mismatch")


def migrate_e96_donor(
    *,
    repository_root: Path,
    trajectory_root: Path,
    count_messages: Callable[[list[dict[str, str]]], int],
    count_text: Callable[[str], int],
    maintenance_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    checkpoint_output: Path | None = None,
    receipt_output: Path | None = None,
    system_builder: Callable[..., tuple[Any, Any, Any]] | None = None,
) -> MigrationOutcome:
    donor_path = donor_checkpoint_path(repository_root)
    donor = load_json(donor_path)
    _verify_checkpoint(donor)
    if donor["counters"] != {
        "provider_attempts": DONOR_PROVIDER_ATTEMPTS,
        "serialized_tokens": DONOR_SERIALIZED_TOKENS,
    }:
        raise ValueError("donor cumulative counters changed")
    domain = donor.get("domain_state")
    if not isinstance(domain, Mapping):
        raise ValueError("donor lacks domain state")
    trellis = domain.get("trellis")
    interaction = domain.get("interaction")
    if not isinstance(trellis, Mapping) or not isinstance(interaction, Mapping):
        raise ValueError("donor domain state is incomplete")
    if trellis.get("candidate_sha256") != DONOR_CANDIDATE_SHA256:
        raise ValueError("donor candidate identity mismatch")
    if InteractionLifecycle.from_dict(interaction).phase != "construction":
        raise ValueError("donor is not at the frozen construction boundary")

    event_rows = donor["event_log"]["events"]
    if not isinstance(event_rows, list) or not event_rows:
        raise ValueError("donor event log is empty")
    terminal = event_rows[-1]
    if (
        terminal.get("kind") != "terminal_recorded"
        or terminal.get("data", {}).get("code") != "capacity_blocked"
    ):
        raise ValueError("donor terminal is not the frozen capacity endpoint")
    preterminal = HostKernel(HostEvent.from_dict(row) for row in event_rows[:-1])
    if preterminal.project().terminal is not None:
        raise ValueError("donor preterminal state is unexpectedly terminal")

    builder = build_lifecycle_scout_system if system_builder is None else system_builder
    host, adapter, orchestrator = builder(
        repository_root=repository_root,
        trajectory_root=trajectory_root,
        domain_snapshot=trellis,
        lifecycle_snapshot=interaction,
        count_messages=count_messages,
        count_text=count_text,
        maintenance_complete=maintenance_complete,
    )
    before_events_sha256 = preterminal.project().events_sha256
    reconciled = CandidateEffectLifecycle().reconcile(preterminal)
    kernel = reconciled.kernel
    state = kernel.project()
    if reconciled.externalized_result_ids != EXPECTED_EXTERNALIZED_EFFECTS:
        raise ValueError("E97 did not select the frozen applied-effect set")
    if state.results[EXPECTED_PENDING_EFFECT].delivery_state is not DeliveryState.PENDING:
        raise ValueError("frozen pending candidate effect was not preserved")
    if adapter.world.candidate_sha256 != DONOR_CANDIDATE_SHA256:
        raise ValueError("materialized donor candidate differs from checkpoint")
    packet = host.composer.compose(kernel)
    prompt_tokens = count_messages(packet.message_list())
    if prompt_tokens > host.configuration.prompt_limit:
        raise ValueError("migrated E97 packet is not feasible")

    counters = RuntimeCounters(
        serialized_tokens=DONOR_SERIALIZED_TOKENS,
        provider_attempts=DONOR_PROVIDER_ATTEMPTS,
    )
    checkpoint = host.checkpoint.snapshot(
        kernel,
        counters,
        parent_checkpoint_sha256=DONOR_CHECKPOINT_SHA256,
        domain_state={
            "interaction": orchestrator.lifecycle.as_dict(),
            "trellis": adapter.snapshot(),
        },
    )
    receipt_payload = {
        "candidate_sha256": adapter.world.candidate_sha256,
        "donor_checkpoint_file_sha256": sha256_file(donor_path),
        "donor_checkpoint_sha256": DONOR_CHECKPOINT_SHA256,
        "donor_configuration_sha256": DONOR_CONFIGURATION_SHA256,
        "donor_counters": counters.as_dict(),
        "donor_events_sha256": str(donor["event_log"]["events_sha256"]),
        "excluded_terminal_event": terminal,
        "excluded_terminal_event_sha256": sha256_bytes(canonical_json_bytes(terminal)),
        "externalized_applied_effect_ids": list(reconciled.externalized_result_ids),
        "migration_kind": "verified_preterminal_state_import_under_new_manifest",
        "new_checkpoint_sha256": checkpoint["checkpoint_sha256"],
        "new_configuration_sha256": host.configuration.sha256,
        "new_execution_manifest_sha256": host.configuration.execution_manifest_sha256,
        "new_events_sha256": state.events_sha256,
        "packet_manifest_sha256": packet.manifest_sha256,
        "packet_sha256": packet.sha256,
        "pending_effect_id": EXPECTED_PENDING_EFFECT,
        "preterminal_events_sha256": before_events_sha256,
        "prompt_limit": host.configuration.prompt_limit,
        "prompt_tokens": prompt_tokens,
        "schema": "trellis-e97-donor-state-migration-receipt-v0",
        "semantic_claim": "none; exact state migration and mechanical lifecycle only",
    }
    receipt = {
        **receipt_payload,
        "migration_receipt_sha256": sha256_bytes(canonical_json_bytes(receipt_payload)),
    }
    if checkpoint_output is not None:
        write_json(checkpoint_output, checkpoint)
    if receipt_output is not None:
        write_json(receipt_output, receipt)
    return MigrationOutcome(
        host=host,
        adapter=adapter,
        orchestrator=orchestrator,
        kernel=kernel,
        counters=counters,
        checkpoint=checkpoint,
        receipt=receipt,
    )
