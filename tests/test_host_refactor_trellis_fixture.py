from __future__ import annotations

import json
import unittest
from pathlib import Path

from host_refactor.model import DeliveryState
from host_refactor.capacity import CapacityManager
from host_refactor.packet import PacketComposer
from host_refactor.trellis_fixture import (
    RUN_ID,
    build_e83_kernel,
    complete_e83_pending,
    delivered_source_ids,
    pending_source_ids,
)
from tools.offline_tokenizer import OfflineTokenizer


ROOT = Path(__file__).resolve().parents[1]


class TrellisRefactorFixtureTests(unittest.TestCase):
    def test_e83_replay_preserves_six_delivered_and_two_pending_sources(self) -> None:
        kernel = build_e83_kernel(ROOT)
        self.assertEqual(
            delivered_source_ids(kernel),
            ("CLIMATE", "CLINIC", "COUNCIL", "GRID", "SHELTER", "WATER"),
        )
        self.assertEqual(pending_source_ids(kernel), ("COMMS", "TRANSIT"))
        self.assertEqual(
            kernel.project().results["RESULT-007"].delivery_state,
            DeliveryState.PENDING,
        )

    def test_e83_next_packet_matches_frozen_live_messages(self) -> None:
        kernel = build_e83_kernel(ROOT)
        packet = PacketComposer().compose(kernel)
        historical = json.loads(
            (ROOT / "runs" / RUN_ID / "FINAL_MESSAGES.json").read_text(encoding="utf-8")
        )
        self.assertEqual(packet.message_list(), historical)

    def test_completed_next_invocation_delivers_pending_sources(self) -> None:
        kernel = complete_e83_pending(ROOT)
        self.assertEqual(
            delivered_source_ids(kernel),
            (
                "CLIMATE",
                "CLINIC",
                "COMMS",
                "COUNCIL",
                "GRID",
                "SHELTER",
                "TRANSIT",
                "WATER",
            ),
        )
        self.assertEqual(pending_source_ids(kernel), ())

    def test_common_relief_admits_e83_pending_packet_without_activation_gate(
        self,
    ) -> None:
        kernel = build_e83_kernel(ROOT)
        tokenizer = OfflineTokenizer()
        composer = PacketComposer()
        ordinary = tokenizer.count_messages(composer.compose(kernel).message_list())
        self.assertEqual(ordinary, 21_401)
        outcome = CapacityManager(
            composer=composer,
            count_messages=tokenizer.count_messages,
            prompt_limit=20_992,
        ).ensure_feasible(
            kernel,
            protected_result_ids=kernel.project().pending_result_ids,
        )
        self.assertTrue(outcome.feasible)
        self.assertEqual(outcome.selected_result_ids, ("RESULT-001",))
        self.assertLessEqual(outcome.prompt_tokens, 20_992)


if __name__ == "__main__":
    unittest.main()
