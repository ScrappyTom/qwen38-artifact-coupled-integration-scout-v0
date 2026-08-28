from __future__ import annotations

# ruff: noqa: E402

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from host_refactor.capacity import CapacityManager
from host_refactor.checkpoint import CheckpointController, RuntimeCounters
from host_refactor.model import RunConfiguration
from host_refactor.packet import PacketComposer
from host_refactor.trellis_fixture import (
    build_e83_kernel,
    delivered_source_ids,
    pending_source_ids,
)
from tools.offline_tokenizer import OfflineTokenizer


def replay(repository_root: Path) -> dict[str, object]:
    kernel = build_e83_kernel(repository_root)
    tokenizer = OfflineTokenizer()
    composer = PacketComposer()
    manager = CapacityManager(
        composer=composer,
        count_messages=tokenizer.count_messages,
        prompt_limit=20_992,
    )
    outcome = manager.ensure_feasible(
        kernel,
        protected_result_ids=kernel.project().pending_result_ids,
    )
    config = RunConfiguration(
        run_id="e83-provider-free-refactor-replay",
        task_id="trellis-heat-continuity-decision-v0",
        seed=884_219,
        context_window=25_088,
        response_reserve=4_096,
        execution_manifest_sha256="a" * 64,
    )
    review = CheckpointController(config).review_packet(
        outcome.kernel,
        RuntimeCounters(),
        composer,
    )
    return {
        "delivered_source_ids": list(delivered_source_ids(kernel)),
        "events_sha256": kernel.project().events_sha256,
        "ordinary_prompt_tokens": tokenizer.count_messages(
            composer.compose(kernel).message_list()
        ),
        "pending_source_ids": list(pending_source_ids(kernel)),
        "relief_feasible": outcome.feasible,
        "relief_prompt_tokens": outcome.prompt_tokens,
        "relief_result_ids": list(outcome.selected_result_ids),
        "review_packet": review,
        "schema": "trellis-host-refactor-provider-free-replay-v0",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(replay(args.repository_root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
