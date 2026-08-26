from __future__ import annotations

import itertools
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.actions import MAX_BATCH_SOURCE_BYTES, MAX_SOURCE_RESULT_TOKENS
from reactive_runtime.anchored_provenance import (
    DELTA_PREFIX,
    AnchoredProvenanceRegister,
    admit_anchored_delta,
    anchored_delta_messages,
)
from reactive_runtime.canonical import canonical_json_text, sha256_file, write_json
from reactive_runtime.configuration import (
    ANCHORED_RELATIONAL_CONFIGURATIONS,
    anchored_relational_actor_actions,
)
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
from reactive_runtime.solace_world import SolaceWorld
from tools.offline_tokenizer import OfflineTokenizer
from tools.materialize_solace_world import SPECS


TASK = ROOT / "task_solace"
TASK_ID = "solace-water-recovery-decision-v0"
PROMPT_LIMIT = 20_992
CONTEXT_TOKENS = 25_088
MAINTENANCE_MAX_TOKENS = 1_800
ACTIVATION_PATH = tuple(
    (SPECS[index].source_id, SPECS[index + 1].source_id)
    for index in range(0, len(SPECS), 2)
)


def catalog() -> dict[str, dict[str, object]]:
    value = json.loads((TASK / "SOURCE_CATALOG.json").read_text(encoding="utf-8"))
    return {row["source_id"]: row for row in value["sources"]}


def base_messages(world: SolaceWorld) -> list[dict[str, str]]:
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


def batch_action(pair: tuple[str, str], world: SolaceWorld) -> dict[str, object]:
    return {
        "action": "read_batch",
        "requests": [
            {"source_id": source_id, "start_line": 1, "end_line": len(world.sources[source_id].lines)}
            for source_id in pair
        ],
    }


def _referents(text: str, source_ids: tuple[str, ...], owner: str) -> tuple[str, ...]:
    return tuple(
        source_id
        for source_id in source_ids
        if source_id != owner and re.search(rf"(?<![A-Z0-9_-]){source_id}(?![A-Z0-9_-])", text)
    )


def fixture_delta(world: SolaceWorld, result_id: str, source_ids: tuple[str, ...]) -> str:
    blocks: list[str] = []
    all_ids = tuple(world.sources)
    for source_id in source_ids:
        source = world.sources[source_id]
        relation = source.lines[source.lines.index("## Governing relationships") + 2]
        referents = _referents(relation, all_ids, source_id)
        if referents:
            anchor = relation
            mode = "source_reported_relationship"
            statement = f"{source_id} reports: {relation}"
            rendered_referents = ",".join(referents)
        else:
            anchor = source.lines[source.lines.index("## Frozen findings") + 2].split(". ", 1)[0] + "."
            mode = "source_reported_fact"
            statement = f"{source_id} reports: {anchor}"
            rendered_referents = "NONE"
        blocks.append(
            "\n".join(
                (
                    f"## CLAIM {source_id}_FIXTURE",
                    f"SLOT_SOURCE: {source_id}",
                    f"SOURCE_VERSION: {source.sha256}",
                    f"EVIDENCE_RESULT: {result_id}",
                    f"EVIDENCE_ANCHOR: {anchor}",
                    f"MODE: {mode}",
                    "ATTRIBUTION: owner_source_reported",
                    f"REFERENTS: {rendered_referents}",
                    "AUTHORITY: non_authoritative_derivative",
                    f"STATEMENT: {statement}",
                )
            )
        )
    return DELTA_PREFIX + "\n" + "\n".join(blocks)


def fixture_ledger() -> str:
    return """# Solace Evidence and Decision Matrix

Current exact task work links authority, hydraulics, sampling, pumping, power,
treatment, source water, access, telemetry, environmental reporting, logistics,
communications, candidate lineage, and independent review [AURORA] [BASTION]
[CIPHER] [DELTA] [ECHO] [FALCON] [GARNET] [HELIX] [INDIGO] [JASPER]
[KESTREL] [LUMEN] [MOSAIC] [NEXUS].
"""


def fixture_decision(world: SolaceWorld, *, defective: bool) -> str:
    config = world.evaluator_config
    required = " ".join(term for terms in config["semantic_term_gates"].values() for term in terms)
    citations = " ".join(f"[{source_id}]" for source_id in config["source_ids"])
    neutral = (
        "The owner records inputs, resources, timing, dependencies, observations, "
        "effects, uncertainty, contingencies, rollback conditions, retirement evidence, "
        "and a falsifier bound to the current candidate. Exact source custody remains "
        "reopenable, while any semantic residue remains incomplete and non-authoritative. "
    )
    sections = []
    for index, heading in enumerate(config["decision_headings"]):
        seed = required + " " + citations if index == 0 else ""
        sections.append(f"## {heading}\n\n{seed} " + neutral * 6)
    decision = config["decision_title"] + "\n\n" + "\n\n".join(sections) + "\n"
    if defective:
        decision = decision.replace("42 psi", "42 kPa", 1)
    return decision


def provider_free_loop(configuration_id: str, root: Path, tokenizer: OfflineTokenizer, source_catalog: dict[str, dict[str, object]]) -> dict[str, object]:
    world = SolaceWorld(TASK, root / configuration_id, count_text=tokenizer.count_text)
    ledger = ResultLedger()
    register = AnchoredProvenanceRegister()
    execution = world.execute(batch_action(ACTIVATION_PATH[0], world), result_id="RESULT-001", ledger=ledger)
    record = world.make_result_record(execution, result_id="RESULT-001", acquired_call=1)
    ledger.add(record)
    if configuration_id == "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE":
        text = fixture_delta(world, record.result_id, ACTIVATION_PATH[0])
        admission = admit_anchored_delta(
            text,
            count_text=tokenizer.count_text,
            source_catalog=source_catalog,
            task_root=TASK,
            newly_externalized=(record,),
            current_source_versions=world.source_versions,
        )
        register = register.apply(
            admission,
            current_source_versions=world.source_versions,
            count_text=tokenizer.count_text,
        ).register
    world.execute({"action": "replace_evidence_ledger", "content": fixture_ledger()}, result_id="RESULT-002", ledger=ledger)
    world.execute({"action": "replace_decision", "content": fixture_decision(world, defective=True)}, result_id="RESULT-003", ledger=ledger)
    first = world.execute({"action": "run_check"}, result_id="RESULT-004", ledger=ledger)
    world.execute({"action": "replace_decision", "content": fixture_decision(world, defective=False)}, result_id="RESULT-005", ledger=ledger)
    stale = world.current_check_binding()
    second = world.execute({"action": "run_check"}, result_id="RESULT-006", ledger=ledger)
    submission = world.execute({"action": "submit"}, result_id="RESULT-007", ledger=ledger)
    return {
        "configuration_id": configuration_id,
        "register_claims": len(register.claims),
        "first_check_passed": first.metadata["check_projection"]["passed"],
        "check_stale_after_repair": stale["currency"] == "stale",
        "recheck_passed": second.metadata["check_projection"]["passed"],
        "recheck_blocking": second.metadata["check_projection"]["blocking_requirements"],
        "submitted": world.submitted,
        "submission_kind": submission.result_kind,
        "candidate_sha256": world.candidate_sha256,
    }


def verify_task_lock() -> None:
    lock = json.loads((TASK / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
    if lock.get("task_id") != TASK_ID:
        raise RuntimeError("Solace task lock identity mismatch")
    for row in lock["files"]:
        path = TASK / row["path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise RuntimeError(f"Solace task lock mismatch: {row['path']}")


def main() -> int:
    verify_task_lock()
    source_catalog = catalog()
    tokenizer = OfflineTokenizer()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        world = SolaceWorld(TASK, root / "geometry")
        messages = base_messages(world)
        base_prompt = tokenizer.count_messages(messages)
        source_rows = [
            {
                "source_id": source_id,
                "source_tokens": tokenizer.count_text(source.path.read_text(encoding="utf-8")),
                "source_bytes": source.size_bytes,
                "line_count": len(source.lines),
            }
            for source_id, source in world.sources.items()
        ]
        path_world = SolaceWorld(TASK, root / "path")
        path_messages = base_messages(path_world)
        path_ledger = ResultLedger()
        path_rows: list[dict[str, object]] = []
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
            path_rows.append({"step": step, "source_ids": list(pair), "prompt_tokens": prompt_tokens, "fits": prompt_tokens <= PROMPT_LIMIT})
            if prompt_tokens > PROMPT_LIMIT:
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
                    "ordinary_prompt_tokens": prompt_tokens,
                    "overflow_tokens": prompt_tokens - PROMPT_LIMIT,
                    "selected_result_ids": list(relief.selected_result_ids),
                    "relieved_prompt_tokens": relief.prompt_tokens,
                    "externalized_source_result_ids": [
                        selected for selected in relief.selected_result_ids
                        if path_ledger.get(selected).result_kind == "source_observation"
                    ],
                }
                break
            path_ledger.mark_model_visible(result_id, call_index=step + 1, message_index=len(path_messages) - 1)

        if pressure is None or pressure["relieved_prompt_tokens"] > PROMPT_LIMIT or not pressure["externalized_source_result_ids"]:
            raise RuntimeError("Solace prospective path lacks feasible authentic-pressure opportunity")

        maintenance_rows = []
        register = AnchoredProvenanceRegister()
        for record in path_records:
            source_ids = tuple(str(value) for value in record.metadata["source_ids"])
            text = fixture_delta(path_world, record.result_id, source_ids)
            admission = admit_anchored_delta(
                text,
                count_text=tokenizer.count_text,
                source_catalog=source_catalog,
                task_root=TASK,
                newly_externalized=(record,),
                current_source_versions=path_world.source_versions,
            )
            transition = register.apply(
                admission,
                current_source_versions=path_world.source_versions,
                count_text=tokenizer.count_text,
            )
            register = transition.register
            maintenance_prompt = tokenizer.count_messages(
                anchored_delta_messages(
                    task_text=(TASK / "TASK.md").read_text(encoding="utf-8"),
                    register=register,
                    newly_externalized=(record,),
                    source_versions=path_world.source_versions,
                )
            )
            maintenance_rows.append(
                {
                    "result_id": record.result_id,
                    "source_ids": list(source_ids),
                    "disposition": admission.disposition,
                    "admitted_claims": len(admission.admitted_claims),
                    "prompt_tokens": maintenance_prompt,
                    "fits": maintenance_prompt + MAINTENANCE_MAX_TOKENS <= CONTEXT_TOKENS,
                    "register_tokens": tokenizer.count_text(register.render()),
                }
            )

        # Deliberately mix one valid and one invalid record, then prove zero-valid fallback.
        first_record = path_records[0]
        first_ids = tuple(str(value) for value in first_record.metadata["source_ids"])
        good = fixture_delta(path_world, first_record.result_id, (first_ids[0],))
        bad_block = fixture_delta(path_world, first_record.result_id, (first_ids[1],)).split("\n", 1)[1].replace(
            "EVIDENCE_ANCHOR: ", "EVIDENCE_ANCHOR: definitely absent ", 1
        )
        partial = admit_anchored_delta(
            good + "\n" + bad_block,
            count_text=tokenizer.count_text,
            source_catalog=source_catalog,
            task_root=TASK,
            newly_externalized=(first_record,),
            current_source_versions=path_world.source_versions,
        )
        zero = admit_anchored_delta(
            DELTA_PREFIX + "\n" + bad_block,
            count_text=tokenizer.count_text,
            source_catalog=source_catalog,
            task_root=TASK,
            newly_externalized=(first_record,),
            current_source_versions=path_world.source_versions,
        )
        baseline = AnchoredProvenanceRegister()
        zero_transition = baseline.apply(
            zero,
            current_source_versions=path_world.source_versions,
            count_text=tokenizer.count_text,
        )
        fixtures = [
            provider_free_loop(configuration_id, root / "fixtures", tokenizer, source_catalog)
            for configuration_id in ANCHORED_RELATIONAL_CONFIGURATIONS
        ]

    if not all(row["fits"] for row in maintenance_rows):
        raise RuntimeError("Solace maintenance geometry does not fit")
    if partial.disposition != "partial_admission" or len(partial.admitted_claims) != 1:
        raise RuntimeError("Solace partial-admission fixture failed")
    if zero.disposition != "zero_valid" or zero_transition.changed:
        raise RuntimeError("Solace zero-valid fallback failed")
    for fixture in fixtures:
        expected = 0 if fixture["configuration_id"].startswith("W0") else 2
        if not (
            fixture["register_claims"] == expected
            and fixture["first_check_passed"] is False
            and fixture["check_stale_after_repair"]
            and fixture["recheck_passed"]
            and fixture["submitted"]
        ):
            raise RuntimeError(f"Solace provider-free lifecycle failed: {fixture}")
    if fixtures[0]["candidate_sha256"] != fixtures[1]["candidate_sha256"]:
        raise RuntimeError("Solace provider-free arm candidates diverged")

    result = {
        "schema": "solace-fault-tolerant-anchored-provenance-stage0-v0",
        "task_id": TASK_ID,
        "task_source_lock_sha256": sha256_file(TASK / "TASK_SOURCE_LOCK.json"),
        "base_actor_prompt_tokens": base_prompt,
        "source_corpus_tokens": sum(row["source_tokens"] for row in source_rows),
        "source_corpus_bytes": sum(row["source_bytes"] for row in source_rows),
        "source_rows": source_rows,
        "prospective_activation_path": path_rows,
        "prospective_pressure_opportunity": pressure,
        "maintenance_geometry": maintenance_rows,
        "partial_admission_fixture": {
            "disposition": partial.disposition,
            "admitted_claim_ids": [claim.claim_id for claim in partial.admitted_claims],
            "rejected_claim_ids": [record.claim_id for record in partial.rejected_claims],
        },
        "zero_valid_fallback": {
            "disposition": zero.disposition,
            "register_changed": zero_transition.changed,
        },
        "provider_free_complete_system_fixtures": fixtures,
        "configurations": list(ANCHORED_RELATIONAL_CONFIGURATIONS),
        "comparison_rule": "same_pressure_relief_and_exact_task_work; treatment_adds_fallible_partial_admission_maintenance",
        "expression_gate": "none; maintenance_yield_is_measured_inside_the_system",
        "gpu_authorized": False,
    }
    write_json(ROOT / "SOLACE_STAGE0_PREFLIGHT.json", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
