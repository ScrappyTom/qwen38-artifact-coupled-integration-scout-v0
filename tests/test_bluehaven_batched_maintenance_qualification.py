from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from pathlib import Path

from reactive_runtime.bluehaven_boundary import (
    hydrate_bluehaven_pressure_boundary,
    verify_bluehaven_pressure_handoff,
)
from reactive_runtime.bluehaven_qualification import (
    build_bluehaven_maintenance_cases,
    deterministic_replacement_prior,
)
from reactive_runtime.integration import (
    BATCHED_INTEGRATION_PROVIDER_MAX_TOKENS,
    BATCHED_INTEGRATION_TOKEN_BUDGET,
    validate_integration,
)
from reactive_runtime.world import ArchitectureWorld
from tools import run_bluehaven_batched_maintenance_qualification as runner
from tools.offline_tokenizer import OfflineTokenizer


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "task_bluehaven"


class BluehavenBatchedMaintenanceQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preflight = json.loads(
            (
                ROOT / "BLUEHAVEN_BATCHED_MAINTENANCE_QUALIFICATION_PREFLIGHT.json"
            ).read_text(encoding="utf-8")
        )
        cls.contract = json.loads(
            (
                ROOT / "BLUEHAVEN_BATCHED_MAINTENANCE_QUALIFICATION_CONTRACT.json"
            ).read_text(encoding="utf-8")
        )
        cls.cases = build_bluehaven_maintenance_cases(ROOT)

    def test_exact_pressure_handoff_verifies_and_hydrates(self) -> None:
        handoff = verify_bluehaven_pressure_handoff(ROOT)
        self.assertEqual("RESULT-006", handoff["pending_result_id"])
        with tempfile.TemporaryDirectory() as temporary:
            world = ArchitectureWorld(TASK, Path(temporary))
            boundary = hydrate_bluehaven_pressure_boundary(
                repository_root=ROOT,
                world=world,
            )
        self.assertEqual(6, boundary.actor_calls_completed)
        self.assertEqual(7, boundary.next_result_ordinal)
        self.assertEqual("RESULT-006", boundary.pending_result_id)
        self.assertEqual(23_820, boundary.prospective_prompt_tokens)
        self.assertEqual(20_992, boundary.prompt_limit)

    def test_two_cases_use_exact_nonoverlapping_boundary_results(self) -> None:
        self.assertEqual(2, len(self.cases))
        self.assertEqual(
            ("RESULT-001", "RESULT-002", "RESULT-003"),
            self.cases[0].input_result_ids,
        )
        self.assertEqual(
            ("RESULT-004", "RESULT-005", "RESULT-006"),
            self.cases[1].input_result_ids,
        )
        self.assertEqual(tuple(f"S{i:02d}" for i in range(1, 7)), self.cases[0].allowed_source_ids)
        self.assertEqual(tuple(f"S{i:02d}" for i in range(1, 13)), self.cases[1].allowed_source_ids)
        self.assertIsNone(self.cases[0].prior)
        self.assertIsNotNone(self.cases[1].prior)

    def test_frozen_prior_is_bounded_and_non_authorizing(self) -> None:
        tokenizer = OfflineTokenizer()
        prior = deterministic_replacement_prior()
        validation = validate_integration(
            prior.body,
            count_text=tokenizer.count_text,
            allowed_source_ids=prior.observed_source_ids,
            token_budget=BATCHED_INTEGRATION_TOKEN_BUDGET,
        )
        self.assertTrue(validation.valid, validation.issues)
        self.assertLess(validation.output_tokens, BATCHED_INTEGRATION_TOKEN_BUDGET)

    def test_exact_case_geometry_matches_preflight(self) -> None:
        tokenizer = OfflineTokenizer()
        expected = {row["case_id"]: row for row in self.preflight["case_geometry"]}
        for case in self.cases:
            prompt = tokenizer.count_messages(case.messages)
            row = expected[case.case_id]
            self.assertEqual(row["prompt_tokens"], prompt)
            self.assertEqual(
                row["headroom_after_max_completion"],
                25_088 - prompt - BATCHED_INTEGRATION_PROVIDER_MAX_TOKENS,
            )
            self.assertTrue(row["fits"])

    def test_contract_runner_and_inert_request_agree(self) -> None:
        request = json.loads(
            (
                ROOT / "BLUEHAVEN_BATCHED_MAINTENANCE_AUTHORIZATION_REQUEST.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(runner.RUN_ID, self.contract["run_id"])
        self.assertEqual(runner.SCOPE, self.contract["scope"])
        self.assertEqual(runner.MAX_CALLS, self.contract["maximum_model_calls"])
        self.assertEqual(2, runner.MAX_CALLS)
        self.assertEqual(
            BATCHED_INTEGRATION_TOKEN_BUDGET,
            self.contract["admission_body_tokens"],
        )
        self.assertEqual(
            BATCHED_INTEGRATION_PROVIDER_MAX_TOKENS,
            self.contract["provider_max_completion_tokens"],
        )
        self.assertFalse(request["authorized"])
        self.assertEqual(runner.RUN_ID, request["run_id"])
        self.assertEqual(runner.SCOPE, request["scope"])
        self.assertFalse(self.contract["measured_continuation_authorized"])

    def test_qualification_runner_contains_no_actor_or_measured_continuation(self) -> None:
        source = inspect.getsource(runner)
        self.assertIn("build_bluehaven_maintenance_cases", source)
        self.assertIn("validate_integration", source)
        self.assertNotIn("bluehaven_actor_actions", source)
        self.assertNotIn("world.execute", source)
        self.assertNotIn("run_cell", source)


if __name__ == "__main__":
    unittest.main()
