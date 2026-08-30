from __future__ import annotations

# ruff: noqa: E402

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from host_refactor.effect_lifecycle import VerificationResidencyLifecycle
from host_refactor.kernel import HostKernel
from host_refactor.lifecycle_scout.adapter import LifecycleScoutAdapter
from host_refactor.packet import PacketComposer
from host_refactor.trellis_adapter import trellis_spec
from interaction_scout.lifecycle import _verification_state
from interaction_scout.provider_free import run_provider_free_lifecycle
from reactive_runtime.canonical import (
    canonical_json_text,
    load_json,
    sha256_bytes,
    sha256_file,
    write_json,
)
from tools.offline_tokenizer import OfflineTokenizer


RUN_ROOT = (
    ROOT
    / "qualification_runs"
    / "2026-08-30-trellis-e99-verification-lifecycle-continuation-v1"
)
CHECKPOINT = RUN_ROOT / "tranche-002" / "CHECKPOINT.json"
OUTPUT = ROOT / "E104_VERIFICATION_RESIDENCY_RECONCILIATION.json"


def _preterminal_kernel(checkpoint: dict[str, Any]) -> HostKernel:
    events = list(checkpoint["event_log"]["events"])
    if not events or events[-1]["kind"] != "terminal_recorded":
        raise ValueError("E103 checkpoint does not end at the capacity terminal")
    return HostKernel.from_dict(
        {
            "events": events[:-1],
            "schema": "bounded-host-event-log-v0",
        }
    )


def _marginal_tokens(
    tokenizer: OfflineTokenizer,
    packet_messages: list[dict[str, str]],
    manifest_entries: list[dict[str, Any]],
    selected_ids: set[str],
) -> list[dict[str, Any]]:
    full = tokenizer.count_messages(packet_messages)
    rows: list[dict[str, Any]] = []
    for entry in manifest_entries:
        entry_id = str(entry["transcript_entry_id"])
        result_id = entry.get("result_id")
        state_slot_id = entry.get("state_slot_id")
        if (
            entry_id not in selected_ids
            and result_id not in selected_ids
            and state_slot_id not in selected_ids
        ):
            continue
        index = int(entry["message_index"])
        without = packet_messages[:index] + packet_messages[index + 1 :]
        without_tokens = tokenizer.count_messages(without)
        rows.append(
            {
                "marginal_tokens_in_exact_packet": full - without_tokens,
                "representation": entry["representation"],
                "result_id": result_id,
                "state_slot_id": state_slot_id,
                "transcript_entry_id": entry_id,
            }
        )
    return rows


def _provider_free_fixture(tokenizer: OfflineTokenizer) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temp:
        result = run_provider_free_lifecycle(
            ROOT,
            configuration_id="V1_TEMPORARY_PROVENANCE_SCAFFOLD",
            output_root=Path(temp),
        )
        reconciled = VerificationResidencyLifecycle().reconcile(result["kernel"])
        state = reconciled.kernel.project()
        check_rows = [
            row
            for row in state.results.values()
            if row.result.result_kind == "check_observation"
        ]
        latest = max(
            check_rows,
            key=lambda row: (row.result.acquired_call, row.result.result_id),
        )
        packet = PacketComposer().compose(reconciled.kernel)
        return {
            "completed": state.terminal is not None
            and state.terminal.value == "completed",
            "current_check_passed": bool(
                latest.result.metadata["check_projection"]["passed"]
            ),
            "delivered_external_check_ids": sorted(
                row.result.result_id
                for row in check_rows
                if row.delivery_state.value == "delivered_external"
            ),
            "final_candidate_sha256": result["adapter"].world.candidate_sha256,
            "model_calls": 0,
            "next_packet_tokens": tokenizer.count_messages(packet.message_list()),
            "submitted": result["adapter"].world.submitted,
        }


def audit() -> dict[str, Any]:
    tokenizer = OfflineTokenizer()
    checkpoint = load_json(CHECKPOINT)
    kernel = _preterminal_kernel(checkpoint)
    composer = PacketComposer()
    historical = composer.compose(kernel)
    historical_tokens = tokenizer.count_messages(historical.message_list())

    with tempfile.TemporaryDirectory() as temp:
        adapter = LifecycleScoutAdapter.from_snapshot(
            spec=trellis_spec(ROOT),
            trajectory_root=Path(temp),
            snapshot=checkpoint["domain_state"]["trellis"],
            count_text=tokenizer.count_text,
        )
        bound = _verification_state(adapter, kernel)
    kernel = kernel.set_state_object(bound)
    bound_packet = composer.compose(kernel)
    bound_tokens = tokenizer.count_messages(bound_packet.message_list())
    outcome = VerificationResidencyLifecycle().reconcile(kernel)
    projected = composer.compose(outcome.kernel)
    projected_tokens = tokenizer.count_messages(projected.message_list())
    state = outcome.kernel.project()

    pending = state.results["RESULT-026"]
    represented = state.results["RESULT-024"]
    packet_manifest = projected.manifest_dict()
    representations = {
        str(row.get("result_id")): row["representation"]
        for row in packet_manifest["entries"]
        if row.get("result_id") is not None
    }
    selected = {
        "RESULT-020",
        "RESULT-021",
        "HOST-ACTION-REJECTION-000022",
        "RESULT-024",
        "HOST-ACTION-REJECTION-000025",
        "RESULT-026",
        "current_candidate",
        "current_candidate_effect",
        "current_verification_frame",
    }
    donor_v007 = (
        ROOT
        / "qualification_runs"
        / "2026-08-29-trellis-e99-verification-lifecycle-scout-v1"
        / "trajectory"
        / "candidate_versions"
        / "version-007"
        / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
    ).read_text(encoding="utf-8")
    donor_v008 = (
        ROOT
        / "qualification_runs"
        / "2026-08-29-trellis-e99-verification-lifecycle-scout-v1"
        / "trajectory"
        / "candidate_versions"
        / "version-008"
        / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
    ).read_text(encoding="utf-8")

    failures: list[str] = []
    if projected_tokens > 20_992:
        failures.append("verification_turnover_does_not_restore_feasibility")
    if outcome.externalized_result_ids != ("RESULT-021", "RESULT-024"):
        failures.append("unexpected_check_turnover_set")
    if pending.delivery_state.value != "pending":
        failures.append("pending_effect_not_preserved")
    if representations.get("RESULT-026") != "pending_exact_body":
        failures.append("pending_effect_not_exact_in_packet")
    if representations.get("RESULT-024") != "exact_receipt":
        failures.append("represented_check_not_receipt")
    bound_content = json.loads(bound.exact_content)
    if bound_content["check_result_binding"] != {
        "check_projection_sha256": sha256_bytes(
            canonical_json_text(
                represented.result.metadata["check_projection"]
            ).encode("utf-8")
        ),
        "evaluated_candidate_sha256": represented.result.evaluated_candidate_sha256,
        "exact_result_sha256": represented.result.exact_content_sha256,
        "reopen_action": {"action": "reopen_exact", "result_id": "RESULT-024"},
        "result_id": "RESULT-024",
    }:
        failures.append("represented_check_hash_binding_invalid")
    if donor_v007.count("\n## ") != 6 or "[REVIEW].## " in donor_v007:
        failures.append("donor_v007_not_structurally_clean")
    if "[REVIEW].## " not in donor_v008:
        failures.append("donor_v008_corruption_not_detected")

    fixture = _provider_free_fixture(tokenizer)
    if not all(
        (
            fixture["completed"],
            fixture["current_check_passed"],
            fixture["submitted"],
            bool(fixture["delivered_external_check_ids"]),
        )
    ):
        failures.append("provider_free_lifecycle_fixture_failed")

    result = {
        "schema": "trellis-verification-residency-reconciliation-v0",
        "passed": not failures,
        "failures": failures,
        "gpu_model_calls": 0,
        "historical_boundary": {
            "checkpoint_sha256": checkpoint["checkpoint_sha256"],
            "checkpoint_file_sha256": sha256_file(CHECKPOINT),
            "prompt_limit": 20_992,
            "live_authoritative_prompt_tokens": 21_318,
            "live_authoritative_deficit_tokens": 326,
            "offline_prompt_tokens": historical_tokens,
            "observed_live_minus_offline_tokens": 21_318 - historical_tokens,
            "pending_result_ids": list(kernel.project().pending_result_ids),
        },
        "prospective_projection": {
            "binding_only_prompt_tokens": bound_tokens,
            "externalized_check_result_ids": list(
                outcome.externalized_result_ids
            ),
            "headroom_tokens": 20_992 - projected_tokens,
            "conservative_headroom_if_observed_live_delta_repeats": (
                20_992 - projected_tokens - (21_318 - historical_tokens)
            ),
            "prompt_tokens": projected_tokens,
            "represented_check_result_id": outcome.represented_check_result_id,
            "result_representations": {
                result_id: representations.get(result_id)
                for result_id in (
                    "RESULT-021",
                    "RESULT-024",
                    "RESULT-026",
                )
            },
        },
        "exact_packet_marginals": _marginal_tokens(
            tokenizer,
            historical.message_list(),
            historical.manifest_dict()["entries"],
            selected,
        ),
        "donor_import_eligibility": {
            "donor_derived_checkpoint_fixture_eligible": False,
            "exact_uncorrupted_candidate_available": "version-007",
            "reason": (
                "version-007 exact artifact bytes are preserved, but no sealed "
                "checkpoint exists at that state; the next sealed checkpoint is "
                "version-008 and already contains the glued-heading corruption"
            ),
            "version_007_heading_count": donor_v007.count("\n## "),
            "version_007_hidden_glued_heading": "[REVIEW].## " in donor_v007,
            "version_008_hidden_glued_heading": "[REVIEW].## " in donor_v008,
            "rule": "do not invent a donor checkpoint from artifact bytes alone",
        },
        "provider_free_full_lifecycle_fixture": fixture,
        "claim_limit": (
            "This qualifies mechanical check turnover and a provider-free complete "
            "lifecycle; it does not establish live actor orientation, repair quality, "
            "or closure utility."
        ),
    }
    return result


def main() -> int:
    result = audit()
    write_json(OUTPUT, result)
    if not result["passed"]:
        raise RuntimeError(f"E104 reconciliation failed: {result['failures']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
