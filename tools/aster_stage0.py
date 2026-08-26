from __future__ import annotations

# ruff: noqa: E402

import itertools
import json
import re
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
from reactive_runtime.aster_world import AsterWorld
from reactive_runtime.canonical import canonical_json_text, sha256_file, write_json
from reactive_runtime.configuration import (
    RELATIONAL_CONFIGURATIONS,
    relational_actor_actions,
)
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
from reactive_runtime.relational_delta import (
    REGISTER_TOKEN_BUDGET,
    SOURCE_DELTA_PROVIDER_MAX_TOKENS,
    SOURCE_DELTA_TOKEN_BUDGET,
    SOURCE_SLOT_TOKEN_BUDGET,
    ProvenanceRegister,
    relational_delta_messages,
    validate_relational_delta,
)
from reactive_runtime.trajectory_budget import ConstructionBudget
from tools.materialize_aster_world import SOURCE_IDS, SPECS
from tools.offline_tokenizer import OfflineTokenizer


TASK = ROOT / "task_aster"
TASK_ID = "aster-payment-recovery-decision-v0"
CONTEXT_TOKENS = 25_088
RESPONSE_RESERVE = 4_096
PROMPT_LIMIT = CONTEXT_TOKENS - RESPONSE_RESERVE
ACTIVATION_PATH = (
    ("ANCHOR", "BRIDGE"),
    ("CIRRUS", "DUSK"),
    ("EMBER", "JUNIPER"),
    ("FORGE", "MICA"),
    ("IRIS", "NOVA"),
    ("LATTICE", "GROVE"),
    ("HARBOR", "KELP"),
    ("ORBIT", "PRISM"),
)


def verify_task_lock() -> None:
    lock = json.loads((TASK / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
    if lock.get("task_id") != TASK_ID:
        raise RuntimeError("Aster task lock identity mismatch")
    for row in lock.get("files", []):
        path = TASK / str(row.get("path"))
        if not path.is_file() or sha256_file(path) != row.get("sha256"):
            raise RuntimeError(f"Aster task lock mismatch: {row.get('path')}")


def source_catalog() -> dict[str, dict[str, object]]:
    value = json.loads((TASK / "SOURCE_CATALOG.json").read_text(encoding="utf-8"))
    return {str(row["source_id"]): row for row in value["sources"]}


def base_messages(world: AsterWorld) -> list[dict[str, str]]:
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


def batch_action(pair: tuple[str, str], world: AsterWorld) -> dict[str, object]:
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


def fixture_delta(
    world: AsterWorld,
    record_id: str,
    source_ids: tuple[str, ...],
) -> str:
    known = tuple(world.sources)
    spec_by_id = dict(zip(SOURCE_IDS, SPECS, strict=True))
    blocks = ["# Provenance-local relational delta"]
    for source_id in source_ids:
        statement = spec_by_id[source_id].relationships[0]
        referents = tuple(
            candidate
            for candidate in known
            if candidate != source_id
            and re.search(
                rf"(?<![A-Z0-9_-]){re.escape(candidate)}(?![A-Z0-9_-])",
                statement,
            )
        )
        blocks.extend(
            [
                f"## CLAIM {source_id}_REL",
                f"SLOT_SOURCE: {source_id}",
                f"SOURCE_VERSION: {world.sources[source_id].sha256}",
                f"EVIDENCE_RESULT: {record_id}",
                f"EVIDENCE_QUOTE: {statement}",
                "MODE: source_reported_relationship",
                "ATTRIBUTION: owner_source_reported",
                f"REFERENTS: {','.join(referents)}",
                "AUTHORITY: non_authoritative_derivative",
                f"STATEMENT: {statement}",
            ]
        )
    return "\n".join(blocks) + "\n"


def fixture_ledger() -> str:
    return """# Aster Evidence and Decision Matrix

## Established source-bound controls

Authority and current verification remain separate [ANCHOR] [PRISM]. Ledger,
retry, queue, capacity, settlement, security, telemetry, and rollback evidence
are version-bound [BRIDGE] [CIRRUS] [DUSK] [EMBER] [FORGE] [IRIS] [LATTICE]
[NOVA].

## Cross-source dependencies

Queue replay requires ledger position, retry identity, capacity, and ordering
telemetry [BRIDGE] [CIRRUS] [DUSK] [EMBER] [LATTICE]. Settlement release
requires current ledger and reconciliation evidence [BRIDGE] [FORGE] [MICA].

## Conflicts, unknowns, and currentness

Historical exercise evidence cannot establish current R5 readiness [ORBIT]
[NOVA] [PRISM]. Customer loss and reportability remain bound to reconciliation
and authority [HARBOR] [KELP] [MICA] [ANCHOR].
"""


def fixture_decision(world: AsterWorld, *, defective: bool) -> str:
    citations = " ".join(f"[{source_id}]" for source_id in world.sources)
    core = (
        "The incident commander isolates traffic while the risk owner retains restoration authority; independent verification and accountable closure remain separate. "
        "Ledger evidence preserves 1,800 milliseconds p95, the 2.5 seconds three-window block, a fifteen seconds RPO, and a forty-five minutes RTO. "
        "Idempotency retains forty-five minutes for API retries and two hours for delayed merchant acknowledgments; the 0.08 percent duplicate observation remains merchant-and-operation scoped. "
        "The 3.6 million queue drains at 1,200 messages per second against 400 live ingress, with 200,000 plus current ordering evidence as the restore gate. "
        "Shared capacity is 24,000 TPS and current usable capacity is 21,600 TPS; 10, 25, 50, and 100 percent stages each require two ten-minute windows. "
        "Settlement preserves 17:00 UTC and 15:30 UTC cutoffs, 6.4 million dollars prefunding, and 220 milliseconds fallback latency. "
        "Fraud keeps the 0.8 percent review rate and 720 alert distinct from the 860 hold while customer states distinguish pending from settled. "
        "Security records 12:20 UTC token revocation, current K7, two hours break-glass access, dual approval, and seven years retention. "
        "Regulatory determination starts a seventy-two hours clock and treats 250,000 dollars as aggregate loss. "
        "Telemetry retains 97 percent coverage, 900 milliseconds alert, and 1,400 milliseconds hold; reconciliation keeps a 2.4 percent sample, 0.14 percent observation, and 0.05 percent release threshold. "
        "R5 and schema-13 govern rollback; each candidate effect makes earlier checks stale until effect uptake and recheck. "
        "Every blocker, falsifier, residual risk, and current candidate binding remains explicit. "
    )
    rows = [world.evaluator_config["decision_title"], ""]
    for index, heading in enumerate(world.decision_headings):
        body = core + citations
        if defective and index == 0:
            body += " The observed replication lag is 1,800 seconds."
        rows.extend([f"## {heading}", "", body, ""])
    return "\n".join(rows).rstrip() + "\n"


def evaluate_candidate(world: AsterWorld) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(TASK / "evaluator" / "evaluate.py"), str(world.candidate_root)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)


def externalize_fixture_record(
    *, record_id: str, record: object, ledger: ResultLedger
) -> None:
    from reactive_runtime.records import ResultRecord

    if not isinstance(record, ResultRecord):
        raise TypeError("record")
    messages = [
        {"role": "system", "content": "provider-free externalization fixture"},
        {"role": "user", "content": record.exact_content},
    ]
    ledger.mark_model_visible(record_id, call_index=1, message_index=1)
    def count(rows: list[dict[str, str]]) -> int:
        return sum(len(row["content"].encode("utf-8")) for row in rows)
    relief = positive_savings_first_fit_step(
        messages=messages,
        ledger=ledger,
        prompt_limit=count(messages) - 1,
        count_messages=count,
    )
    if relief.selected_result_ids != (record_id,):
        raise RuntimeError("provider-free fixture failed to externalize source result")


def provider_free_loop(
    configuration_id: str,
    root: Path,
    tokenizer: OfflineTokenizer,
    catalog: dict[str, dict[str, object]],
) -> dict[str, object]:
    world = AsterWorld(TASK, root / configuration_id, count_text=tokenizer.count_text)
    ledger = ResultLedger()
    register = ProvenanceRegister()
    maintenance_calls = 0
    next_result = 1
    prior_register_hashes: list[str] = []
    for pair in ACTIVATION_PATH[:5]:
        result_id = f"RESULT-{next_result:03d}"
        next_result += 1
        execution = world.execute(batch_action(pair, world), result_id=result_id, ledger=ledger)
        record = world.make_result_record(execution, result_id=result_id, acquired_call=next_result)
        ledger.add(record)
        externalize_fixture_record(record_id=result_id, record=record, ledger=ledger)
        if configuration_id == "L1_PROVENANCE_LOCAL_RELATIONAL":
            output = fixture_delta(world, result_id, pair)
            validation = validate_relational_delta(
                output,
                count_text=tokenizer.count_text,
                source_catalog=catalog,
                task_root=TASK,
                newly_externalized=(record,),
                current_source_versions=world.source_versions,
            )
            if not validation.valid:
                raise RuntimeError(f"fixture relational delta failed: {validation.issues}")
            prior_register_hashes.append(register.sha256)
            register = register.merge(
                validation,
                current_source_versions=world.source_versions,
                count_text=tokenizer.count_text,
            )
            maintenance_calls += 1

    world.execute(
        {"action": "replace_evidence_ledger", "content": fixture_ledger()},
        result_id=f"RESULT-{next_result:03d}",
        ledger=ledger,
    )
    world.execute(
        {"action": "replace_decision", "content": fixture_decision(world, defective=True)},
        result_id=f"RESULT-{next_result + 1:03d}",
        ledger=ledger,
    )
    first_check = world.execute(
        {"action": "run_check"}, result_id=f"RESULT-{next_result + 2:03d}", ledger=ledger
    )
    world.execute(
        {"action": "replace_decision", "content": fixture_decision(world, defective=False)},
        result_id=f"RESULT-{next_result + 3:03d}",
        ledger=ledger,
    )
    stale = world.current_check_binding()
    second_check = world.execute(
        {"action": "run_check"}, result_id=f"RESULT-{next_result + 4:03d}", ledger=ledger
    )
    current = world.current_check_binding()
    submission = world.execute(
        {"action": "submit"}, result_id=f"RESULT-{next_result + 5:03d}", ledger=ledger
    )
    final_evaluation = evaluate_candidate(world)
    return {
        "configuration_id": configuration_id,
        "source_results_externalized": 5,
        "semantic_register_claims": len(register.claims),
        "semantic_register_tokens": tokenizer.count_text(register.render()),
        "semantic_register_hash": register.sha256,
        "maintenance_calls": maintenance_calls,
        "prior_register_versions": len(prior_register_hashes),
        "first_check_passed": first_check.metadata["check_projection"]["passed"],
        "check_stale_after_repair": stale["currency"] == "stale",
        "recheck_passed": second_check.metadata["check_projection"]["passed"],
        "recheck_currency": current["currency"],
        "submission_kind": submission.result_kind,
        "submitted": world.submitted,
        "candidate_sha256": world.candidate_sha256,
        "mechanical_final_evaluation": final_evaluation,
    }


def main() -> int:
    verify_task_lock()
    catalog = source_catalog()
    tokenizer = OfflineTokenizer()
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        world = AsterWorld(TASK, temporary_root / "geometry")
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
            execution = world.execute(batch_action((left, right), world), result_id="GEOMETRY")
            record = world.make_result_record(execution, result_id="GEOMETRY", acquired_call=0)
            pair_rows.append(
                {
                    "source_ids": [left, right],
                    "result_tokens": tokenizer.count_text(record.exact_content),
                    "source_bytes": execution.metadata["total_source_bytes"],
                }
            )

        path_world = AsterWorld(TASK, temporary_root / "path")
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
                source_relief = [
                    selected
                    for selected in relief.selected_result_ids
                    if path_ledger.get(selected).result_kind == "source_observation"
                ]
                pressure = {
                    "step": step,
                    "pending_result_id": result_id,
                    "overflow_tokens": prompt_tokens - PROMPT_LIMIT,
                    "activation_snapshot": snapshot.as_dict(),
                    "positive_relief_result_ids": list(relief.selected_result_ids),
                    "externalized_source_result_ids": source_relief,
                    "positive_relief_after_tokens": relief.prompt_tokens,
                    "positive_relief_tokens": prompt_tokens - relief.prompt_tokens,
                }
                break
            path_ledger.mark_model_visible(
                record.result_id, call_index=step + 1, message_index=len(path_messages) - 1
            )

        register = ProvenanceRegister()
        maintenance_geometry = []
        for record in path_records:
            source_ids = tuple(str(value) for value in record.metadata["source_ids"])
            output = fixture_delta(path_world, record.result_id, source_ids)
            validation = validate_relational_delta(
                output,
                count_text=tokenizer.count_text,
                source_catalog=catalog,
                task_root=TASK,
                newly_externalized=(record,),
                current_source_versions=path_world.source_versions,
            )
            if not validation.valid:
                raise RuntimeError(f"prospective delta fixture failed: {validation.issues}")
            messages = relational_delta_messages(
                task_text=(TASK / "TASK.md").read_text(encoding="utf-8"),
                register=register,
                newly_externalized=(record,),
                source_versions=path_world.source_versions,
            )
            prompt_tokens = tokenizer.count_messages(messages)
            register = register.merge(
                validation,
                current_source_versions=path_world.source_versions,
                count_text=tokenizer.count_text,
            )
            maintenance_geometry.append(
                {
                    "result_id": record.result_id,
                    "source_ids": list(source_ids),
                    "prompt_tokens": prompt_tokens,
                    "completion_reserve": SOURCE_DELTA_PROVIDER_MAX_TOKENS,
                    "fits": prompt_tokens + SOURCE_DELTA_PROVIDER_MAX_TOKENS <= CONTEXT_TOKENS,
                    "register_tokens_after": tokenizer.count_text(register.render()),
                }
            )

        # Render the maximum one-claim-per-source stock prospectively.
        maximum_register = ProvenanceRegister()
        for pair in ACTIVATION_PATH:
            source_ids = tuple(pair)
            record = next(
                (row for row in path_records if tuple(row.metadata["source_ids"]) == source_ids),
                None,
            )
            if record is None:
                result_id = f"MAX-{source_ids[0]}-{source_ids[1]}"
                execution = path_world.execute(batch_action(pair, path_world), result_id=result_id, ledger=path_ledger)
                record = path_world.make_result_record(execution, result_id=result_id, acquired_call=0)
            output = fixture_delta(path_world, record.result_id, source_ids)
            validation = validate_relational_delta(
                output,
                count_text=tokenizer.count_text,
                source_catalog=catalog,
                task_root=TASK,
                newly_externalized=(record,),
                current_source_versions=path_world.source_versions,
            )
            maximum_register = maximum_register.merge(
                validation,
                current_source_versions=path_world.source_versions,
                count_text=tokenizer.count_text,
            )

        if pressure is None:
            raise RuntimeError("Aster prospective path did not reach pressure")
        first_externalized_id = pressure["externalized_source_result_ids"][0]
        first_externalized = path_ledger.get(first_externalized_id)
        first_source_ids = tuple(
            str(value) for value in first_externalized.metadata["source_ids"]
        )
        first_validation = validate_relational_delta(
            fixture_delta(path_world, first_externalized_id, first_source_ids),
            count_text=tokenizer.count_text,
            source_catalog=catalog,
            task_root=TASK,
            newly_externalized=(first_externalized,),
            current_source_versions=path_world.source_versions,
        )
        first_register = ProvenanceRegister().merge(
            first_validation,
            current_source_versions=path_world.source_versions,
            count_text=tokenizer.count_text,
        )
        first_transition_messages = [dict(message) for message in path_messages]
        first_transition_messages.append(
            {
                "role": "user",
                "content": "# Current non-authoritative provenance-local source register\n"
                + first_register.render(),
            }
        )
        first_transition_prompt_tokens = tokenizer.count_messages(
            first_transition_messages
        )

        schemas = {
            configuration_id: action_json_schema(
                relational_actor_actions(configuration_id),
                source_ids=world.sources,
                reopen_result_ids=(),
                decision_headings=world.decision_headings,
                schema_name=f"aster_{configuration_id.casefold()}_action_v0",
            )["json_schema"]["name"]
            for configuration_id in RELATIONAL_CONFIGURATIONS
        }
        parser_examples = [
            parse_action(
                canonical_json_text(
                    {
                        "action": "upsert_decision_section",
                        "heading": world.decision_headings[0],
                        "body": "bounded exact decision work [ANCHOR] [BRIDGE]",
                    }
                ),
                relational_actor_actions("W0_DIRECT_EXACT_WORK"),
                decision_headings=world.decision_headings,
            ),
            parse_action(
                '{"action":"run_check"}',
                relational_actor_actions("L1_PROVENANCE_LOCAL_RELATIONAL"),
                decision_headings=world.decision_headings,
            ),
        ]
        fixtures = [
            provider_free_loop(configuration_id, temporary_root / "fixtures", tokenizer, catalog)
            for configuration_id in RELATIONAL_CONFIGURATIONS
        ]

    if len(pressure["activation_snapshot"]["qualifying_sources"]) < 4:
        raise RuntimeError("Aster pressure occurs before source coverage activation")
    if len(pressure["activation_snapshot"]["qualifying_domains"]) < 3:
        raise RuntimeError("Aster pressure occurs before domain activation")
    if not pressure["externalized_source_result_ids"]:
        raise RuntimeError("Aster relief externalizes no source result")
    if pressure["positive_relief_after_tokens"] > PROMPT_LIMIT:
        raise RuntimeError("Aster pressure lacks feasible positive relief")
    if not all(row["fits"] for row in maintenance_geometry):
        raise RuntimeError("Aster provenance maintenance prompt is infeasible")
    if tokenizer.count_text(maximum_register.render()) > REGISTER_TOKEN_BUDGET:
        raise RuntimeError("Aster maximum register exceeds stock budget")
    if first_transition_prompt_tokens > PROMPT_LIMIT:
        raise RuntimeError("Aster first treatment register cannot enter actor context")
    for row in fixtures:
        expected_claims = 0 if row["configuration_id"] == "W0_DIRECT_EXACT_WORK" else 10
        if not (
            row["semantic_register_claims"] == expected_claims
            and row["first_check_passed"] is False
            and row["check_stale_after_repair"]
            and row["recheck_passed"] is True
            and row["recheck_currency"] == "current"
            and row["submitted"]
            and row["mechanical_final_evaluation"]["passed"]
            and row["mechanical_final_evaluation"]["closure_readiness"] == "not_adjudicated"
        ):
            raise RuntimeError(f"provider-free loop failed: {row['configuration_id']}")
    if fixtures[0]["candidate_sha256"] != fixtures[1]["candidate_sha256"]:
        raise RuntimeError("provider-free arm candidates diverged")

    result = {
        "schema": "aster-provenance-local-relational-stage0-v0",
        "task_id": TASK_ID,
        "task_source_lock_sha256": sha256_file(TASK / "TASK_SOURCE_LOCK.json"),
        "model_profile_lock_sha256": sha256_file(ROOT / "ASTER_MODEL_PROFILE_LOCK.json"),
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
        "provenance_maintenance_geometry": maintenance_geometry,
        "first_treatment_transition": {
            "externalized_result_ids": [first_externalized_id],
            "source_ids": list(first_source_ids),
            "relieved_prompt_tokens_before_register": pressure[
                "positive_relief_after_tokens"
            ],
            "register_tokens": tokenizer.count_text(first_register.render()),
            "actor_prompt_tokens_after_register": first_transition_prompt_tokens,
            "fits": first_transition_prompt_tokens <= PROMPT_LIMIT,
        },
        "provenance_contract": {
            "total_delta_token_budget": SOURCE_DELTA_TOKEN_BUDGET,
            "provider_completion_tokens": SOURCE_DELTA_PROVIDER_MAX_TOKENS,
            "per_source_slot_token_budget": SOURCE_SLOT_TOKEN_BUDGET,
            "register_token_budget": REGISTER_TOKEN_BUDGET,
            "maximum_register_fixture_tokens": tokenizer.count_text(maximum_register.render()),
            "source_slot_mutation_only": True,
            "relationship_referents_permitted_when_owner_evidence_grounded": True,
            "cross_source_synthesis_location": "exact_task_native_candidate_work",
            "readiness_authority": False,
            "semantic_truth_validated_mechanically": False,
        },
        "provider_free_complete_system_fixtures": fixtures,
        "dynamic_action_parser_cases": parser_examples,
        "dynamic_action_schema_names": schemas,
        "trajectory_budget": {
            **ConstructionBudget(maximum_preconstruction_calls=36, postconstruction_calls=12).as_dict(),
            "protected_postconstruction_tail_calls": 12,
            "tail_operations": ["effect_uptake", "check", "repair", "recheck", "closure"],
            "maximum_maintenance_calls_L1": 12,
            "W0_maximum_provider_calls": 48,
            "L1_maximum_provider_calls": 60,
        },
        "evaluator": {
            "candidate_bound": True,
            "mechanical_check_cannot_return_ready": True,
            "independent_readiness_required": True,
            "gold_requirement_source_map_actor_visible": False,
            "semantic_adjudication_must_be_condition_blinded_where_feasible": True,
        },
        "authentic_activation_qualified": False,
        "next_live_operation": "ordinary_common_pressure_screen_only",
        "maximum_expression_qualification_calls_after_pressure": 1,
        "measured_continuation_authorized": False,
        "gpu_authorized": False,
        "provider_calls": 0,
    }
    write_json(ROOT / "ASTER_STAGE0_PREFLIGHT.json", result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
