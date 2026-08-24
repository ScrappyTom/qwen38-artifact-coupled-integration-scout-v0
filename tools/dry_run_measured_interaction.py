from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import canonical_json_text, write_json  # noqa: E402
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
        allowed = sorted(set(__import__("re").findall(r"S(?:0[1-9]|1[0-4])", messages[0]["content"])))
        cited = allowed or ["S02"]
        rows = ["# Evidence Integration Ledger", ""]
        for ordinal in range(1, 13):
            source = cited[(ordinal - 1) % len(cited)]
            rows.append(
                f"R{ordinal:02d}: bounded integration remains provisional and source-bound [{source}]."
            )
        rows.extend(
            [
                "",
                "Cross-source relationships remain subject to exact reopen and candidate-bound checks.",
            ]
        )
        return "\n".join(rows)

    def _actor_actions(self) -> list[dict[str, object]]:
        ledger = "# Evidence Integration Ledger\n\n" + "\n".join(
            f"R{i:02d}: provider-free fixture disposition [S02] [S03]."
            for i in range(1, 13)
        )
        headings = (
            "Decision and scope",
            "Earned mechanical substrate",
            "Information interactions and failure migration",
            "State, relationships, chronology, and control",
            "Runtime policy",
            "Experimental roadmap",
            "Verification, readiness, and governance",
            "Uncertainties and falsifiers",
        )
        actions: list[dict[str, object]] = [
            {
                "action": "read_batch",
                "requests": [
                    {"source_id": "S12", "start_line": 1, "end_line": 120},
                    {"source_id": "S14", "start_line": 1, "end_line": 120},
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
                    "body": (
                        "The bounded interaction scout preserves exact custody, delivery, effect uptake, "
                        "cache and decision cost, host and model demand, evaluation, uncertainty, and "
                        "falsifiable stopping rules [S02] [S03] [S04] [S08] [S13]."
                    ),
                }
            )
        actions.extend(
            [
                {"action": "run_check"},
                {
                    "action": "upsert_decision_section",
                    "heading": "Uncertainties and falsifiers",
                    "body": "The candidate remains uncertain and falsifiable under fresh transfer [S02] [S13].",
                },
                {"action": "run_check"},
                {"action": "submit"},
            ]
        )
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
        with (
            patch.object(measured, "verify_runtime_assets", return_value={"passed": True, "failures": []}),
            patch.object(measured, "start_server", return_value=(None, None, None, {"passed": True})),
            patch.object(measured, "LiveTokenizer", return_value=tokenizer),
            patch.object(measured, "complete_custodied", side_effect=provider.complete),
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
    boundary_hash = "eb63671008e22987e37ff1ebc26a8ddb29f92ec55ee1d3d1ad0d7d1d64ae181e"
    if initial["D0_DETACHED"]["candidate_sha256"] != boundary_hash:
        failures.append("detached_maintenance_mutated_candidate")
    if initial["A1_COUPLED"]["candidate_sha256"] == boundary_hash:
        failures.append("coupled_maintenance_did_not_mutate_candidate")
    return {
        "schema": "artifact-coupled-measured-provider-free-fixture-v0",
        "passed": not failures,
        "failures": failures,
        "offline_provider_only": True,
        "gpu_authorized": False,
        "apparatus_commit": measured.git_commit(),
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
