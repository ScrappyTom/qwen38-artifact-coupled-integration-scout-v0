from __future__ import annotations

import json
from pathlib import Path

import pytest

from host_refactor.effect_lifecycle import VerificationResidencyLifecycle
from host_refactor.kernel import HostKernel, InvalidTransition
from host_refactor.lifecycle_scout.adapter import LifecycleScoutAdapter
from host_refactor.model import DeliveryState, ExactStateObject, HostEvent
from host_refactor.packet import PacketComposer
from host_refactor.trellis_adapter import trellis_spec
from interaction_scout.lifecycle import _verification_state
from reactive_runtime.canonical import load_json
from tools.offline_tokenizer import OfflineTokenizer


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = (
    ROOT
    / "qualification_runs"
    / "2026-08-30-trellis-e99-verification-lifecycle-continuation-v1"
    / "tranche-002"
    / "CHECKPOINT.json"
)


def _e103_preterminal() -> tuple[dict, HostKernel]:
    checkpoint = load_json(CHECKPOINT)
    rows = checkpoint["event_log"]["events"]
    assert rows[-1]["kind"] == "terminal_recorded"
    return checkpoint, HostKernel(tuple(HostEvent.from_dict(row) for row in rows[:-1]))


def _bound_kernel(tmp_path: Path) -> HostKernel:
    checkpoint, kernel = _e103_preterminal()
    tokenizer = OfflineTokenizer()
    adapter = LifecycleScoutAdapter.from_snapshot(
        spec=trellis_spec(ROOT),
        trajectory_root=tmp_path / "trajectory",
        snapshot=checkpoint["domain_state"]["trellis"],
        count_text=tokenizer.count_text,
    )
    return kernel.set_state_object(_verification_state(adapter, kernel))


def test_e103_checks_turn_over_only_after_exact_verification_binding(
    tmp_path: Path,
) -> None:
    kernel = _bound_kernel(tmp_path)
    outcome = VerificationResidencyLifecycle().reconcile(kernel)
    state = outcome.kernel.project()

    assert outcome.externalized_result_ids == ("RESULT-021", "RESULT-024")
    assert outcome.represented_check_result_id == "RESULT-024"
    assert state.results["RESULT-021"].delivery_state is DeliveryState.DELIVERED_EXTERNAL
    assert state.results["RESULT-024"].delivery_state is DeliveryState.DELIVERED_EXTERNAL
    assert state.results["RESULT-026"].delivery_state is DeliveryState.PENDING
    representations = {
        row.result_id: row.representation
        for row in PacketComposer().compose(outcome.kernel).manifest
        if row.result_id in {"RESULT-021", "RESULT-024", "RESULT-026"}
    }
    assert representations == {
        "RESULT-021": "exact_receipt",
        "RESULT-024": "exact_receipt",
        "RESULT-026": "pending_exact_body",
    }


def test_check_turnover_fails_closed_on_state_binding_tamper(tmp_path: Path) -> None:
    kernel = _bound_kernel(tmp_path)
    slot = kernel.project().state_slots["current_verification_frame"]
    content = json.loads(slot.exact_content)
    content["check_result_binding"]["exact_result_sha256"] = "0" * 64
    broken = kernel.set_state_object(
        ExactStateObject(
            slot_id=slot.slot_id,
            object_id=slot.object_id,
            object_version="tampered",
            exact_content=json.dumps(content, separators=(",", ":"), sort_keys=True),
            metadata=slot.metadata,
        )
    )
    with pytest.raises(InvalidTransition, match="binding mismatch"):
        VerificationResidencyLifecycle().reconcile(broken)


def test_externalized_check_remains_exactly_reopenable(tmp_path: Path) -> None:
    bounded = VerificationResidencyLifecycle().reconcile(
        _bound_kernel(tmp_path)
    ).kernel
    delivered = bounded.complete_invocation(
        call_index=27,
        included_result_ids=("RESULT-026",),
        request_sha256="request-27",
        response_sha256="response-27",
    )
    reopened = delivered.request_reopen(
        "RESULT-024",
        call_index=28,
        transcript_entry_id="TEST-REOPEN-RESULT-024",
    )
    assert any(
        row.result_id == "RESULT-024" and row.representation == "pending_exact_body"
        for row in PacketComposer().compose(reopened).manifest
    )


def test_published_e104_reconciliation_passes() -> None:
    result = load_json(ROOT / "E104_VERIFICATION_RESIDENCY_RECONCILIATION.json")
    assert result["passed"] is True
    assert result["gpu_model_calls"] == 0
    assert result["prospective_projection"]["prompt_tokens"] <= 20_992
    assert result["provider_free_full_lifecycle_fixture"]["submitted"] is True
