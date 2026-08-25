from __future__ import annotations

import itertools
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.actions import (
    MAX_BATCH_SOURCE_BYTES,
    MAX_SOURCE_RESULT_TOKENS,
    action_json_schema,
    parse_action,
)
from reactive_runtime.activation import activation_snapshot
from reactive_runtime.canonical import canonical_json_text, sha256_file, write_json
from reactive_runtime.configuration import DELTA_CONFIGURATIONS, delta_actor_actions
from reactive_runtime.meridian_world import MeridianWorld
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
from reactive_runtime.source_delta import (
    DELTA_PREFIX,
    DELTA_PROVIDER_MAX_TOKENS,
    DELTA_TOKEN_BUDGET,
    REQUIRED_LOCAL_HEADINGS,
    SourceEvidenceRegister,
    SourceSlotRecord,
    source_delta_messages,
    validate_source_delta,
)
from reactive_runtime.trajectory_budget import ConstructionBudget
from tools.offline_tokenizer import OfflineTokenizer


TASK = ROOT / "task_meridian"
TASK_ID = "meridian-sterile-infusion-recovery-v0"
CONTEXT_TOKENS = 25_088
RESPONSE_RESERVE = 4_096
PROMPT_LIMIT = CONTEXT_TOKENS - RESPONSE_RESERVE
ACTIVATION_PATH = (
    ("AXIOM", "BRAMBLE"),
    ("CIPHER", "DRIFT"),
    ("EMBER", "FJORD"),
    ("GLINT", "HEATH"),
    ("IRIS", "JASPER"),
    ("KNOLL", "LOOM"),
    ("MARCH", "NORTH"),
    ("ONYX", "PIVOT"),
)


def verify_task_lock() -> None:
    lock = json.loads((TASK / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
    if lock.get("task_id") != TASK_ID:
        raise RuntimeError("Meridian task lock identity mismatch")
    for row in lock["files"]:
        path = TASK / row["path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise RuntimeError(f"Meridian task lock mismatch: {row['path']}")


def base_messages(world: MeridianWorld) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": (TASK / "SYSTEM.md").read_text(encoding="utf-8")},
        {"role": "user", "content": (TASK / "TASK.md").read_text(encoding="utf-8")},
        {
            "role": "user",
            "content": (TASK / "ACTIONS.md").read_text(encoding="utf-8")
            + "\n\n# Common pre-fork action notice\n"
            + "Evidence-slot mutation is not available during pressure screening.\n\n"
            + "# Exact source catalog\n"
            + world.source_catalog_for_actor(),
        },
        {"role": "user", "content": "# Exact current candidate\n" + world.candidate_packet()},
    ]


def batch_action(pair: tuple[str, str], world: MeridianWorld) -> dict[str, object]:
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


def fixture_slot_body(source_id: str, *, suffix: str = "") -> str:
    requirements = " ".join(f"Q{ordinal:02d}" for ordinal in range(1, 13))
    return f"""### REQUIREMENTS
{requirements}
### FINDINGS
Bounded source-local task work for {source_id} preserves exact values, units,
versions, owners, effects, and observations from the bound source {suffix}.
### QUALIFICATIONS AND CONFLICTS
Targets remain distinct from observations; nominal values remain distinct from
shared usable capacity; this slot is lossy and cannot replace exact evidence.
### UNKNOWNS AND REOPEN CONDITIONS
Reopen {source_id} for quotation, unresolved conflict, changed version, or
candidate-bound verification. This slot cannot authorize readiness."""


def fixture_delta(world: MeridianWorld, source_ids: tuple[str, ...], *, suffix: str = "") -> str:
    rows = [DELTA_PREFIX]
    for source_id in source_ids:
        rows.extend(
            [
                f"## SOURCE {source_id}",
                f"VERSION {world.sources[source_id].sha256}",
                fixture_slot_body(source_id, suffix=suffix),
            ]
        )
    return "\n".join(rows).rstrip() + "\n"


def fixture_decision(world: MeridianWorld, *, defective: bool) -> str:
    citations = "".join(f"[{source_id}]" for source_id in world.sources)
    core = (
        "The quality unit retains lot release authority while incident command, "
        "recall authorization, procurement, and closure authority remain distinct. "
        "The plan holds affected material at the 0.25 EU/mL alert, preserves the "
        "0.50 EU/mL rejection limit, treats 41 percent as assay-drift probability, "
        "and uses MR-4 controls and post-change samples. Demand is 38,400 bags over "
        "seventy-two hours; 93 percent registry coverage creates uncertainty rather "
        "than a demand reduction, and cohort overlap is reconciled once. The shared "
        "sterilizer limits output to 18,000 while 16,200 is the observed integrated "
        "rate after inspection loss. Component qualification distinguishes observed "
        "nineteen-hour arrival from an eight-hour target. Distribution preserves the "
        "2 and 8 degrees Celsius range, logger custody, excursion holds, route power, "
        "and facility acknowledgment. Clinical substitution requires pharmacy review. "
        "The sixteen-hour fuel observation, twelve-hour duty ceiling, qualified relief, "
        "and alternate supplier constraints govern continuity. Lot and pallet genealogy, "
        "privacy, retention, and deletion proof remain exact. Every candidate effect "
        "makes older evidence potentially stale; current check, repair, recheck, blocker, "
        "and falsifier handling precede independent adjudication. Owners receive inputs, "
        "resources, timing, dependencies, contingencies, observations, and retirement "
        "conditions. "
    )
    rows = [world.evaluator_config["decision_title"], ""]
    for index, heading in enumerate(world.decision_headings):
        body = core + citations
        if defective and index == 0:
            body += " The 41 percent humidity condition is treated as the controlling observation."
        rows.extend([f"## {heading}", "", body, ""])
    return "\n".join(rows).rstrip() + "\n"


def evaluate_candidate(world: MeridianWorld) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(TASK / "evaluator" / "evaluate.py"), str(world.candidate_root)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)


def provider_free_loop(
    configuration_id: str, root: Path, tokenizer: OfflineTokenizer
) -> dict[str, object]:
    world = MeridianWorld(
        TASK, root / configuration_id, count_text=tokenizer.count_text
    )
    ledger = ResultLedger()
    register = world.evidence_register()
    actor_effects = 0
    maintenance_effects = 0
    maintenance_calls = 0
    next_result = 1
    unrelated_preservation_checks: list[bool] = []
    all_records = []

    for pair in ACTIVATION_PATH[:5]:
        action = batch_action(pair, world)
        result_id = f"RESULT-{next_result:03d}"
        next_result += 1
        execution = world.execute(action, result_id=result_id, ledger=ledger)
        record = world.make_result_record(execution, result_id=result_id, acquired_call=next_result)
        ledger.add(record)
        messages = [
            {"role": "system", "content": "provider-free pressure fixture"},
            {"role": "user", "content": record.exact_content},
        ]
        ledger.mark_model_visible(record.result_id, call_index=next_result, message_index=1)
        count = lambda rows: sum(len(row["content"].encode("utf-8")) for row in rows)
        relief = positive_savings_first_fit_step(
            messages=messages,
            ledger=ledger,
            prompt_limit=count(messages) - 1,
            count_messages=count,
        )
        if relief.selected_result_ids != (record.result_id,):
            raise RuntimeError("provider-free fixture did not externalize current result")
        all_records.append(record)

        prior_slots = register.slots()
        if configuration_id == "L1_LOCAL_DELTA":
            output = fixture_delta(world, pair, suffix=f"batch {record.result_id}")
            validation = validate_source_delta(
                output,
                count_text=tokenizer.count_text,
                allowed_source_versions={source_id: world.sources[source_id].sha256 for source_id in pair},
                known_source_ids=world.sources,
            )
            if not validation.valid:
                raise RuntimeError(f"provider-free delta invalid: {validation.issues}")
            effect = world.apply_source_delta(validation, input_result_ids=(record.result_id,))
            maintenance_calls += 1
            maintenance_effects += effect.result_kind == "candidate_effect"
        else:
            for source_id in pair:
                effect = world.execute(
                    {
                        "action": "upsert_evidence_slot",
                        "source_id": source_id,
                        "source_version": world.sources[source_id].sha256,
                        "content": fixture_slot_body(source_id, suffix=f"batch {record.result_id}"),
                    },
                    result_id=f"RESULT-{next_result:03d}",
                    ledger=ledger,
                )
                next_result += 1
                actor_effects += effect.result_kind == "candidate_effect"
        register = world.evidence_register()
        current_slots = register.slots()
        unrelated_preservation_checks.append(
            all(
                source_id in current_slots
                and current_slots[source_id].body_sha256 == prior.body_sha256
                for source_id, prior in prior_slots.items()
                if source_id not in pair
            )
        )

    # Qualify the generic version-replacement law without changing the frozen world.
    before_version_change = register.slots()
    revised = SourceSlotRecord.create(
        source_id="AXIOM",
        source_version="f" * 64,
        body=fixture_slot_body("AXIOM", suffix="synthetic exact version successor"),
        origin="provider_free_version_fixture",
        result_ids=("VERSION-FIXTURE",),
    )
    revised_register = register.merge((revised,))
    version_replacement_preserved_unrelated = all(
        revised_register.get(source_id) == record
        for source_id, record in before_version_change.items()
        if source_id != "AXIOM"
    )

    first_decision = fixture_decision(world, defective=True)
    world.execute(
        {"action": "replace_decision", "content": first_decision},
        result_id=f"RESULT-{next_result:03d}",
        ledger=ledger,
    )
    first_check = world.execute(
        {"action": "run_check"}, result_id=f"RESULT-{next_result + 1:03d}", ledger=ledger
    )
    first_projection = first_check.metadata["check_projection"]
    world.execute(
        {"action": "replace_decision", "content": fixture_decision(world, defective=False)},
        result_id=f"RESULT-{next_result + 2:03d}",
        ledger=ledger,
    )
    stale = world.current_check_binding()
    second_check = world.execute(
        {"action": "run_check"}, result_id=f"RESULT-{next_result + 3:03d}", ledger=ledger
    )
    second_projection = second_check.metadata["check_projection"]
    current = world.current_check_binding()
    submission = world.execute(
        {"action": "submit"}, result_id=f"RESULT-{next_result + 4:03d}", ledger=ledger
    )
    final_evaluation = evaluate_candidate(world)
    final_slots = world.evidence_register().slots()
    known_result_ids = {record.result_id for record in ledger.records()}
    return {
        "configuration_id": configuration_id,
        "source_results_externalized": len(all_records),
        "source_slots": len(final_slots),
        "source_slot_result_provenance_complete": all(
            record.result_ids
            and all(result_id in known_result_ids for result_id in record.result_ids)
            for record in final_slots.values()
        ),
        "maximum_source_slot_tokens": max(
            tokenizer.count_text(record.body) for record in final_slots.values()
        ),
        "source_slot_origins": sorted(
            {record.origin for record in final_slots.values()}
        ),
        "actor_slot_effects": actor_effects,
        "maintenance_calls": maintenance_calls,
        "maintenance_candidate_effects": maintenance_effects,
        "unrelated_slots_preserved": all(unrelated_preservation_checks),
        "version_replacement_preserved_unrelated": version_replacement_preserved_unrelated,
        "first_check_passed": first_projection["passed"],
        "first_check_currency": "current",
        "check_stale_after_repair": stale["currency"] == "stale",
        "recheck_passed": second_projection["passed"],
        "recheck_currency": current["currency"],
        "submission_kind": submission.result_kind,
        "submitted": world.submitted,
        "mechanical_final_evaluation": final_evaluation,
    }


def main() -> int:
    verify_task_lock()
    tokenizer = OfflineTokenizer()
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        world = MeridianWorld(TASK, temporary_root / "geometry")
        initial_candidate = world.candidate_sha256
        base_prompt = tokenizer.count_messages(base_messages(world))

        source_rows = []
        for source_id, source in world.sources.items():
            execution = world.execute(
                {
                    "action": "read_source",
                    "source_id": source_id,
                    "start_line": 1,
                    "end_line": len(source.lines),
                },
                result_id="GEOMETRY",
            )
            record = world.make_result_record(execution, result_id="GEOMETRY", acquired_call=0)
            source_rows.append(
                {
                    "source_id": source_id,
                    "source_tokens": tokenizer.count_text(source.path.read_text(encoding="utf-8")),
                    "result_tokens": tokenizer.count_text(record.exact_content),
                    "source_bytes": source.size_bytes,
                    "line_count": len(source.lines),
                }
            )

        pair_rows = []
        for left, right in itertools.combinations(world.sources, 2):
            execution = world.execute(
                batch_action((left, right), world), result_id="GEOMETRY"
            )
            record = world.make_result_record(execution, result_id="GEOMETRY", acquired_call=0)
            pair_rows.append(
                {
                    "source_ids": [left, right],
                    "result_tokens": tokenizer.count_text(record.exact_content),
                    "source_bytes": execution.metadata["total_source_bytes"],
                }
            )

        path_world = MeridianWorld(TASK, temporary_root / "path")
        path_messages = base_messages(path_world)
        path_ledger = ResultLedger()
        path_rows = []
        path_records = []
        pressure = None
        for step, pair in enumerate(ACTIVATION_PATH, start=1):
            action = batch_action(pair, path_world)
            path_messages.append({"role": "assistant", "content": canonical_json_text(action)})
            result_id = f"RESULT-{step:03d}"
            execution = path_world.execute(action, result_id=result_id, ledger=path_ledger)
            record = path_world.make_result_record(execution, result_id=result_id, acquired_call=step)
            path_ledger.add(record)
            path_records.append(record)
            path_messages.append({"role": "user", "content": record.exact_content})
            prompt_tokens = tokenizer.count_messages(path_messages)
            path_rows.append(
                {
                    "step": step,
                    "source_ids": list(pair),
                    "result_tokens": tokenizer.count_text(record.exact_content),
                    "prospective_prompt_tokens": prompt_tokens,
                    "fits": prompt_tokens <= PROMPT_LIMIT,
                }
            )
            if prompt_tokens > PROMPT_LIMIT:
                snapshot = activation_snapshot(pending=record, ledger=path_ledger, world=path_world)
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
            path_ledger.mark_model_visible(
                record.result_id, call_index=step + 1, message_index=len(path_messages) - 1
            )

        delta_geometry = []
        empty_register = SourceEvidenceRegister()
        for record in path_records:
            messages = source_delta_messages(
                task_text=(TASK / "TASK.md").read_text(encoding="utf-8"),
                register=empty_register,
                newly_externalized=(record,),
                source_versions=path_world.source_versions,
            )
            prompt_tokens = tokenizer.count_messages(messages)
            delta_geometry.append(
                {
                    "result_id": record.result_id,
                    "source_ids": record.metadata["source_ids"],
                    "prompt_tokens": prompt_tokens,
                    "headroom_after_completion": CONTEXT_TOKENS
                    - prompt_tokens
                    - DELTA_PROVIDER_MAX_TOKENS,
                    "fits": prompt_tokens + DELTA_PROVIDER_MAX_TOKENS <= CONTEXT_TOKENS,
                }
            )

        parser_examples = [
            parse_action(
                canonical_json_text(
                    {
                        "action": "upsert_evidence_slot",
                        "source_id": "AXIOM",
                        "source_version": world.sources["AXIOM"].sha256,
                        "content": fixture_slot_body("AXIOM"),
                    }
                ),
                delta_actor_actions("W0_DIRECT_WORK"),
                decision_headings=world.decision_headings,
            ),
            parse_action(
                canonical_json_text(
                    {
                        "action": "upsert_decision_section",
                        "heading": world.decision_headings[0],
                        "body": "bounded exact decision work [AXIOM]",
                    }
                ),
                delta_actor_actions("L1_LOCAL_DELTA"),
                decision_headings=world.decision_headings,
            ),
            parse_action(
                '{"action":"run_check"}',
                delta_actor_actions("L1_LOCAL_DELTA"),
                decision_headings=world.decision_headings,
            ),
        ]
        schemas = {
            configuration_id: action_json_schema(
                delta_actor_actions(configuration_id),
                source_ids=world.sources,
                reopen_result_ids=(),
                decision_headings=world.decision_headings,
                schema_name=f"meridian_{configuration_id.casefold()}_action_v0",
            )["json_schema"]["name"]
            for configuration_id in DELTA_CONFIGURATIONS
        }
        fixtures = [
            provider_free_loop(configuration_id, temporary_root / "fixtures", tokenizer)
            for configuration_id in DELTA_CONFIGURATIONS
        ]
        path_candidate_unchanged = path_world.candidate_sha256 == initial_candidate

    if pressure is None:
        raise RuntimeError("Meridian prospective path did not reach pressure")
    if len(pressure["activation_snapshot"]["qualifying_sources"]) < 4:
        raise RuntimeError("Meridian pressure occurs before source coverage activation")
    if len(pressure["activation_snapshot"]["qualifying_domains"]) < 3:
        raise RuntimeError("Meridian pressure occurs before domain activation")
    if not pressure["positive_relief_result_ids"] or pressure["positive_relief_after_tokens"] > PROMPT_LIMIT:
        raise RuntimeError("Meridian pressure lacks feasible positive relief")
    if not all(row["fits"] for row in delta_geometry):
        raise RuntimeError("Meridian source-local maintenance prompt is infeasible")
    if not path_candidate_unchanged:
        raise RuntimeError("prospective pressure path mutated candidate")
    for row in fixtures:
        if not (
            row["source_slots"] == 10
            and row["unrelated_slots_preserved"]
            and row["version_replacement_preserved_unrelated"]
            and row["first_check_passed"] is False
            and row["check_stale_after_repair"]
            and row["recheck_passed"] is True
            and row["recheck_currency"] == "current"
            and row["submitted"]
        ):
            raise RuntimeError(f"provider-free complete loop failed: {row['configuration_id']}")

    result = {
        "schema": "meridian-source-local-delta-stage0-v0",
        "task_id": TASK_ID,
        "task_source_lock_sha256": sha256_file(TASK / "TASK_SOURCE_LOCK.json"),
        "model_profile_lock_sha256": sha256_file(ROOT / "MERIDIAN_MODEL_PROFILE_LOCK.json"),
        "base_actor_prompt_tokens": base_prompt,
        "source_corpus_tokens": sum(row["source_tokens"] for row in source_rows),
        "source_corpus_bytes": sum(row["source_bytes"] for row in source_rows),
        "source_rows": source_rows,
        "permitted_ingress_geometry": {
            "maximum_batch_ranges": 2,
            "maximum_batch_lines": 160,
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
        "source_delta_prompt_geometry": delta_geometry,
        "source_delta_contract": {
            "total_token_budget": DELTA_TOKEN_BUDGET,
            "provider_completion_tokens": DELTA_PROVIDER_MAX_TOKENS,
            "required_local_headings": list(REQUIRED_LOCAL_HEADINGS),
            "global_replacement_forbidden": True,
            "readiness_authority": False,
            "mechanical_merge_unit": "source_id_and_source_version_slot",
        },
        "provider_free_complete_system_fixtures": fixtures,
        "dynamic_action_parser_cases": parser_examples,
        "dynamic_action_schema_names": schemas,
        "trajectory_budget": {
            **ConstructionBudget(
                maximum_preconstruction_calls=32, postconstruction_calls=10
            ).as_dict(),
            "protected_postconstruction_tail_calls": 10,
            "tail_operations": ["effect_uptake", "check", "repair", "recheck", "closure"],
            "maximum_maintenance_calls_L1": 12,
            "W0_maximum_provider_calls": 42,
            "L1_maximum_provider_calls": 54,
        },
        "evaluator": {
            "candidate_bound": True,
            "mechanical_check_cannot_return_ready": True,
            "independent_readiness_required": True,
            "gold_requirement_source_map_actor_visible": False,
        },
        "authentic_activation_qualified": False,
        "next_live_operation": "ordinary_common_pressure_screen_only",
        "gpu_authorized": False,
        "provider_calls": 0,
    }
    write_json(ROOT / "MERIDIAN_STAGE0_PREFLIGHT.json", result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
