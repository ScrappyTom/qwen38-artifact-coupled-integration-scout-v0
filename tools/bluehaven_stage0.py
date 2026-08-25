from __future__ import annotations

import itertools
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.actions import (
    MAX_BATCH_RANGES,
    MAX_BATCH_SOURCE_BYTES,
    MAX_BATCH_TOTAL_LINES,
    MAX_READ_LINES,
    MAX_SOURCE_RESULT_TOKENS,
    action_json_schema,
    parse_action,
)
from reactive_runtime.activation import activation_snapshot
from reactive_runtime.canonical import canonical_json_text, sha256_file, write_json
from reactive_runtime.integration import (
    BATCHED_INTEGRATION_PROVIDER_MAX_TOKENS,
    BATCHED_INTEGRATION_TOKEN_BUDGET,
    batched_integration_messages,
    next_artifact_batch,
    validate_integration,
)
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
from reactive_runtime.trajectory_budget import ConstructionBudget
from reactive_runtime.world import ArchitectureWorld
from tools.offline_tokenizer import OfflineTokenizer


TASK = ROOT / "task_bluehaven"
TASK_ID = "bluehaven-water-restoration-package-v0"
CONTEXT_TOKENS = 25_088
RESPONSE_RESERVE = 4_096
PROMPT_LIMIT = CONTEXT_TOKENS - RESPONSE_RESERVE
ACTIVATION_PATH = (
    ("S01", "S02"),
    ("S03", "S04"),
    ("S05", "S06"),
    ("S07", "S08"),
    ("S09", "S10"),
    ("S11", "S12"),
    ("S13", "S14"),
    ("S15", "S16"),
)


def verify_task_lock() -> None:
    lock = json.loads((TASK / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
    if lock.get("task_id") != TASK_ID:
        raise RuntimeError("Bluehaven task lock identity mismatch")
    for row in lock["files"]:
        path = TASK / row["path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise RuntimeError(f"Bluehaven task lock mismatch: {row['path']}")


def base_messages(world: ArchitectureWorld) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": (TASK / "SYSTEM.md").read_text(encoding="utf-8")},
        {"role": "user", "content": (TASK / "TASK.md").read_text(encoding="utf-8")},
        {
            "role": "user",
            "content": (TASK / "ACTIONS.md").read_text(encoding="utf-8")
            + "\n\n# Exact source catalog\n"
            + world.source_catalog_for_actor(),
        },
        {"role": "user", "content": "# Exact current candidate\n" + world.candidate_packet()},
    ]


def batch_action(pair: tuple[str, str], world: ArchitectureWorld) -> dict[str, object]:
    return {
        "action": "read_batch",
        "requests": [
            {
                "source_id": source_id,
                "start_line": 1,
                "end_line": len(world.sources[source_id].lines),
            }
            for source_id in pair
        ],
    }


def fixture_ledger(source_ids: tuple[str, ...]) -> str:
    cited = "".join(f"[{source_id}]" for source_id in source_ids)
    rows = ["# Evidence Integration Ledger", ""]
    for ordinal in range(1, 13):
        rows.append(
            f"R{ordinal:02d}: provisional exact-work binding; preserve units, "
            f"revision, qualifications, and unresolved blockers {cited}."
        )
    rows.extend(["", "This state is model-authored, lossy, and not readiness authority."])
    return "\n".join(rows)


def fixture_decision(world: ArchitectureWorld, *, suffix: str) -> str:
    rows = [world.evaluator_config["decision_title"], ""]
    for heading in world.decision_headings:
        rows.extend(
            [
                f"## {heading}",
                "",
                "Provisional candidate-bound work preserves 0.2 mg/L residual, "
                "5 micrograms per liter benzene, 38 percent plume probability, "
                "94 percent registry coverage, the 15 ML/day East trunk, observed "
                "13.4 output, 28 psi hospital pressure, WQ-R7, public-health and "
                "utility director authority, clinical potable handoff, the "
                "seventeen-hour fuel delay, twelve-hour duty, alternate supply, "
                "Vietnamese and ASL door-knock receipt evidence, and candidate "
                f"recheck blockers and falsifiers [S01][S02][S03][S04][S05][S06] {suffix}.",
                "",
            ]
        )
    return "\n".join(rows).rstrip() + "\n"


def provider_free_loop(configuration_id: str, root: Path, tokenizer: OfflineTokenizer) -> dict[str, object]:
    world = ArchitectureWorld(TASK, root / configuration_id)
    ledger = ResultLedger()
    records = []
    for ordinal, pair in enumerate(ACTIVATION_PATH[:3], 1):
        action = batch_action(pair, world)
        execution = world.execute(action, result_id=f"RESULT-{ordinal:03d}", ledger=ledger)
        record = world.make_result_record(execution, result_id=f"RESULT-{ordinal:03d}", acquired_call=ordinal)
        ledger.add(record)
        ledger.mark_model_visible(record.result_id, call_index=ordinal + 1, message_index=ordinal)
        ledger.mark_external(record.result_id)
        records.append(record)

    effects = []
    if configuration_id == "B1_BATCHED_COUPLED":
        body = fixture_ledger(tuple(f"S{i:02d}" for i in range(1, 7)))
        validation = validate_integration(
            body,
            count_text=tokenizer.count_text,
            allowed_source_ids=tuple(f"S{i:02d}" for i in range(1, 7)),
            token_budget=BATCHED_INTEGRATION_TOKEN_BUDGET,
        )
        if not validation.valid:
            raise RuntimeError(f"provider-free batched integration invalid: {validation}")
        artifact = next_artifact_batch(
            prior=None,
            body=body,
            body_tokens=validation.output_tokens,
            results=records,
        )
        effect = world.apply_integration("A1_COUPLED", artifact)
        effects.append(effect.result_kind)
    else:
        effect = world.execute(
            {"action": "replace_evidence_ledger", "content": fixture_ledger(tuple(f"S{i:02d}" for i in range(1, 7)))},
            result_id="RESULT-004",
            ledger=ledger,
        )
        effects.append(effect.result_kind)

    construction = world.execute(
        {"action": "replace_decision", "content": fixture_decision(world, suffix="initial")},
        result_id="RESULT-005",
        ledger=ledger,
    )
    effects.append(construction.result_kind)
    first_check = world.execute({"action": "run_check"}, result_id="RESULT-006", ledger=ledger)
    first_check_projection = first_check.metadata["check_projection"]
    current_before_repair = world.current_check_binding()
    repair = world.execute(
        {"action": "replace_decision", "content": fixture_decision(world, suffix="repaired")},
        result_id="RESULT-007",
        ledger=ledger,
    )
    stale_after_repair = repair.metadata.get("cause") == "actor_replace_decision" and world.current_check_binding()
    recheck = world.execute({"action": "run_check"}, result_id="RESULT-008", ledger=ledger)
    current_after_recheck = world.current_check_binding()
    submission = world.execute({"action": "submit"}, result_id="RESULT-009", ledger=ledger)
    return {
        "configuration_id": configuration_id,
        "effect_kinds": effects,
        "first_check_kind": first_check.result_kind,
        "first_check_passed": first_check_projection["passed"],
        "first_check_closure_readiness": first_check_projection["closure_readiness"],
        "check_current_before_repair": current_before_repair["currency"] == "current",
        "check_stale_after_repair": bool(stale_after_repair) and stale_after_repair["currency"] == "stale",
        "recheck_current": current_after_recheck["currency"] == "current",
        "submission_kind": submission.result_kind,
        "candidate_changed": world.version_index >= 2,
        "submitted": world.submitted,
    }


def main() -> int:
    verify_task_lock()
    tokenizer = OfflineTokenizer()
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        world = ArchitectureWorld(TASK, temporary_root / "geometry")
        messages = base_messages(world)
        base_prompt = tokenizer.count_messages(messages)
        source_rows = []
        for source_id, source in world.sources.items():
            action = {
                "action": "read_source",
                "source_id": source_id,
                "start_line": 1,
                "end_line": len(source.lines),
            }
            execution = world.execute(action, result_id=f"SINGLE-{source_id}")
            record = world.make_result_record(execution, result_id=f"SINGLE-{source_id}", acquired_call=0)
            source_rows.append(
                {
                    "source_id": source_id,
                    "evidence_domain": source.evidence_domain,
                    "lines": len(source.lines),
                    "bytes": source.size_bytes,
                    "result_tokens": tokenizer.count_text(record.exact_content),
                    "source_tokens": tokenizer.count_text(source.path.read_text(encoding="utf-8")),
                }
            )

        pair_rows = []
        for pair in itertools.combinations(world.sources, 2):
            execution = world.execute(batch_action(pair, world), result_id=f"PAIR-{pair[0]}-{pair[1]}")
            record = world.make_result_record(execution, result_id=f"PAIR-{pair[0]}-{pair[1]}", acquired_call=0)
            pair_rows.append(
                {
                    "source_ids": list(pair),
                    "source_bytes": execution.metadata["total_source_bytes"],
                    "result_tokens": tokenizer.count_text(record.exact_content),
                }
            )

        path_messages = list(messages)
        path_ledger = ResultLedger()
        path_records = []
        path_rows = []
        pending_id = None
        pressure = None
        for step, pair in enumerate(ACTIVATION_PATH, 1):
            if pending_id is not None:
                path_ledger.mark_model_visible(
                    pending_id, call_index=step, message_index=len(path_messages) - 1
                )
            action = batch_action(pair, world)
            path_messages.append({"role": "assistant", "content": canonical_json_text(action)})
            result_id = f"RESULT-{step:03d}"
            execution = world.execute(action, result_id=result_id, ledger=path_ledger)
            record = world.make_result_record(execution, result_id=result_id, acquired_call=step)
            path_ledger.add(record)
            path_records.append(record)
            path_messages.append({"role": "user", "content": record.exact_content})
            pending_id = result_id
            prompt_tokens = tokenizer.count_messages(path_messages)
            path_rows.append(
                {
                    "step": step,
                    "source_ids": list(pair),
                    "prospective_prompt_tokens": prompt_tokens,
                    "fits": prompt_tokens <= PROMPT_LIMIT,
                }
            )
            if prompt_tokens > PROMPT_LIMIT:
                snapshot = activation_snapshot(pending=record, ledger=path_ledger, world=world)
                relief = positive_savings_first_fit_step(
                    messages=path_messages,
                    ledger=path_ledger,
                    prompt_limit=PROMPT_LIMIT,
                    count_messages=tokenizer.count_messages,
                    protected_result_ids=(result_id,),
                )
                pressure = {
                    "step": step,
                    "pending_result_id": result_id,
                    "overflow_tokens": prompt_tokens - PROMPT_LIMIT,
                    "activation_snapshot": snapshot.as_dict(),
                    "positive_relief_result_ids": list(relief.selected_result_ids),
                    "positive_relief_after_tokens": relief.prompt_tokens,
                    "positive_relief_tokens": prompt_tokens - relief.prompt_tokens,
                }
                break

        maintenance_batches = []
        prior_text = fixture_ledger(tuple(f"S{i:02d}" for i in range(1, 7)))
        prior_validation = validate_integration(
            prior_text,
            count_text=tokenizer.count_text,
            allowed_source_ids=tuple(f"S{i:02d}" for i in range(1, 7)),
            token_budget=BATCHED_INTEGRATION_TOKEN_BUDGET,
        )
        prior = next_artifact_batch(
            prior=None,
            body=prior_text,
            body_tokens=prior_validation.output_tokens,
            results=path_records[:3],
        )
        for start in range(0, min(len(path_records), 6), 3):
            batch = path_records[start : start + 3]
            allowed = sorted(
                set(prior.observed_source_ids)
                | {source for record in batch for source in record.metadata["source_ids"]}
            )
            maintenance_messages = batched_integration_messages(
                task_text=(TASK / "TASK.md").read_text(encoding="utf-8"),
                prior=prior,
                newly_externalized=batch,
                allowed_source_ids=allowed,
            )
            prompt = tokenizer.count_messages(maintenance_messages)
            maintenance_batches.append(
                {
                    "result_ids": [record.result_id for record in batch],
                    "prompt_tokens": prompt,
                    "headroom_after_max_completion": CONTEXT_TOKENS
                    - prompt
                    - BATCHED_INTEGRATION_PROVIDER_MAX_TOKENS,
                    "fits": prompt + BATCHED_INTEGRATION_PROVIDER_MAX_TOKENS <= CONTEXT_TOKENS,
                }
            )

        parser_examples = []
        for raw in (
            '{"action":"read_batch","requests":[{"source_id":"S01","start_line":1,"end_line":70},{"source_id":"S02","start_line":1,"end_line":70}]}',
            '{"action":"upsert_decision_section","heading":"Contamination triggers and service-zone sequencing","body":"bounded exact work [S02]"}',
            '{"action":"run_check"}',
        ):
            parser_examples.append(
                parse_action(
                    raw,
                    ("read_batch", "upsert_decision_section", "run_check"),
                    decision_headings=world.decision_headings,
                )
            )
        schema = action_json_schema(
            ("read_batch", "upsert_decision_section", "run_check"),
            source_ids=world.sources,
            reopen_result_ids=(),
            decision_headings=world.decision_headings,
            schema_name="bluehaven_actor_action_v0",
        )
        fixtures = [
            provider_free_loop(configuration_id, temporary_root / "fixtures", tokenizer)
            for configuration_id in ("B1_BATCHED_COUPLED", "W1_DIRECT_WORK")
        ]

    if pressure is None:
        raise RuntimeError("Bluehaven prospective path did not reach pressure")
    if len(pressure["activation_snapshot"]["qualifying_sources"]) < 4:
        raise RuntimeError("Bluehaven pressure occurs before source maturity")
    if len(pressure["activation_snapshot"]["qualifying_domains"]) < 3:
        raise RuntimeError("Bluehaven pressure occurs before domain maturity")
    if not pressure["positive_relief_result_ids"] or pressure["positive_relief_after_tokens"] > PROMPT_LIMIT:
        raise RuntimeError("Bluehaven pressure lacks positive feasible relief")
    if not all(row["fits"] for row in maintenance_batches):
        raise RuntimeError("Bluehaven batched maintenance prompt is infeasible")
    if not all(
        row["check_current_before_repair"]
        and row["first_check_passed"] is False
        and row["first_check_closure_readiness"] == "not_ready"
        and row["check_stale_after_repair"]
        and row["recheck_current"]
        and row["submitted"]
        for row in fixtures
    ):
        raise RuntimeError("Bluehaven provider-free interaction fixture failed")

    result = {
        "schema": "bluehaven-offline-stage0-v0",
        "task_id": TASK_ID,
        "task_source_lock_sha256": sha256_file(TASK / "TASK_SOURCE_LOCK.json"),
        "base_actor_prompt_tokens": base_prompt,
        "source_corpus_tokens": sum(row["source_tokens"] for row in source_rows),
        "source_rows": source_rows,
        "permitted_ingress_geometry": {
            "maximum_read_lines": MAX_READ_LINES,
            "maximum_batch_ranges": MAX_BATCH_RANGES,
            "maximum_batch_lines": MAX_BATCH_TOTAL_LINES,
            "maximum_batch_source_bytes": MAX_BATCH_SOURCE_BYTES,
            "maximum_source_result_tokens": MAX_SOURCE_RESULT_TOKENS,
            "observed_max_single_result_tokens": max(row["result_tokens"] for row in source_rows),
            "observed_max_pair_result_tokens": max(row["result_tokens"] for row in pair_rows),
            "observed_max_pair_source_bytes": max(row["source_bytes"] for row in pair_rows),
            "every_full_single_admissible": max(row["result_tokens"] for row in source_rows) <= MAX_SOURCE_RESULT_TOKENS,
            "every_full_pair_admissible": max(row["result_tokens"] for row in pair_rows) <= MAX_SOURCE_RESULT_TOKENS
            and max(row["source_bytes"] for row in pair_rows) <= MAX_BATCH_SOURCE_BYTES,
        },
        "prospective_activation_path": path_rows,
        "prospective_pressure_opportunity": pressure,
        "batched_maintenance_prompt_geometry": maintenance_batches,
        "batched_maintenance_expression_budget": {
            "admission_tokens": BATCHED_INTEGRATION_TOKEN_BUDGET,
            "provider_completion_tokens": BATCHED_INTEGRATION_PROVIDER_MAX_TOKENS,
            "rationale": "prospectively clears the 1369-1900-token Cedar output range while retaining a bounded task-work representation; not tuned on Bluehaven model behavior",
        },
        "provider_free_complete_system_fixtures": fixtures,
        "dynamic_action_parser_cases": parser_examples,
        "dynamic_action_schema_name": schema["json_schema"]["name"],
        "trajectory_budget": {
            **ConstructionBudget(
                maximum_preconstruction_calls=28, postconstruction_calls=8
            ).as_dict(),
            "clean_verification_tail_calls": 4,
            "additional_repair_or_expression_allowance_calls": 4,
            "B1_maximum_maintenance_calls": 7,
            "B1_maximum_provider_calls": 43,
            "W1_maximum_provider_calls": 36,
        },
        "relation_level_evaluator": {
            "candidate_bound": True,
            "forbidden_conversion_gates": list(
                json.loads((TASK / "EVALUATOR.json").read_text(encoding="utf-8"))[
                    "forbidden_relation_patterns"
                ]
            ),
            "independent_semantic_adjudication_still_required": True,
        },
        "authentic_activation_qualified": False,
        "authentic_activation_blocker": "Only the separately authorized ordinary actor pressure screen can establish realized pressure and a common pretreatment boundary.",
        "gpu_authorized": False,
    }
    write_json(ROOT / "BLUEHAVEN_STAGE0_PREFLIGHT.json", result)
    print(json.dumps({"passed": True, "pressure_step": pressure["step"], "output": str(ROOT / "BLUEHAVEN_STAGE0_PREFLIGHT.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
