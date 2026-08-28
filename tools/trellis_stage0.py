from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.anchored_provenance import AnchoredProvenanceRegister, DELTA_PREFIX
from reactive_runtime.canonical import canonical_json_text, sha256_file, write_json
from reactive_runtime.configuration import ARTIFACT_CENTERED_LIFECYCLE_CONFIGURATIONS
from reactive_runtime.keystone_world import KeystoneWorld
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
from reactive_runtime.task_coupled_scaffold import admit_task_coupled_delta, requirement_index
from reactive_runtime.verification_causal_frame import section_spans, sha256_text
from tools.materialize_trellis_world import SOURCE_IDS, SPECS
from tools.offline_tokenizer import OfflineTokenizer


TASK = ROOT / "task_trellis"
TASK_ID = "trellis-heat-continuity-decision-v0"
PROMPT_LIMIT = 20_992
REQUIREMENTS = tuple(f"T{index:02d}" for index in range(1, 9))


def _catalog() -> dict[str, dict[str, Any]]:
    value = json.loads((TASK / "SOURCE_CATALOG.json").read_text(encoding="utf-8"))
    return {row["source_id"]: row for row in value["sources"]}


def _base_messages(world: KeystoneWorld) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": (TASK / "SYSTEM.md").read_text(encoding="utf-8")},
        {"role": "user", "content": (TASK / "TASK.md").read_text(encoding="utf-8")},
        {"role": "user", "content": (TASK / "ACTIONS.md").read_text(encoding="utf-8") + "\n\n# Exact source catalog\n" + world.source_catalog_for_actor()},
        {"role": "user", "content": "# Exact current candidate\n" + world.candidate_packet()},
    ]


def fixture_ledger() -> str:
    rows = ["# Trellis Evidence-to-Requirement Matrix", "", "| Requirement | Exact sources | Current work status |", "|---|---|---|"]
    groups = (
        ("T01", ("COUNCIL", "LINEAGE", "REVIEW")),
        ("T02", ("CLIMATE", "LINEAGE")),
        ("T03", ("GRID", "SUPPLY", "LINEAGE")),
        ("T04", ("WATER", "GRID", "SUPPLY")),
        ("T05", ("CLINIC", "SHELTER", "LABOR")),
        ("T06", ("TRANSIT", "COMMS", "SHELTER")),
        ("T07", ("SUPPLY", "LABOR", "GRID")),
        ("T08", ("LINEAGE", "REVIEW", "COUNCIL")),
    )
    for requirement, sources in groups:
        rows.append(f"| {requirement} | {' '.join(f'[{source}]' for source in sources)} | Evidence acquired; exact relationship remains subject to current candidate check. |")
    return "\n".join(rows) + "\n"


def fixture_decision(*, defective: bool) -> str:
    config = json.loads((TASK / "EVALUATOR.json").read_text(encoding="utf-8"))
    by_id = {spec.source_id: spec for spec in SPECS}
    groups = (
        ("COUNCIL", "LINEAGE", "REVIEW"),
        ("CLIMATE",),
        ("GRID", "WATER", "SUPPLY"),
        ("CLINIC", "SHELTER"),
        ("TRANSIT", "COMMS", "LABOR"),
        (),
    )
    control = (
        "The named owner records prerequisites, observations, candidate version, uncertainty, falsifier, pause condition, rollback action, and exact evidence required to retire each temporary control. "
        "Before advancing, the owner reconciles dependencies, obtains a current check, records residual risk, and seeks separately authorized acceptance. "
    )
    sections = []
    for heading, source_ids in zip(config["decision_headings"], groups):
        chunks = []
        for source_id in source_ids:
            spec = by_id[source_id]
            chunks.append(" ".join((*spec.findings, *spec.relationships, f"[{source_id}]")))
        sections.append(f"## {heading}\n\n" + " ".join(chunks) + " " + control)
    decision = config["decision_title"] + "\n\n" + "\n\n".join(sections) + "\n"
    if defective:
        decision = decision.replace("three consecutive fifteen-minute windows", "one fifteen-minute window", 1)
    return decision


def _execute(world: KeystoneWorld, ledger: ResultLedger, action: dict[str, Any], result_id: str, call: int):
    execution = world.execute(action, result_id=result_id, ledger=ledger)
    record = world.make_result_record(execution, result_id=result_id, acquired_call=call)
    ledger.add(record)
    return record


def _repair_action(world: KeystoneWorld, valid_decision: str) -> dict[str, Any]:
    current = (world.candidate_root / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md").read_text(encoding="utf-8")
    heading = "Power, water, and cooling continuity"
    old = next(row for row in section_spans(current) if row["heading"] == heading)
    new = next(row for row in section_spans(valid_decision) if row["heading"] == heading)
    return {
        "action": "replace_artifact_section",
        "candidate_sha256": world.candidate_sha256,
        "artifact_sha256": sha256_text(current),
        "section_heading": heading,
        "expected_section_sha256": old["sha256"],
        "replacement_section": new["text"],
    }


def _provider_free_lifecycle(root: Path, tokenizer: OfflineTokenizer) -> dict[str, Any]:
    world = KeystoneWorld(TASK, root / "lifecycle", count_text=tokenizer.count_text)
    ledger = ResultLedger()
    _execute(world, ledger, {"action": "replace_evidence_ledger", "content": fixture_ledger()}, "RESULT-001", 1)
    _execute(world, ledger, {"action": "replace_decision", "content": fixture_decision(defective=True)}, "RESULT-002", 2)
    milestone = world.construction_milestone()
    _execute(world, ledger, {"action": "begin_verification"}, "RESULT-003", 3)
    failed = _execute(world, ledger, {"action": "run_check"}, "RESULT-004", 4)
    failed_projection = failed.metadata["check_projection"]
    repair = _repair_action(world, fixture_decision(defective=False))
    effect = _execute(world, ledger, repair, "RESULT-005", 5)
    passed = _execute(world, ledger, {"action": "run_check"}, "RESULT-006", 6)
    passed_projection = passed.metadata["check_projection"]
    _execute(world, ledger, {"action": "submit"}, "RESULT-007", 7)
    return {
        "milestone_passed": milestone["passed"],
        "first_check_passed": failed_projection["passed"],
        "first_check_blockers": failed_projection["blocking_requirements"],
        "repair_changed_candidate": effect.metadata["before_sha256"] != effect.candidate_sha256_after,
        "recheck_passed": passed_projection["passed"],
        "submitted": world.submitted,
        "final_candidate_sha256": world.candidate_sha256,
    }


def _scaffold_qualification(root: Path, tokenizer: OfflineTokenizer) -> dict[str, Any]:
    world = KeystoneWorld(TASK, root / "scaffold", count_text=tokenizer.count_text)
    ledger = ResultLedger()
    source = _execute(
        world, ledger,
        {"action": "read_batch", "requests": [{"source_id": "COUNCIL", "start_line": 1, "end_line": 24}, {"source_id": "CLIMATE", "start_line": 1, "end_line": 24}]},
        "RESULT-001", 1,
    )
    ledger.mark_model_visible("RESULT-001", call_index=2, message_index=0)
    ledger.mark_external("RESULT-001")
    council = world.sources["COUNCIL"]
    climate = world.sources["CLIMATE"]
    council_anchor = council.lines[council.lines.index("## Governing relationships") + 2]
    climate_anchor = climate.lines[climate.lines.index("## Governing relationships") + 2]
    delta = DELTA_PREFIX + "\n" + "\n".join(
        (
            "\n".join((
                "## CLAIM COUNCIL_T01", "SLOT_SOURCE: COUNCIL", f"SOURCE_VERSION: {council.sha256}",
                "EVIDENCE_RESULT: RESULT-001", f"EVIDENCE_ANCHOR: {council_anchor}",
                "MODE: source_reported_relationship", "ATTRIBUTION: owner_source_reported",
                "REFERENTS: CLIMATE,GRID,WATER,REVIEW", "AUTHORITY: non_authoritative_derivative",
                f"STATEMENT: [REQUIREMENTS:T01,T08] COUNCIL reports: {council_anchor}",
            )),
            "\n".join((
                "## CLAIM CLIMATE_BAD", "SLOT_SOURCE: CLIMATE", f"SOURCE_VERSION: {climate.sha256}",
                "EVIDENCE_RESULT: RESULT-001", f"EVIDENCE_ANCHOR: {climate_anchor}",
                "MODE: source_reported_relationship", "ATTRIBUTION: owner_source_reported",
                "REFERENTS: SHELTER,TRANSIT,COMMS,COUNCIL", "AUTHORITY: non_authoritative_derivative",
                f"STATEMENT: [REQUIREMENTS:Z99] CLIMATE reports: {climate_anchor}",
            )),
        )
    )
    admission = admit_task_coupled_delta(
        delta,
        count_text=tokenizer.count_text,
        source_catalog=_catalog(),
        task_root=TASK,
        newly_externalized=(source,),
        current_source_versions=world.source_versions,
        requirement_ids=REQUIREMENTS,
    )
    transition = AnchoredProvenanceRegister().apply(admission, current_source_versions=world.source_versions, count_text=tokenizer.count_text)
    return {
        "disposition": admission.disposition,
        "admitted_claim_ids": [claim.claim_id for claim in admission.admitted_claims],
        "rejected_codes": {row.claim_id: row.code for row in admission.rejected_claims},
        "register_changed": transition.changed,
        "requirement_index": requirement_index(transition.register),
    }


def _pressure_geometry(root: Path, tokenizer: OfflineTokenizer) -> dict[str, Any]:
    world = KeystoneWorld(TASK, root / "pressure", count_text=tokenizer.count_text)
    ledger = ResultLedger()
    messages = _base_messages(world)
    pressure = None
    delivered_sources: set[str] = set()
    result_index = 1
    for call, index in enumerate(range(0, len(SOURCE_IDS), 2), 1):
        pair = SOURCE_IDS[index:index + 2]
        action = {"action": "read_batch", "requests": [{"source_id": source_id, "start_line": 1, "end_line": 78} for source_id in pair]}
        output = canonical_json_text(action)
        messages.append({"role": "assistant", "content": output})
        result_id = f"RESULT-{result_index:03d}"
        result_index += 1
        record = _execute(world, ledger, action, result_id, call)
        messages.append({"role": "user", "content": record.exact_content})
        ledger.mark_model_visible(result_id, call_index=call + 1, message_index=len(messages) - 1)
        delivered_sources.update(pair)
        prompt_tokens = tokenizer.count_messages(messages)
        if prompt_tokens > PROMPT_LIMIT:
            candidate_messages = [dict(message) for message in messages]
            candidate_ledger = ResultLedger.from_dict(ledger.as_dict(include_exact_content=True))
            relief = positive_savings_first_fit_step(
                messages=candidate_messages,
                ledger=candidate_ledger,
                prompt_limit=PROMPT_LIMIT,
                count_messages=tokenizer.count_messages,
                protected_result_ids=(result_id,),
            )
            pressure = {
                "actor_calls": call,
                "delivered_sources": sorted(delivered_sources),
                "ordinary_prompt_tokens": prompt_tokens,
                "overflow_tokens": prompt_tokens - PROMPT_LIMIT,
                "relief_result_ids": list(relief.selected_result_ids),
                "relief_prompt_tokens": relief.prompt_tokens,
                "relief_feasible": bool(relief.selected_result_ids) and relief.prompt_tokens <= PROMPT_LIMIT,
            }
            break
    return {"pressure": pressure, "complete_world_tokens": tokenizer.count_text("\n".join(path.read_text(encoding="utf-8") for path in sorted((TASK / "sources").glob("*.md"))))}


def main() -> int:
    tokenizer = OfflineTokenizer()
    with tempfile.TemporaryDirectory(prefix="trellis-stage0-") as temp:
        root = Path(temp)
        lifecycle = _provider_free_lifecycle(root, tokenizer)
        scaffold = _scaffold_qualification(root, tokenizer)
        geometry = _pressure_geometry(root, tokenizer)
    lock = json.loads((TASK / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    if lock.get("task_id") != TASK_ID or len(lock.get("source_custody", [])) != 12:
        failures.append("task_custody_invalid")
    if not lifecycle["milestone_passed"] or lifecycle["first_check_passed"] or not lifecycle["recheck_passed"] or not lifecycle["submitted"]:
        failures.append("provider_free_lifecycle_invalid")
    if scaffold["admitted_claim_ids"] != ["COUNCIL_T01"] or scaffold["rejected_codes"].get("CLIMATE_BAD") != "target_requirement_unknown":
        failures.append("partial_scaffold_admission_invalid")
    pressure = geometry["pressure"]
    if pressure is None or len(pressure["delivered_sources"]) < 8 or not pressure["relief_feasible"]:
        failures.append("pressure_geometry_not_diagnostic")
    result = {
        "schema": "trellis-artifact-centered-stage0-v0",
        "task_id": TASK_ID,
        "configurations": list(ARTIFACT_CENTERED_LIFECYCLE_CONFIGURATIONS),
        "task_source_lock_sha256": sha256_file(TASK / "TASK_SOURCE_LOCK.json"),
        "provider_model_calls": 0,
        "lifecycle": lifecycle,
        "scaffold": scaffold,
        "pressure_geometry": geometry,
        "passed": not failures,
        "failures": failures,
    }
    write_json(ROOT / "TRELLIS_STAGE0_RESULT.json", result)
    print(canonical_json_text(result))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
