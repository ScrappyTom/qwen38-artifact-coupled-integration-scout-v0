#!/usr/bin/env python3
# ruff: noqa: E402
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from host_refactor.effect_lifecycle import CandidateEffectLifecycle
from host_refactor.kernel import HostKernel
from host_refactor.model import HostEvent
from host_refactor.packet import PacketComposer
from interaction_scout.lifecycle import TREATMENT_CONFIGURATION
from reactive_runtime.canonical import load_json, write_json
from tools.offline_tokenizer import OfflineTokenizer


CHECKPOINT = (
    ROOT
    / "qualification_runs"
    / "2026-08-29-trellis-refactored-interaction-continuation-v0"
    / "cells"
    / TREATMENT_CONFIGURATION
    / "tranche-002"
    / "CHECKPOINT.json"
)


def audit() -> dict[str, object]:
    checkpoint = load_json(CHECKPOINT)
    rows = checkpoint["event_log"]["events"]
    if rows[-1]["kind"] != "terminal_recorded":
        raise ValueError("E96 checkpoint lacks terminal event")
    kernel = HostKernel(tuple(HostEvent.from_dict(row) for row in rows[:-1]))
    tokenizer = OfflineTokenizer()
    composer = PacketComposer()
    before_hashes = {
        result_id: row.result.exact_content_sha256
        for result_id, row in kernel.project().results.items()
        if row.result.result_kind == "candidate_effect"
    }
    before_tokens = tokenizer.count_messages(composer.compose(kernel).message_list())
    outcome = CandidateEffectLifecycle().reconcile(kernel)
    packet = composer.compose(outcome.kernel)
    state = outcome.kernel.project()
    after_hashes = {
        result_id: row.result.exact_content_sha256
        for result_id, row in state.results.items()
        if row.result.result_kind == "candidate_effect"
    }
    return {
        "after": {
            "applied_action_receipts": sum(
                row.representation == "applied_candidate_action_receipt"
                for row in packet.manifest
            ),
            "applied_effect_receipts": sum(
                row.representation == "applied_candidate_effect_receipt"
                for row in packet.manifest
            ),
            "externalized_result_ids": list(outcome.externalized_result_ids),
            "headroom_tokens": 20_992
            - tokenizer.count_messages(packet.message_list()),
            "pending_result_ids": list(state.pending_result_ids),
            "prompt_tokens_offline": tokenizer.count_messages(
                packet.message_list()
            ),
        },
        "before": {
            "historical_reported_live_prompt_tokens": 21_041,
            "prompt_tokens_offline": before_tokens,
            "terminal": rows[-1]["data"]["code"],
        },
        "checkpoint_sha256": checkpoint["checkpoint_sha256"],
        "exact_effect_hashes_preserved": before_hashes == after_hashes,
        "historical_checkpoint_unchanged": True,
        "prompt_allowance": 20_992,
        "schema": "candidate-effect-lifecycle-offline-audit-v0",
        "semantic_uptake_inferred": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "TRELLIS_CANDIDATE_EFFECT_LIFECYCLE_AUDIT.json",
    )
    args = parser.parse_args()
    value = audit()
    write_json(args.output, value)
    print(value)


if __name__ == "__main__":
    main()
