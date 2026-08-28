from __future__ import annotations

import tempfile
import json
import unittest
from pathlib import Path

from host_refactor.checkpoint import CheckpointController, RuntimeCounters
from host_refactor.trellis_adapter import build_trellis_host, trellis_spec
from host_refactor.trellis_adapter import TrellisDomainAdapter
from tools.offline_tokenizer import OfflineTokenizer


ROOT = Path(__file__).resolve().parents[1]


class TrellisAdapterTests(unittest.TestCase):
    def test_selected_path_contains_no_legacy_visibility_mutation(self) -> None:
        selected = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / "host_refactor").glob("*.py"))
        )
        self.assertNotIn("mark_model_visible(", selected)
        self.assertNotIn(".resident =", selected)
        self.assertNotIn(".message_index =", selected)
        self.assertNotIn("runner.RUN_ID =", selected)

    def test_spec_is_immutable_and_does_not_mutate_historical_runner(self) -> None:
        from tools import run_solace_pressure_screen as historical

        before = {
            "RUN_ID": historical.RUN_ID,
            "TASK_ID": historical.TASK_ID,
            "SEED": historical.SEED,
            "TASK": historical.TASK,
        }
        spec = trellis_spec(ROOT)
        after = {
            "RUN_ID": historical.RUN_ID,
            "TASK_ID": historical.TASK_ID,
            "SEED": historical.SEED,
            "TASK": historical.TASK,
        }
        self.assertEqual(after, before)
        self.assertEqual(
            spec.configuration.task_id, "trellis-heat-continuity-decision-v0"
        )
        self.assertEqual(spec.configuration.tranche_calls, 12)
        self.assertEqual(spec.configuration.maximum_calls, 60)

    def test_thin_host_builds_without_provider_or_global_reconfiguration(self) -> None:
        tokenizer = OfflineTokenizer()
        with tempfile.TemporaryDirectory() as temp:
            host, adapter, kernel = build_trellis_host(
                repository_root=ROOT,
                trajectory_root=Path(temp) / "trajectory",
                count_messages=tokenizer.count_messages,
                count_text=tokenizer.count_text,
            )
            packet = host.composer.compose(kernel)
        self.assertEqual(len(packet.messages), 4)
        self.assertEqual(adapter.world.phase, "construction")
        self.assertIn("current_candidate", kernel.project().state_slots)
        self.assertEqual(
            packet.manifest[-1].representation,
            "current_exact_state",
        )
        self.assertLess(tokenizer.count_messages(packet.message_list()), 20_992)
        self.assertIn("read_batch", adapter.allowed_actions)

    def test_domain_state_is_exactly_checkpointed_and_hydrated(self) -> None:
        tokenizer = OfflineTokenizer()
        spec = trellis_spec(ROOT)
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            host, adapter, kernel = build_trellis_host(
                repository_root=ROOT,
                trajectory_root=temp_root / "first",
                count_messages=tokenizer.count_messages,
                count_text=tokenizer.count_text,
            )
            adapter.next_result_index = 7
            checkpoint = CheckpointController(spec.configuration).snapshot(
                kernel,
                RuntimeCounters(serialized_tokens=123, provider_attempts=4),
                domain_state=adapter.snapshot(),
            )
            hydrated_kernel, counters, domain_state = (
                CheckpointController.hydrate_with_domain(
                    checkpoint,
                    spec.configuration,
                )
            )
            self.assertIsNotNone(domain_state)
            resumed = TrellisDomainAdapter.from_snapshot(
                spec=spec,
                trajectory_root=temp_root / "resumed",
                snapshot=domain_state or {},
                count_text=tokenizer.count_text,
            )
            self.assertEqual(resumed.next_result_index, 7)
            self.assertEqual(
                resumed.world.candidate_packet(), adapter.world.candidate_packet()
            )
        self.assertEqual(hydrated_kernel.as_dict(), kernel.as_dict())
        self.assertEqual(counters.serialized_tokens, 123)

    def test_provider_free_thin_runner_deduplicates_repeated_trellis_read(self) -> None:
        tokenizer = OfflineTokenizer()
        action = json.dumps(
            {
                "action": "read_batch",
                "requests": [{"end_line": 20, "source_id": "COUNCIL", "start_line": 1}],
            }
        )

        def complete(_payload):
            return {
                "content": action,
                "finish_reason": "stop",
                "usage": {
                    "completion_tokens": 20,
                    "prompt_tokens": 1_000,
                    "total_tokens": 1_020,
                },
            }

        with tempfile.TemporaryDirectory() as temp:
            host, adapter, kernel = build_trellis_host(
                repository_root=ROOT,
                trajectory_root=Path(temp) / "trajectory",
                count_messages=tokenizer.count_messages,
                count_text=tokenizer.count_text,
            )
            from host_refactor.checkpoint import RuntimeCounters

            first = host.step(
                kernel=kernel,
                counters=RuntimeCounters(),
                provider_complete=complete,
                domain=adapter,
            )
            second = host.step(
                kernel=first.kernel,
                counters=first.counters,
                provider_complete=complete,
                domain=adapter,
            )
            packet = host.composer.compose(second.kernel)
        state = second.kernel.project()
        self.assertEqual(tuple(state.results), ("RESULT-001",))
        self.assertEqual(state.results["RESULT-001"].demand_count, 2)
        contents = "\n".join(row["content"] for row in packet.messages)
        self.assertEqual(contents.count("--- exact result body ---"), 1)
        self.assertIn('"status":"already_resident"', contents)

    def test_candidate_mutation_replaces_exact_current_state_slot(self) -> None:
        tokenizer = OfflineTokenizer()
        action = json.dumps(
            {
                "action": "replace_evidence_ledger",
                "content": "# Evidence Integration Ledger\n\nExact bounded work.\n",
            }
        )

        def complete(_payload):
            return {
                "content": action,
                "finish_reason": "stop",
                "usage": {
                    "completion_tokens": 20,
                    "prompt_tokens": 1_000,
                    "total_tokens": 1_020,
                },
            }

        with tempfile.TemporaryDirectory() as temp:
            host, adapter, kernel = build_trellis_host(
                repository_root=ROOT,
                trajectory_root=Path(temp) / "trajectory",
                count_messages=tokenizer.count_messages,
                count_text=tokenizer.count_text,
            )
            initial = kernel.project().state_slots["current_candidate"]
            from host_refactor.checkpoint import RuntimeCounters

            step = host.step(
                kernel=kernel,
                counters=RuntimeCounters(),
                provider_complete=complete,
                domain=adapter,
            )
            current = step.kernel.project().state_slots["current_candidate"]
            packet = host.composer.compose(step.kernel)
        self.assertNotEqual(current.object_version, initial.object_version)
        self.assertIn("Exact bounded work.", current.exact_content)
        self.assertEqual(
            [
                row["content"]
                for row, manifest in zip(packet.messages, packet.manifest)
                if manifest.state_slot_id == "current_candidate"
            ],
            [current.exact_content],
        )


if __name__ == "__main__":
    unittest.main()
