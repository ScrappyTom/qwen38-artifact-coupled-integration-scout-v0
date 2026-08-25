from __future__ import annotations

import itertools
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.actions import (
    MAX_BATCH_RANGES,
    MAX_BATCH_RESULT_TOKENS,
    MAX_BATCH_SOURCE_BYTES,
    MAX_BATCH_TOTAL_LINES,
    MAX_READ_LINES,
    MAX_SOURCE_RESULT_TOKENS,
)
from reactive_runtime.activation import activation_snapshot
from reactive_runtime.canonical import canonical_json_text, write_json
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.qualification import build_action_cases, build_cases
from reactive_runtime.records import ResultLedger
from reactive_runtime.trajectory_budget import ConstructionBudget
from reactive_runtime.world import ArchitectureWorld
from tools.offline_tokenizer import OfflineTokenizer


CONTEXT_TOKENS = 25_088
RESPONSE_RESERVE = 4_096
PROMPT_LIMIT = CONTEXT_TOKENS - RESPONSE_RESERVE
TASK_ID = "cedar-valley-evacuation-decision-package-v0"
ACTIVATION_PATH = (
    ("S01", "S02"),  # authority + hazard
    ("S03", "S06"),  # demand + shelter/care => four sources, four domains
    ("S04", "S08"),
    ("S09", "S12"),
    ("S13", "S15"),
    ("S07", "S16"),
)


def action_for_pair(pair: tuple[str, str], world: ArchitectureWorld) -> dict[str, object]:
    return {
        "action": "read_batch",
        "requests": [
            {"source_id": source_id, "start_line": 1, "end_line": len(world.sources[source_id].lines)}
            for source_id in pair
        ],
    }


def base_messages(world: ArchitectureWorld) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": (ROOT / "task" / "SYSTEM.md").read_text(encoding="utf-8")},
        {"role": "user", "content": (ROOT / "task" / "TASK.md").read_text(encoding="utf-8")},
        {"role": "user", "content": (ROOT / "task" / "ACTIONS.md").read_text(encoding="utf-8") + "\n\n# Exact source catalog\n" + world.source_catalog_for_actor()},
        {"role": "user", "content": "# Exact current candidate\n" + world.candidate_packet()},
    ]


def main() -> int:
    tokenizer = OfflineTokenizer()
    with tempfile.TemporaryDirectory() as temporary:
        world = ArchitectureWorld(ROOT / "task", Path(temporary))
        initial_messages = base_messages(world)
        base_prompt = tokenizer.count_messages(initial_messages)
        source_rows = []
        for source_id, source in world.sources.items():
            execution = world.execute(
                {"action": "read_source", "source_id": source_id, "start_line": 1, "end_line": len(source.lines)},
                result_id=f"SINGLE-{source_id}",
            )
            record = world.make_result_record(execution, result_id=f"SINGLE-{source_id}", acquired_call=0)
            source_rows.append(
                {
                    "activation_min_lines": source.activation_min_lines,
                    "bytes": source.size_bytes,
                    "evidence_domain": source.evidence_domain,
                    "full_observation_tokens": tokenizer.count_text(record.exact_content),
                    "lines": len(source.lines),
                    "source_id": source_id,
                    "source_tokens": tokenizer.count_text(source.path.read_text(encoding="utf-8")),
                }
            )

        pair_rows = []
        for pair in itertools.combinations(world.sources, 2):
            execution = world.execute(action_for_pair(pair, world), result_id=f"PAIR-{pair[0]}-{pair[1]}")
            record = world.make_result_record(execution, result_id=f"PAIR-{pair[0]}-{pair[1]}", acquired_call=0)
            pair_rows.append(
                {
                    "source_ids": list(pair),
                    "source_bytes": execution.metadata["total_source_bytes"],
                    "result_tokens": tokenizer.count_text(record.exact_content),
                }
            )

        # Exact prospective path.  A result is marked visible only after a
        # feasible later actor invocation would have crossed its boundary.
        messages = list(initial_messages)
        ledger = ResultLedger()
        path_rows = []
        pending_id: str | None = None
        pressure = None
        for step, pair in enumerate(ACTIVATION_PATH, 1):
            if pending_id is not None:
                ledger.mark_model_visible(
                    pending_id, call_index=step, message_index=len(messages) - 1
                )
                pending_id = None
            action = action_for_pair(pair, world)
            messages.append({"role": "assistant", "content": canonical_json_text(action)})
            result_id = f"RESULT-{step:03d}"
            execution = world.execute(action, result_id=result_id, ledger=ledger)
            record = world.make_result_record(execution, result_id=result_id, acquired_call=step)
            ledger.add(record)
            messages.append({"role": "user", "content": record.exact_content})
            pending_id = result_id
            prompt_tokens = tokenizer.count_messages(messages)
            row = {
                "step": step,
                "source_ids": list(pair),
                "result_tokens": tokenizer.count_text(record.exact_content),
                "prospective_prompt_tokens": prompt_tokens,
                "fits": prompt_tokens <= PROMPT_LIMIT,
            }
            path_rows.append(row)
            if prompt_tokens > PROMPT_LIMIT:
                snapshot = activation_snapshot(pending=record, ledger=ledger, world=world)
                relief = positive_savings_first_fit_step(
                    messages=messages,
                    ledger=ledger,
                    prompt_limit=PROMPT_LIMIT,
                    count_messages=tokenizer.count_messages,
                    protected_result_ids=(result_id,),
                )
                pressure = {
                    "activation_snapshot": snapshot.as_dict(),
                    "overflow_tokens": prompt_tokens - PROMPT_LIMIT,
                    "pending_result_id": result_id,
                    "positive_relief_after_tokens": relief.prompt_tokens,
                    "positive_relief_result_ids": list(relief.selected_result_ids),
                    "positive_relief_tokens": prompt_tokens - relief.prompt_tokens,
                    "step": step,
                }
                break

        maturity = path_rows[1]
        qualification_cases = [
            {
                "case_id": case.case_id,
                "prompt_tokens": tokenizer.count_messages(case.messages),
                "headroom_after_max_completion": CONTEXT_TOKENS - tokenizer.count_messages(case.messages) - 1900,
            }
            for case in build_cases(ROOT)
        ]
        action_cases = [
            {
                "case_id": case.case_id,
                "prompt_tokens": tokenizer.count_messages(case.messages),
                "headroom_after_max_completion": CONTEXT_TOKENS - tokenizer.count_messages(case.messages) - RESPONSE_RESERVE,
            }
            for case in build_action_cases(ROOT)
        ]

    max_single = max(row["full_observation_tokens"] for row in source_rows)
    max_pair = max(row["result_tokens"] for row in pair_rows)
    result = {
        "schema": "cedar-ingress-aligned-stage0-geometry-v0",
        "task_id": TASK_ID,
        "base_actor_prompt_tokens": base_prompt,
        "source_corpus_tokens": sum(row["source_tokens"] for row in source_rows),
        "source_rows": source_rows,
        "permitted_ingress_geometry": {
            "max_read_lines": MAX_READ_LINES,
            "max_batch_ranges": MAX_BATCH_RANGES,
            "max_batch_total_lines": MAX_BATCH_TOTAL_LINES,
            "max_batch_source_bytes": MAX_BATCH_SOURCE_BYTES,
            "max_source_result_tokens": MAX_SOURCE_RESULT_TOKENS,
            "max_batch_result_tokens_alias": MAX_BATCH_RESULT_TOKENS,
            "observed_max_full_single_result_tokens": max_single,
            "observed_max_full_pair_result_tokens": max_pair,
            "every_full_single_is_admissible": max_single <= MAX_SOURCE_RESULT_TOKENS,
            "every_full_pair_is_admissible": max_pair <= MAX_SOURCE_RESULT_TOKENS and max(row["source_bytes"] for row in pair_rows) <= MAX_BATCH_SOURCE_BYTES,
        },
        "prospective_activation_path": path_rows,
        "maturity_reachability": {
            "mature_after_delivered_steps": 2,
            "qualifying_source_ids": ["S01", "S02", "S03", "S06"],
            "qualifying_domains": ["authority", "demand", "hazard", "shelter_care"],
            "prospective_prompt_tokens_at_maturity": maturity["prospective_prompt_tokens"],
            "fits_at_maturity": maturity["fits"],
            "headroom_at_maturity": PROMPT_LIMIT - maturity["prospective_prompt_tokens"],
            "basis": "exact rendering of two admissible two-source batches and their action/result chronology",
        },
        "prospective_pressure_opportunity": pressure,
        "maintenance_qualification_cases": qualification_cases,
        "action_qualification_cases": action_cases,
        "trajectory_budget": {
            **ConstructionBudget(maximum_preconstruction_calls=26, postconstruction_calls=8).as_dict(),
            "clean_postconstruction_path_calls": 4,
            "clean_path": [
                "receive construction effect and run current-candidate check",
                "receive check and repair exact candidate",
                "receive repair effect and rerun check",
                "receive current recheck and propose closure",
            ],
            "additional_error_or_repair_allowance_calls": 4,
        },
        "activation_qualified": False,
        "activation_blocker": "Only an authorized ordinary screening trajectory can demonstrate authentic pressure. This offline receipt proves that the frozen coverage/domain maturity gate is prospectively reachable under the exact permitted ingress geometry before a later exact result can create pressure.",
        "measured_gpu_authorized": False,
    }
    write_json(ROOT / "STAGE0_GEOMETRY.json", result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
