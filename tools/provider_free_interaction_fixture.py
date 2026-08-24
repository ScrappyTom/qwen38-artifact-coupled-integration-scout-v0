from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import write_json
from reactive_runtime.configuration import CONFIGURATIONS
from reactive_runtime.integration import next_artifact, validate_integration
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
from reactive_runtime.world import ArchitectureWorld


def exercise(configuration_id: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as temporary:
        world = ArchitectureWorld(ROOT / "task", Path(temporary))
        ledger = ResultLedger()
        execution = world.execute({"action": "read_source", "source_id": "S02", "start_line": 1, "end_line": 200}, result_id="RESULT-001")
        record = world.make_result_record(execution, result_id="RESULT-001", acquired_call=1)
        ledger.add(record)
        messages = [{"role": "system", "content": "fixture"}, {"role": "user", "content": record.exact_content}]
        ledger.mark_model_visible(record.result_id, call_index=2, message_index=1)
        count = lambda rows: sum(len(row["content"]) for row in rows)
        relief = positive_savings_first_fit_step(messages=messages, ledger=ledger, prompt_limit=count(messages) - 1, count_messages=count)
        integration_body = "# Evidence Integration Ledger\n\nR01: exact custody remains supported [S02].\n"
        validation = validate_integration(integration_body, count_text=lambda value: len(value.split()), allowed_source_ids=("S02",))
        artifact = next_artifact(prior=None, body=integration_body, body_tokens=validation.output_tokens, result=record)
        before_maintenance = world.candidate_sha256
        maintenance = world.apply_integration(configuration_id, artifact)
        after_maintenance = world.candidate_sha256
        section_effect = world.execute({"action": "upsert_decision_section", "heading": "Decision and scope", "body": "Run a bounded interaction scout [S02]."}, result_id="RESULT-003")
        first_check = world.execute({"action": "run_check"}, result_id="RESULT-004")
        repair = world.execute({"action": "upsert_decision_section", "heading": "Uncertainties and falsifiers", "body": "The interaction remains falsifiable [S02]."}, result_id="RESULT-005")
        stale = world.current_check_binding()
        second_check = world.execute({"action": "run_check"}, result_id="RESULT-006")
        current = world.current_check_binding()
        submission = world.execute({"action": "submit"}, result_id="RESULT-007")
        return {
            "configuration_id": configuration_id,
            "positive_relief_selected": list(relief.selected_result_ids),
            "integration_valid": validation.valid,
            "maintenance_result_kind": maintenance.result_kind,
            "candidate_changed_by_maintenance": before_maintenance != after_maintenance,
            "section_effect_kind": section_effect.result_kind,
            "first_check_kind": first_check.result_kind,
            "repair_effect_kind": repair.result_kind,
            "post_repair_prior_check_currency": stale["currency"],
            "recheck_kind": second_check.result_kind,
            "recheck_currency": current["currency"],
            "submission_kind": submission.result_kind,
        }


def main() -> int:
    rows = [exercise(configuration_id) for configuration_id in CONFIGURATIONS]
    expected = {
        "D0_DETACHED": ("semantic_state_effect", False),
        "A1_COUPLED": ("candidate_effect", True),
    }
    failures = []
    for row in rows:
        kind, changed = expected[row["configuration_id"]]
        if row["maintenance_result_kind"] != kind or row["candidate_changed_by_maintenance"] is not changed:
            failures.append(f"maintenance_semantics:{row['configuration_id']}")
        if row["post_repair_prior_check_currency"] != "stale" or row["recheck_currency"] != "current":
            failures.append(f"check_currency:{row['configuration_id']}")
    result = {"schema": "artifact-coupled-provider-free-interaction-fixture-v0", "passed": not failures, "failures": failures, "configurations": rows, "provider_calls": 0, "gpu_authorized": False}
    write_json(ROOT / "STAGE0_INTERACTION_FIXTURE.json", result)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
