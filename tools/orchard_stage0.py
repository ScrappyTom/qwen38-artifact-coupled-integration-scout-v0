from __future__ import annotations

import json
import re
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.anchored_provenance import (
    DELTA_PREFIX,
    AnchoredProvenanceRegister,
    admit_anchored_delta,
)
from reactive_runtime.canonical import canonical_json_text, sha256_file, write_json
from reactive_runtime.orchard_world import OrchardWorld
from reactive_runtime.phase_lifecycle import p1_verification_messages
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
from tools.materialize_orchard_world import SOURCE_IDS, SPECS
from tools.offline_tokenizer import OfflineTokenizer


TASK = ROOT / "task_orchard"
TASK_ID = "orchard-biologics-restart-decision-v0"
PROMPT_LIMIT = 20_992
CONTEXT_TOKENS = 25_088
ACTOR_MAX_TOKENS = 4_096
MAINTENANCE_MAX_TOKENS = 1_800
CONFIGURATION_ORDER = (
    "F0_FIXED_SCAFFOLD_APPEND_ONLY_VERIFICATION",
    "P1_PHASE_CONDITIONAL_CURRENT_VERIFICATION",
)
ACTIVATION_PATH = tuple(
    (SOURCE_IDS[index], SOURCE_IDS[index + 1])
    for index in range(0, 12, 2)
) + ((SOURCE_IDS[-1],),)


def catalog() -> dict[str, dict[str, object]]:
    value = json.loads((TASK / "SOURCE_CATALOG.json").read_text(encoding="utf-8"))
    return {row["source_id"]: row for row in value["sources"]}


def base_messages(world: OrchardWorld) -> list[dict[str, str]]:
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


def batch_action(pair: tuple[str, ...], world: OrchardWorld) -> dict[str, object]:
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


def fixture_delta(world: OrchardWorld, result_id: str, source_ids: tuple[str, ...]) -> str:
    blocks: list[str] = []
    all_ids = tuple(world.sources)
    for source_id in source_ids:
        source = world.sources[source_id]
        relation = source.lines[source.lines.index("## Governing relationships") + 2]
        referents = _referents(relation, all_ids, source_id)
        blocks.append(
            "\n".join(
                (
                    f"## CLAIM {source_id}_FIXTURE",
                    f"SLOT_SOURCE: {source_id}",
                    f"SOURCE_VERSION: {source.sha256}",
                    f"EVIDENCE_RESULT: {result_id}",
                    f"EVIDENCE_ANCHOR: {relation}",
                    "MODE: source_reported_relationship",
                    "ATTRIBUTION: owner_source_reported",
                    f"REFERENTS: {','.join(referents) if referents else 'NONE'}",
                    "AUTHORITY: non_authoritative_derivative",
                    f"STATEMENT: {source_id} reports: {relation}",
                )
            )
        )
    return DELTA_PREFIX + "\n" + "\n".join(blocks)


def fixture_ledger() -> str:
    citations = " ".join(f"[{source_id}]" for source_id in SOURCE_IDS)
    return (
        "# Orchard Evidence and Decision Matrix\n\n"
        "Current exact task work binds restart authority, process and batch genealogy, aseptic controls, cold chain, utilities, quality disposition, cyber state, supplies, safety, telemetry, communication, change lineage, and independent readiness. "
        + citations
        + "\n"
    )


def fixture_decision(*, defective: bool) -> str:
    config = json.loads((TASK / "EVALUATOR.json").read_text(encoding="utf-8"))
    grouped = [[], [], [], [], [], [], [], []]
    for index, spec in enumerate(SPECS):
        text = " ".join((*spec.findings, *spec.relationships, f"[{spec.source_id}]"))
        grouped[index % len(grouped)].append(text)
    control = (
        "The accountable owner records the prerequisite, exact observation, candidate version, uncertainty, falsifier, pause condition, rollback action, and evidence required to retire the temporary control. "
        "Exact source and event custody remains externally reopenable; model-authored semantic state is incomplete and non-authoritative. "
    )
    sections = []
    for heading, chunks in zip(config["decision_headings"], grouped):
        sections.append(f"## {heading}\n\n" + " ".join(chunks) + " " + control)
    decision = config["decision_title"] + "\n\n" + "\n\n".join(sections) + "\n"
    if defective:
        decision = decision.replace("two consecutive engineering batches", "one engineering batch", 1)
        decision = decision.replace("at every return point", "on average", 1)
        decision = decision.replace("0.50 EU/mL method is superseded", "0.50 EU/mL current limit", 1)
    return decision


def repair_action() -> dict[str, Any]:
    return {
        "action": "patch_decision",
        "edits": [
            {"old": "The restart gate is at least 68 percent yield in one engineering batch", "new": "The restart gate is at least 68 percent yield in two consecutive engineering batches"},
            {"old": "requires at least 80 degrees on average for three consecutive thirty-minute windows", "new": "requires at least 80 degrees at every return point for three consecutive thirty-minute windows"},
            {"old": "A legacy 0.50 EU/mL current limit and cannot govern current release", "new": "A legacy 0.50 EU/mL method is superseded and cannot govern current release"},
        ],
    }


def execute_and_record(world: OrchardWorld, ledger: ResultLedger, action: dict[str, Any], result_id: str, call: int):
    execution = world.execute(action, result_id=result_id, ledger=ledger)
    record = world.make_result_record(execution, result_id=result_id, acquired_call=call)
    ledger.add(record)
    return record


def provider_free_lifecycle(configuration_id: str, root: Path, tokenizer: OfflineTokenizer) -> dict[str, object]:
    world = OrchardWorld(TASK, root / configuration_id, count_text=tokenizer.count_text)
    ledger = ResultLedger()
    register = AnchoredProvenanceRegister()
    source_record = execute_and_record(world, ledger, batch_action(("CHARTER", "CULTURE"), world), "RESULT-001", 1)
    ledger.mark_model_visible("RESULT-001", call_index=2, message_index=0)
    ledger.mark_external("RESULT-001")
    admission = admit_anchored_delta(
        fixture_delta(world, "RESULT-001", ("CHARTER", "CULTURE")),
        count_text=tokenizer.count_text,
        source_catalog=catalog(),
        task_root=TASK,
        newly_externalized=(source_record,),
        current_source_versions=world.source_versions,
    )
    register = register.apply(admission, current_source_versions=world.source_versions, count_text=tokenizer.count_text).register
    execute_and_record(world, ledger, {"action": "replace_evidence_ledger", "content": fixture_ledger()}, "RESULT-002", 2)
    execute_and_record(world, ledger, {"action": "replace_decision", "content": fixture_decision(defective=True)}, "RESULT-003", 3)
    milestone = world.construction_milestone()
    phase = execute_and_record(world, ledger, {"action": "begin_verification"}, "RESULT-004", 4)
    ledger.mark_model_visible("RESULT-004", call_index=5, message_index=0)
    if configuration_id.startswith("P1_"):
        messages = p1_verification_messages(
            task_system=(TASK / "SYSTEM.md").read_text(encoding="utf-8"),
            task_text=(TASK / "TASK.md").read_text(encoding="utf-8"),
            action_text=(TASK / "VERIFICATION_ACTIONS.md").read_text(encoding="utf-8"),
            source_catalog=world.source_catalog_for_actor(),
            world=world,
            ledger=ledger,
            pending_result_id=None,
            latest_effect_result_id=phase.result_id,
            full_history_handle="fixture://orchard/full-history",
            scaffold_handle=f"semantic-register://{register.sha256}",
        )
    else:
        messages = base_messages(world) + [
            {"role": "user", "content": register.render()},
            {"role": "user", "content": phase.exact_content},
        ]
    initial_prompt = tokenizer.count_messages(messages)
    first_check = execute_and_record(world, ledger, {"action": "run_check"}, "RESULT-005", 5)
    first_blockers = first_check.metadata["check_projection"]["blocking_requirements"]
    if configuration_id.startswith("P1_"):
        messages = p1_verification_messages(
            task_system=(TASK / "SYSTEM.md").read_text(encoding="utf-8"),
            task_text=(TASK / "TASK.md").read_text(encoding="utf-8"),
            action_text=(TASK / "VERIFICATION_ACTIONS.md").read_text(encoding="utf-8"),
            source_catalog=world.source_catalog_for_actor(),
            world=world,
            ledger=ledger,
            pending_result_id="RESULT-005",
            latest_effect_result_id="RESULT-004",
            full_history_handle="fixture://orchard/full-history",
            scaffold_handle=f"semantic-register://{register.sha256}",
        )
    else:
        messages += [{"role": "assistant", "content": canonical_json_text({"action": "run_check"})}, {"role": "user", "content": first_check.exact_content}]
    after_check_prompt = tokenizer.count_messages(messages)
    ledger.mark_model_visible("RESULT-005", call_index=6, message_index=len(messages) - 1)
    patch = execute_and_record(world, ledger, repair_action(), "RESULT-006", 6)
    stale = world.current_check_binding()
    if configuration_id.startswith("P1_"):
        messages = p1_verification_messages(
            task_system=(TASK / "SYSTEM.md").read_text(encoding="utf-8"), task_text=(TASK / "TASK.md").read_text(encoding="utf-8"),
            action_text=(TASK / "VERIFICATION_ACTIONS.md").read_text(encoding="utf-8"), source_catalog=world.source_catalog_for_actor(),
            world=world, ledger=ledger, pending_result_id="RESULT-006", latest_effect_result_id="RESULT-006",
            full_history_handle="fixture://orchard/full-history", scaffold_handle=f"semantic-register://{register.sha256}",
        )
    else:
        messages += [{"role": "assistant", "content": canonical_json_text(repair_action())}, {"role": "user", "content": patch.exact_content}]
    after_patch_prompt = tokenizer.count_messages(messages)
    ledger.mark_model_visible("RESULT-006", call_index=7, message_index=len(messages) - 1)
    recheck = execute_and_record(world, ledger, {"action": "run_check"}, "RESULT-007", 7)
    if configuration_id.startswith("P1_"):
        messages = p1_verification_messages(
            task_system=(TASK / "SYSTEM.md").read_text(encoding="utf-8"), task_text=(TASK / "TASK.md").read_text(encoding="utf-8"),
            action_text=(TASK / "VERIFICATION_ACTIONS.md").read_text(encoding="utf-8"), source_catalog=world.source_catalog_for_actor(),
            world=world, ledger=ledger, pending_result_id="RESULT-007", latest_effect_result_id="RESULT-006",
            full_history_handle="fixture://orchard/full-history", scaffold_handle=f"semantic-register://{register.sha256}",
        )
    else:
        messages += [{"role": "assistant", "content": canonical_json_text({"action": "run_check"})}, {"role": "user", "content": recheck.exact_content}]
    after_recheck_prompt = tokenizer.count_messages(messages)
    ledger.mark_model_visible("RESULT-007", call_index=8, message_index=len(messages) - 1)
    submission = execute_and_record(world, ledger, {"action": "submit"}, "RESULT-008", 8)
    return {
        "configuration_id": configuration_id,
        "construction_milestone": milestone,
        "register_claims": len(register.claims),
        "register_tokens": tokenizer.count_text(register.render()),
        "first_check_blocking_ids": sorted(row.split(":", 1)[0] for row in first_blockers),
        "prior_check_stale_after_patch": stale is not None and stale["currency"] == "stale",
        "recheck_passed": recheck.metadata["check_projection"]["passed"],
        "recheck_blockers": recheck.metadata["check_projection"]["blocking_requirements"],
        "submitted": world.submitted,
        "submission_kind": submission.result_kind,
        "prompt_tokens": {
            "initial_verification": initial_prompt,
            "after_check": after_check_prompt,
            "after_patch": after_patch_prompt,
            "after_recheck": after_recheck_prompt,
        },
        "final_candidate_sha256": world.candidate_sha256,
    }


def verify_task_lock() -> None:
    lock = json.loads((TASK / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
    if lock.get("task_id") != TASK_ID:
        raise RuntimeError("Orchard task lock identity mismatch")
    for row in lock["files"]:
        path = TASK / row["path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise RuntimeError(f"Orchard task lock mismatch: {row['path']}")


def main() -> int:
    verify_task_lock()
    tokenizer = OfflineTokenizer()
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        world = OrchardWorld(TASK, root / "geometry")
        source_rows = [
            {"source_id": source_id, "source_tokens": tokenizer.count_text(source.path.read_text(encoding="utf-8")), "source_bytes": source.size_bytes, "line_count": len(source.lines)}
            for source_id, source in world.sources.items()
        ]
        messages = base_messages(world)
        ledger = ResultLedger()
        path_rows = []
        pressure = None
        for step, pair in enumerate(ACTIVATION_PATH, start=1):
            action = batch_action(pair, world)
            messages.append({"role": "assistant", "content": canonical_json_text(action)})
            record = execute_and_record(world, ledger, action, f"RESULT-{step:03d}", step)
            messages.append({"role": "user", "content": record.exact_content})
            tokens = tokenizer.count_messages(messages)
            path_rows.append({"step": step, "source_ids": list(pair), "prompt_tokens": tokens, "fits": tokens <= PROMPT_LIMIT})
            if tokens > PROMPT_LIMIT:
                relief = positive_savings_first_fit_step(messages=messages, ledger=ledger, prompt_limit=PROMPT_LIMIT, count_messages=tokenizer.count_messages, protected_result_ids=(record.result_id,))
                pressure = {"step": step, "pending_result_id": record.result_id, "ordinary_prompt_tokens": tokens, "overflow_tokens": tokens - PROMPT_LIMIT, "selected_result_ids": list(relief.selected_result_ids), "relieved_prompt_tokens": relief.prompt_tokens, "feasible": relief.feasible}
                break
            ledger.mark_model_visible(record.result_id, call_index=step + 1, message_index=len(messages) - 1)
        if pressure is None or not pressure["feasible"]:
            failures.append("no_feasible_prospective_pressure")

        lifecycles = [provider_free_lifecycle(configuration_id, root / "fixtures", tokenizer) for configuration_id in CONFIGURATION_ORDER]
        if not all(row["construction_milestone"]["passed"] and row["recheck_passed"] and row["submitted"] for row in lifecycles):
            failures.append("provider_free_lifecycle_failed")
        if lifecycles[0]["final_candidate_sha256"] != lifecycles[1]["final_candidate_sha256"]:
            failures.append("provider_free_final_candidate_mismatch")
        if max(lifecycles[1]["prompt_tokens"].values()) > PROMPT_LIMIT:
            failures.append("p1_projection_infeasible")

        valid = fixture_decision(defective=False)
        relation_checks = []
        for name, old, new, expected_gate in (
            ("yield_gate", "two consecutive engineering batches", "one 72 percent batch is sufficient", "R02_process"),
            ("aseptic_limit", "The action limit is 1 CFU per cubic meter in Grade A active air", "The 3 CFU Grade A action applies", "R03_aseptic"),
            ("power_capacity", "currently usable capacity must not be swapped or added together", "7.1 plus 5.4 MW is available", "power_sum_reversal"),
            ("quality_limit", "0.50 EU/mL method is superseded", "0.50 EU/mL current limit", "quality_limit_reversal"),
        ):
            check_world = OrchardWorld(TASK, root / f"red-team-{name}")
            check_world.execute({"action": "replace_evidence_ledger", "content": fixture_ledger()}, result_id="R-LEDGER")
            check_world.execute({"action": "replace_decision", "content": valid.replace(old, new, 1)}, result_id="R-DECISION")
            result = check_world.execute({"action": "run_check"}, result_id="R-CHECK")
            blockers = [row.split(":", 1)[0] for row in result.metadata["check_projection"]["blocking_requirements"]]
            relation_checks.append({"case": name, "expected_gate": expected_gate, "blocking_ids": blockers, "caught": expected_gate in blockers})
        if not all(row["caught"] for row in relation_checks):
            failures.append("relationship_red_team_not_caught")

        preflight = {
            "schema": "orchard-phase-conditional-lifecycle-stage0-v0",
            "task_id": TASK_ID,
            "provider_calls": 0,
            "gpu_authorized": False,
            "passed": not failures,
            "failures": failures,
            "source_geometry": {"source_count": len(source_rows), "total_source_bytes": sum(row["source_bytes"] for row in source_rows), "total_source_tokens": sum(row["source_tokens"] for row in source_rows), "sources": source_rows},
            "prospective_pressure_opportunity": pressure,
            "prospective_path": path_rows,
            "provider_free_lifecycles": lifecycles,
            "relationship_red_team": relation_checks,
            "budgets": {"pressure_screen_actor_calls": 30, "measured_actor_calls_per_cell": 36, "measured_maintenance_calls_per_cell": 12, "maximum_measured_provider_calls": 96, "attempts_per_call": 1, "retries": 0},
            "claim_limit": "Provider-free qualification of a fresh whole-system lifecycle, prospective pressure, relational feedback, mechanical phase transition, scaffold demotion, verification-state replacement, exact repair, current recheck, and submission mechanics. It provides no live model behavior or utility evidence.",
        }
    write_json(ROOT / "ORCHARD_PHASE_LIFECYCLE_STAGE0_PREFLIGHT.json", preflight)
    if failures:
        raise RuntimeError(f"Orchard Stage 0 failed: {failures}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
