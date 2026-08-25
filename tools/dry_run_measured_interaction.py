from __future__ import annotations

import json
import re
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import canonical_json_text, sha256_file, write_json  # noqa: E402
from reactive_runtime.boundary import PressureBoundary  # noqa: E402
from reactive_runtime.records import ResultLedger  # noqa: E402
from reactive_runtime.world import ArchitectureWorld  # noqa: E402
from reactive_runtime.tokenizer import render_qwen_messages  # noqa: E402
from tools.offline_tokenizer import OfflineTokenizer  # noqa: E402
from tools import run_measured_interaction as measured  # noqa: E402


class OfflineAdapter:
    def __init__(self) -> None:
        self.inner = OfflineTokenizer()

    def tokenize(self, content: str) -> list[int]:
        return list(range(self.inner.count_text(content)))

    def count_messages(self, messages: list[dict[str, str]]) -> tuple[int, str]:
        rendered = render_qwen_messages(messages)
        return self.inner.count_text(rendered), rendered


class ScriptedProvider:
    def __init__(self, tokenizer: OfflineAdapter) -> None:
        self.tokenizer = tokenizer
        self.configuration_id = ""
        self.actor_index = 0

    def reset(self, configuration_id: str) -> None:
        self.configuration_id = configuration_id
        self.actor_index = 0

    def _maintenance(self, messages: list[dict[str, str]]) -> str:
        allowed = sorted(set(re.findall(r"S(?:0[1-9]|1[0-6])", messages[0]["content"])))
        cited = allowed or ["S02"]
        rows = ["# Evidence Integration Ledger", ""]
        for ordinal in range(1, 13):
            source = cited[(ordinal - 1) % len(cited)]
            rows.append(
                f"R{ordinal:02d}: Cedar Valley evacuation evidence remains provisional and source-bound [{source}]."
            )
        rows.extend(
            [
                "",
                "Cross-source relationships remain subject to exact reopen, effect uptake, and candidate-bound checks.",
            ]
        )
        return "\n".join(rows)

    def _actor_actions(self) -> list[dict[str, object]]:
        grounding = " ".join(f"[S{i:02d}]" for i in range(1, 17))
        ledger = "# Evidence Integration Ledger\n\n" + "\n".join(
            f"R{i:02d}: provider-free Cedar Valley disposition {grounding}."
            for i in range(1, 13)
        )
        headings = (
            "Decision, scope, and authority",
            "Hazard triggers and zone sequencing",
            "Population, transport, and route clearance",
            "Shelter, medical, and accessibility continuity",
            "Warnings, accountability, and community support",
            "Power, fuel, and resource contracting",
            "Forty-eight-hour execution and contingencies",
            "Verification, readiness, blockers, and falsifiers",
        )
        actions: list[dict[str, object]] = [
            {
                "action": "read_batch",
                "requests": [
                    {"source_id": "S14", "start_line": 1, "end_line": 70},
                    {"source_id": "S16", "start_line": 1, "end_line": 70},
                ],
            }
        ]
        if self.configuration_id == "D0_DETACHED":
            actions.append({"action": "replace_evidence_ledger", "content": ledger})
        for heading in headings:
            actions.append(
                {
                    "action": "upsert_decision_section",
                    "heading": heading,
                    "body": " ".join(
                        [
                            "The incident commander holds legal order and closure authority, while the sheriff executes route control; the conservative 5.8-hour envelope and 42 percent wind branch govern Zone A rather than the better median.",
                            "Population and person-level transport assignments preserve survey overlap, tourists, lift capacity, driver duty, accessible medical placement, smoke-safe shelter space, oxygen handoff, and relocation triggers.",
                            "Mill Junction is the shared bottleneck at the observed 1,180 vehicles per hour; emergency inbound access, contraflow setup, door-knock timing, Hmong warnings, and radio interoperability remain explicit effects.",
                            "Twenty-four-hour local fuel or a verified alternate covers the observed nineteen-hour delay; private self-evacuation accountability, deletion proof, animal parallelism, cost authority, and candidate-bound checks govern the forty-eight-hour sequence.",
                            "Every blocker has an owner, repair, current recheck, and falsifier; a stale component result, model-authored ledger, or submission cannot establish readiness for this candidate.",
                        ]
                        * 2
                    )
                    + " [S01] [S02] [S03] [S04] [S05] [S06] [S07] [S08] [S09] [S10] [S11] [S12] [S13] [S14] [S15] [S16]",
                }
            )
        actions.extend(
            [
                {"action": "run_check"},
                {
                    "action": "upsert_decision_section",
                    "heading": "Verification, readiness, blockers, and falsifiers",
                    "body": "This candidate remains not ready while any bridge, driver, filter, radio interoperability, alternate fuel, or oxygen-matching blocker lacks a current repair and recheck. The incident commander retains closure authority; any stale result or failed falsifier blocks closure [S01] [S04] [S05] [S06] [S07] [S08] [S09] [S13] [S16].",
                },
            ]
        )
        if self.configuration_id == "A1_COUPLED":
            # Prove that the ordinary actor can revise a coupled maintenance
            # artifact after maintenance interference; coupling does not make
            # the maintenance output authoritative or immutable. The second
            # replacement is a deterministic repair after the final pending
            # source externalization can trigger one more maintenance write.
            actions.append({"action": "replace_evidence_ledger", "content": ledger})
            actions.append({"action": "replace_evidence_ledger", "content": ledger})
        actions.extend([{"action": "run_check"}, {"action": "submit"}])
        return actions

    def complete(
        self, payload: dict[str, object], custody_root: Path, *, timeout: int = 900
    ) -> dict[str, object]:
        del timeout
        messages = payload["messages"]
        assert isinstance(messages, list)
        maintenance = str(messages[0]["content"]).startswith("# EVIDENCE_INTEGRATION")
        if maintenance:
            content = self._maintenance(messages)
        else:
            actions = self._actor_actions()
            content = json.dumps(actions[min(self.actor_index, len(actions) - 1)], ensure_ascii=False)
            self.actor_index += 1
        prompt_tokens = self.tokenizer.count_messages(messages)[0]
        completion_tokens = len(self.tokenizer.tokenize(content))
        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "prompt_tokens_details": {"cached_tokens": 0},
        }
        write_json(custody_root / "request.body.json", payload)
        write_json(
            custody_root / "PROVIDER_CALL_RECEIPT.json",
            {
                "schema_version": "provider-call-custody-v1",
                "attempted": True,
                "outcome": "valid_completion_response",
                "completion_response_valid": True,
                "offline_provider": True,
            },
        )
        return {
            "content": content,
            "usage": usage,
            "finish_reason": "stop",
            "response": {"offline_provider": True},
        }


def run_fixture() -> dict[str, object]:
    tokenizer = OfflineAdapter()
    provider = ScriptedProvider(tokenizer)
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary) / "measured"
        output.mkdir()
        expected_world = ArchitectureWorld(
            ROOT / "task", Path(temporary) / "expected-initial"
        )
        expected_initial_hash = expected_world.candidate_sha256
        def synthetic_boundary(*, repository_root: Path, world: ArchitectureWorld) -> PressureBoundary:
            del repository_root
            ledger = ResultLedger()
            messages = [
                {"role": "system", "content": (ROOT / "task" / "SYSTEM.md").read_text(encoding="utf-8")},
                {"role": "user", "content": (ROOT / "task" / "TASK.md").read_text(encoding="utf-8")},
                {"role": "user", "content": (ROOT / "task" / "ACTIONS.md").read_text(encoding="utf-8") + "\n\n# Exact source catalog\n" + world.source_catalog_for_actor()},
                {"role": "user", "content": "# Exact current candidate\n" + world.candidate_packet()},
            ]
            requests = tuple((source_id, 1, 70) for source_id in ("S01", "S02", "S03", "S06", "S04", "S08", "S09", "S12", "S13", "S15"))
            for ordinal, (source_id, start, end) in enumerate(requests, 1):
                action = {"action": "read_source", "source_id": source_id, "start_line": start, "end_line": end}
                messages.append({"role": "assistant", "content": json.dumps(action, separators=(",", ":"))})
                result_id = f"RESULT-{ordinal:03d}"
                execution = world.execute(action, result_id=result_id, ledger=ledger)
                record = world.make_result_record(execution, result_id=result_id, acquired_call=ordinal)
                ledger.add(record)
                messages.append({"role": "user", "content": record.exact_content})
                record.message_index = len(messages) - 1
                if ordinal < len(requests):
                    ledger.mark_model_visible(result_id, call_index=ordinal + 1, message_index=record.message_index)
            pending = ledger.get("RESULT-010")
            return PressureBoundary(
                messages=deepcopy(messages),
                ledger=ledger,
                pending_result_id=pending.result_id,
                pending_message_index=int(pending.message_index),
                actor_calls_completed=10,
                next_result_ordinal=11,
                candidate_sha256=world.candidate_sha256,
                prospective_prompt_tokens=25_000,
                prompt_limit=measured.PROMPT_LIMIT,
            )

        with (
            patch.object(measured, "verify_runtime_assets", return_value={"passed": True, "failures": []}),
            patch.object(measured, "start_server", return_value=(None, None, None, {"passed": True})),
            patch.object(measured, "LiveTokenizer", return_value=tokenizer),
            patch.object(measured, "complete_custodied", side_effect=provider.complete),
            patch.object(measured, "hydrate_pressure_boundary", side_effect=synthetic_boundary),
        ):
            for configuration_id in measured.CONFIGURATION_ORDER:
                provider.reset(configuration_id)
                rows.append(measured.run_cell(configuration_id, output))
        initial = {
            configuration_id: json.loads(
                (output / "cells" / configuration_id / "INITIAL_CONTINUATION_STATE.json").read_text(
                    encoding="utf-8"
                )
            )
            for configuration_id in measured.CONFIGURATION_ORDER
        }
    failures: list[str] = []
    by_id = {str(row["configuration_id"]): row for row in rows}
    for configuration_id, row in by_id.items():
        if row["terminal_disposition"] != "submitted":
            failures.append(f"terminal:{configuration_id}")
        if int(row["accepted_integration_updates"]) < 1:
            failures.append(f"maintenance:{configuration_id}")
        if int(row["externalization_count"]) < 1:
            failures.append(f"relief:{configuration_id}")
        if int(row["check_count"]) != 2:
            failures.append(f"checks:{configuration_id}")
        if int(row["candidate_effects_delivered"]) < 1:
            failures.append(f"effect_uptake:{configuration_id}")
        mechanical = row["mechanical_final_evaluation"]["projection"]
        if mechanical["closure_readiness"] != "not_adjudicated":
            failures.append(f"mechanical_precheck:{configuration_id}")
        if mechanical["blocking_requirements"] != [
            "independent condition-blinded semantic adjudication required"
        ]:
            failures.append(f"mechanical_blockers:{configuration_id}")
        budget = row["trajectory_budget"]
        if budget["milestone_call"] is None or budget["remaining_calls_in_current_window"] < 1:
            failures.append(f"postconstruction_tail:{configuration_id}")
    if initial["D0_DETACHED"]["candidate_sha256"] != expected_initial_hash:
        failures.append("detached_maintenance_mutated_candidate")
    if initial["A1_COUPLED"]["candidate_sha256"] == expected_initial_hash:
        failures.append("coupled_maintenance_did_not_mutate_candidate")
    return {
        "schema": "cedar-artifact-coupling-measured-provider-free-fixture-v0",
        "passed": not failures,
        "failures": failures,
        "offline_provider_only": True,
        "gpu_authorized": False,
        "working_tree_base_commit_at_generation": measured.git_commit(),
        "exact_apparatus_file_hashes": {
            "tools/dry_run_measured_interaction.py": sha256_file(ROOT / "tools" / "dry_run_measured_interaction.py"),
            "tools/run_measured_interaction.py": sha256_file(ROOT / "tools" / "run_measured_interaction.py"),
            "task/TASK_SOURCE_LOCK.json": sha256_file(ROOT / "task" / "TASK_SOURCE_LOCK.json"),
            "MEASURED_INTERACTION_CONTRACT.json": sha256_file(ROOT / "MEASURED_INTERACTION_CONTRACT.json"),
        },
        "initial_continuation": initial,
        "cells": rows,
    }


def main() -> int:
    result = run_fixture()
    write_json(ROOT / "STAGE0_MEASURED_FIXTURE.json", result)
    print(canonical_json_text(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
