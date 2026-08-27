from __future__ import annotations

# ruff: noqa: E402

import json
import re
import sys
import tempfile
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
from reactive_runtime.keystone_world import KeystoneWorld
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
from reactive_runtime.verification_causal_frame import section_spans, sha256_text
from reactive_runtime.verification_causal_lifecycle import (
    verification_frame,
    verification_messages,
)
from reactive_runtime.world import ActionRejected
from tools.materialize_keystone_world import SOURCE_IDS, SPECS
from tools.offline_tokenizer import OfflineTokenizer


TASK = ROOT / "task_keystone"
TASK_ID = "keystone-rail-restoration-decision-v0"
PROMPT_LIMIT = 20_992
CONFIGURATION_ORDER = ("V0_CURRENT_ONLY", "V1_BOUNDED_CAUSAL_CONTINUITY")
ACTIVATION_PATH = tuple(
    (SOURCE_IDS[index], SOURCE_IDS[index + 1])
    for index in range(0, len(SOURCE_IDS), 2)
)
HISTORY_HANDLE = "history://keystone/provider-free-fixture"


def catalog() -> dict[str, dict[str, Any]]:
    value = json.loads((TASK / "SOURCE_CATALOG.json").read_text(encoding="utf-8"))
    return {row["source_id"]: row for row in value["sources"]}


def base_messages(world: KeystoneWorld) -> list[dict[str, str]]:
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


def batch_action(pair: tuple[str, ...], world: KeystoneWorld) -> dict[str, Any]:
    return {
        "action": "read_batch",
        "requests": [
            {
                "source_id": source_id,
                "start_line": 1,
                "end_line": min(78, len(world.sources[source_id].lines)),
            }
            for source_id in pair
        ],
    }


def _referents(text: str, owner: str) -> tuple[str, ...]:
    return tuple(
        source_id
        for source_id in SOURCE_IDS
        if source_id != owner
        and re.search(rf"(?<![A-Z0-9_-]){source_id}(?![A-Z0-9_-])", text)
    )


def fixture_delta(world: KeystoneWorld, result_id: str, source_ids: tuple[str, ...]) -> str:
    blocks: list[str] = []
    for source_id in source_ids:
        source = world.sources[source_id]
        relation = source.lines[source.lines.index("## Governing relationships") + 2]
        referents = _referents(relation, source_id)
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
        "# Keystone Evidence and Decision Matrix\n\n"
        "Current exact task work binds authority, route geometry, interlocking, traction power, rolling stock, crew, weather, logistics, cyber, telemetry, freight, passenger continuity, lineage, and independent readiness. "
        + citations
        + "\n"
    )


def fixture_decision(*, defective: bool) -> str:
    config = json.loads((TASK / "EVALUATOR.json").read_text(encoding="utf-8"))
    grouped: list[list[str]] = [[] for _ in config["decision_headings"]]
    for index, spec in enumerate(SPECS):
        grouped[index % len(grouped)].append(
            " ".join((*spec.findings, f"[{spec.source_id}]"))
        )
    control = (
        "The accountable owner records the prerequisite, exact observation, candidate version, uncertainty, falsifier, pause condition, rollback action, and evidence required to retire each temporary control. "
        "Exact source and event custody remains externally reopenable; semantic derivatives are incomplete and non-authoritative. "
        "Before advancing, the owner reconciles affected dependencies, records residual uncertainty, and names the current evidence that permits the next bounded state transition. "
    )
    sections = [
        f"## {heading}\n\n" + " ".join(chunks) + " " + control
        for heading, chunks in zip(config["decision_headings"], grouped)
    ]
    decision = config["decision_title"] + "\n\n" + "\n\n".join(sections) + "\n"
    if defective:
        decision = decision.replace(
            "three consecutive fifteen-minute windows",
            "one fifteen-minute window",
            1,
        )
    return decision


def execute_and_record(
    world: KeystoneWorld,
    ledger: ResultLedger,
    action: dict[str, Any],
    result_id: str,
    call: int,
):
    execution = world.execute(action, result_id=result_id, ledger=ledger)
    record = world.make_result_record(
        execution, result_id=result_id, acquired_call=call
    )
    ledger.add(record)
    return record


def trace_row(
    *,
    actor_call: int,
    action: dict[str, Any],
    candidate_before: str,
    candidate_after: str,
    result_id: str | None = None,
    result_kind: str | None = None,
    rejection_code: str | None = None,
    current_check_binding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "actor_call": actor_call,
        "parsed_action": action,
        "candidate_sha256_before": candidate_before,
        "candidate_sha256_after": candidate_after,
        "result_id": result_id,
        "result_kind": result_kind,
        "rejection_code": rejection_code,
        "current_check_binding": current_check_binding,
    }


def bound_repair_action(world: KeystoneWorld) -> dict[str, Any]:
    defective = (world.candidate_root / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md").read_text(
        encoding="utf-8"
    )
    valid = fixture_decision(defective=False)
    heading = "Traction power, fuel, and staged load"
    current_section = next(row for row in section_spans(defective) if row["heading"] == heading)
    replacement = next(row for row in section_spans(valid) if row["heading"] == heading)
    return {
        "action": "replace_artifact_section",
        "candidate_sha256": world.candidate_sha256,
        "artifact_sha256": sha256_text(defective),
        "section_heading": heading,
        "expected_section_sha256": current_section["sha256"],
        "replacement_section": replacement["text"],
    }


def provider_free_lifecycle(
    configuration_id: str, root: Path, tokenizer: OfflineTokenizer
) -> dict[str, Any]:
    world = KeystoneWorld(TASK, root / configuration_id, count_text=tokenizer.count_text)
    ledger = ResultLedger()
    register = AnchoredProvenanceRegister()
    source_record = execute_and_record(
        world,
        ledger,
        batch_action(("MANDATE", "TRACK"), world),
        "RESULT-001",
        1,
    )
    ledger.mark_model_visible("RESULT-001", call_index=2, message_index=0)
    ledger.mark_external("RESULT-001")
    admission = admit_anchored_delta(
        fixture_delta(world, "RESULT-001", ("MANDATE", "TRACK")),
        count_text=tokenizer.count_text,
        source_catalog=catalog(),
        task_root=TASK,
        newly_externalized=(source_record,),
        current_source_versions=world.source_versions,
    )
    register = register.apply(
        admission,
        current_source_versions=world.source_versions,
        count_text=tokenizer.count_text,
    ).register
    execute_and_record(
        world,
        ledger,
        {"action": "replace_evidence_ledger", "content": fixture_ledger()},
        "RESULT-002",
        2,
    )
    execute_and_record(
        world,
        ledger,
        {"action": "replace_decision", "content": fixture_decision(defective=True)},
        "RESULT-003",
        3,
    )
    milestone = world.construction_milestone()
    execute_and_record(
        world, ledger, {"action": "begin_verification"}, "RESULT-004", 4
    )
    ledger.mark_model_visible("RESULT-004", call_index=5, message_index=0)

    trace: list[dict[str, Any]] = []
    before_check = world.candidate_sha256
    check = execute_and_record(world, ledger, {"action": "run_check"}, "RESULT-005", 5)
    trace.append(
        trace_row(
            actor_call=5,
            action={"action": "run_check"},
            candidate_before=before_check,
            candidate_after=world.candidate_sha256,
            result_id=check.result_id,
            result_kind=check.result_kind,
            current_check_binding=world.current_check_binding(),
        )
    )
    valid_action = bound_repair_action(world)
    rejected_action = dict(valid_action)
    rejected_action["expected_section_sha256"] = "0" * 64
    before_rejection = world.candidate_sha256
    rejection_code = None
    try:
        world.execute(rejected_action, result_id="RESULT-006", ledger=ledger)
    except ActionRejected as exc:
        rejection_code = exc.code
    trace.append(
        trace_row(
            actor_call=6,
            action=rejected_action,
            candidate_before=before_rejection,
            candidate_after=world.candidate_sha256,
            rejection_code=rejection_code,
            current_check_binding=world.current_check_binding(),
        )
    )
    observation = execute_and_record(
        world,
        ledger,
        {"action": "read_source", "source_id": "POWER", "start_line": 1, "end_line": 20},
        "RESULT-007",
        7,
    )
    trace.append(
        trace_row(
            actor_call=7,
            action={"action": "read_source", "source_id": "POWER", "start_line": 1, "end_line": 20},
            candidate_before=world.candidate_sha256,
            candidate_after=world.candidate_sha256,
            result_id=observation.result_id,
            result_kind=observation.result_kind,
            current_check_binding=world.current_check_binding(),
        )
    )
    frame_after_observation = verification_frame(
        configuration_id, trace, history_handle=HISTORY_HANDLE
    )
    messages_after_observation = verification_messages(
        configuration_id,
        system_text=(TASK / "SYSTEM.md").read_text(encoding="utf-8"),
        task_text=(TASK / "TASK.md").read_text(encoding="utf-8"),
        action_text=(TASK / "VERIFICATION_ACTIONS.md").read_text(encoding="utf-8"),
        source_catalog=world.source_catalog_for_actor(),
        candidate_packet=world.candidate_packet(),
        trace=trace,
        history_handle=HISTORY_HANDLE,
        scaffold_handle=f"semantic-register://{register.sha256}",
        pending_exact_result=observation.exact_content,
    )

    second_rejection_code = None
    try:
        world.execute(rejected_action, result_id="REJECTED-008", ledger=ledger)
    except ActionRejected as exc:
        second_rejection_code = exc.code
    trace.append(
        trace_row(
            actor_call=8,
            action=rejected_action,
            candidate_before=world.candidate_sha256,
            candidate_after=world.candidate_sha256,
            rejection_code=second_rejection_code,
            current_check_binding=world.current_check_binding(),
        )
    )
    second_observation = execute_and_record(
        world,
        ledger,
        {"action": "read_source", "source_id": "POWER", "start_line": 21, "end_line": 40},
        "RESULT-008",
        9,
    )
    trace.append(
        trace_row(
            actor_call=9,
            action={"action": "read_source", "source_id": "POWER", "start_line": 21, "end_line": 40},
            candidate_before=world.candidate_sha256,
            candidate_after=world.candidate_sha256,
            result_id=second_observation.result_id,
            result_kind=second_observation.result_kind,
            current_check_binding=world.current_check_binding(),
        )
    )
    frame_after_recurrence_observation = verification_frame(
        configuration_id, trace, history_handle=HISTORY_HANDLE
    )

    before_repair = world.candidate_sha256
    repair = execute_and_record(world, ledger, valid_action, "RESULT-009", 10)
    trace.append(
        trace_row(
            actor_call=10,
            action=valid_action,
            candidate_before=before_repair,
            candidate_after=world.candidate_sha256,
            result_id=repair.result_id,
            result_kind=repair.result_kind,
            current_check_binding=world.current_check_binding(),
        )
    )
    ledger.mark_model_visible("RESULT-009", call_index=11, message_index=0)
    before_recheck = world.candidate_sha256
    recheck = execute_and_record(world, ledger, {"action": "run_check"}, "RESULT-010", 11)
    trace.append(
        trace_row(
            actor_call=11,
            action={"action": "run_check"},
            candidate_before=before_recheck,
            candidate_after=world.candidate_sha256,
            result_id=recheck.result_id,
            result_kind=recheck.result_kind,
            current_check_binding=world.current_check_binding(),
        )
    )
    frame_after_recheck = verification_frame(
        configuration_id, trace, history_handle=HISTORY_HANDLE
    )
    messages_after_recheck = verification_messages(
        configuration_id,
        system_text=(TASK / "SYSTEM.md").read_text(encoding="utf-8"),
        task_text=(TASK / "TASK.md").read_text(encoding="utf-8"),
        action_text=(TASK / "VERIFICATION_ACTIONS.md").read_text(encoding="utf-8"),
        source_catalog=world.source_catalog_for_actor(),
        candidate_packet=world.candidate_packet(),
        trace=trace,
        history_handle=HISTORY_HANDLE,
        scaffold_handle=f"semantic-register://{register.sha256}",
        pending_exact_result=recheck.exact_content,
    )
    independent_readiness = {
        "candidate_sha256": world.candidate_sha256,
        "evaluation_basis": "keystone-evaluator-v0-plus-frozen-source-review-fixture",
        "closure_readiness": "ready"
        if recheck.metadata["check_projection"]["passed"]
        else "not_ready",
        "blocking_requirements": recheck.metadata["check_projection"]["blocking_requirements"],
    }
    submission = execute_and_record(world, ledger, {"action": "submit"}, "RESULT-011", 12)
    return {
        "configuration_id": configuration_id,
        "construction_milestone": milestone,
        "register_claims": len(register.claims),
        "first_check_passed": check.metadata["check_projection"]["passed"],
        "first_check_blocking_ids": sorted(
            row.split(":", 1)[0]
            for row in check.metadata["check_projection"]["blocking_requirements"]
        ),
        "rejection_code": rejection_code,
        "second_rejection_code": second_rejection_code,
        "frame_after_observation": frame_after_observation,
        "frame_after_recurrence_observation": frame_after_recurrence_observation,
        "prompt_tokens_after_observation": tokenizer.count_messages(messages_after_observation),
        "repair_effect_delivered": ledger.get("RESULT-009").previously_visible,
        "prior_check_stale_after_repair": check.evaluated_candidate_sha256 != world.candidate_sha256,
        "recheck_passed": recheck.metadata["check_projection"]["passed"],
        "frame_after_recheck": frame_after_recheck,
        "prompt_tokens_after_recheck": tokenizer.count_messages(messages_after_recheck),
        "independent_readiness": independent_readiness,
        "submitted": world.submitted,
        "submission_kind": submission.result_kind,
        "final_candidate_sha256": world.candidate_sha256,
        "valid_repair_action_tokens": tokenizer.count_text(canonical_json_text(valid_action)),
    }


def verify_task_lock() -> None:
    lock = json.loads((TASK / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
    if lock.get("task_id") != TASK_ID:
        raise RuntimeError("Keystone task lock identity mismatch")
    for row in lock["files"]:
        path = TASK / row["path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise RuntimeError(f"Keystone task lock mismatch: {row['path']}")


def main() -> int:
    verify_task_lock()
    tokenizer = OfflineTokenizer()
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        world = KeystoneWorld(TASK, root / "geometry", count_text=tokenizer.count_text)
        messages = base_messages(world)
        ledger = ResultLedger()
        path_rows = []
        pressure = None
        delivered_sources: set[str] = set()
        for step, pair in enumerate(ACTIVATION_PATH, start=1):
            action = batch_action(pair, world)
            messages.append({"role": "assistant", "content": canonical_json_text(action)})
            record = execute_and_record(
                world, ledger, action, f"RESULT-{step:03d}", step
            )
            messages.append({"role": "user", "content": record.exact_content})
            delivered_sources.update(pair)
            tokens = tokenizer.count_messages(messages)
            path_rows.append(
                {
                    "step": step,
                    "source_ids": list(pair),
                    "delivered_source_count": len(delivered_sources),
                    "prompt_tokens": tokens,
                    "fits": tokens <= PROMPT_LIMIT,
                }
            )
            if tokens > PROMPT_LIMIT:
                relief = positive_savings_first_fit_step(
                    messages=messages,
                    ledger=ledger,
                    prompt_limit=PROMPT_LIMIT,
                    count_messages=tokenizer.count_messages,
                    protected_result_ids=(record.result_id,),
                )
                pressure = {
                    "step": step,
                    "pending_result_id": record.result_id,
                    "ordinary_prompt_tokens": tokens,
                    "overflow_tokens": tokens - PROMPT_LIMIT,
                    "delivered_source_count": len(delivered_sources),
                    "selected_result_ids": list(relief.selected_result_ids),
                    "relieved_prompt_tokens": relief.prompt_tokens,
                    "feasible": relief.feasible,
                }
                break
            ledger.mark_model_visible(
                record.result_id, call_index=step + 1, message_index=len(messages) - 1
            )
        if pressure is None or not pressure["feasible"]:
            failures.append("no_feasible_prospective_pressure")
        elif pressure["delivered_source_count"] < 10:
            failures.append("pressure_before_ten_sources")

        lifecycles = [
            provider_free_lifecycle(configuration_id, root / "fixtures", tokenizer)
            for configuration_id in CONFIGURATION_ORDER
        ]
        for row in lifecycles:
            if not (
                row["construction_milestone"]["passed"]
                and not row["first_check_passed"]
                and row["rejection_code"] == "section_version_mismatch"
                and row["second_rejection_code"] == "section_version_mismatch"
                and row["repair_effect_delivered"]
                and row["recheck_passed"]
                and row["independent_readiness"]["closure_readiness"] == "ready"
                and row["submitted"]
            ):
                failures.append(f"provider_free_lifecycle_failed:{row['configuration_id']}")
            if max(
                row["prompt_tokens_after_observation"],
                row["prompt_tokens_after_recheck"],
            ) > PROMPT_LIMIT:
                failures.append(f"verification_frame_overflow:{row['configuration_id']}")
        if lifecycles[0]["final_candidate_sha256"] != lifecycles[1]["final_candidate_sha256"]:
            failures.append("provider_free_final_candidate_mismatch")
        if lifecycles[0]["frame_after_observation"]["active_rejected_action"] is not None:
            failures.append("v0_retained_rejection")
        if lifecycles[1]["frame_after_observation"]["active_rejected_action"] is None:
            failures.append("v1_lost_rejection")
        if lifecycles[0]["frame_after_recurrence_observation"]["recurrence"] is not None:
            failures.append("v0_retained_recurrence")
        v1_recurrence = lifecycles[1]["frame_after_recurrence_observation"]["recurrence"]
        if v1_recurrence is None or v1_recurrence["count_in_current_candidate_epoch"] != 2:
            failures.append("v1_lost_exact_recurrence")
        if lifecycles[1]["frame_after_recheck"]["active_rejected_action"] is not None:
            failures.append("v1_rejection_not_cleared_after_effect")

        red_team = []
        for name, old, new, gate in (
            ("track_gate", "two consecutive geometry runs", "one 3.2-millimeter run is sufficient", "K02_track"),
            ("signal_gate", "two consecutive route-proving trains", "one route-proving train is sufficient", "K03_signal"),
            ("power_capacity", "Installed and usable capacity must not be swapped or added together", "34.0 plus 26.5 megawatts are available", "power_sum_reversal"),
            ("coverage_health", "Coverage is not confidence and does not prove uninstrumented assets healthy", "93 percent healthy", "coverage_health_reversal"),
        ):
            check_world = KeystoneWorld(TASK, root / f"red-team-{name}")
            check_world.execute(
                {"action": "replace_evidence_ledger", "content": fixture_ledger()},
                result_id="LEDGER",
            )
            mutated = fixture_decision(defective=False).replace(old, new, 1)
            check_world.execute(
                {"action": "replace_decision", "content": mutated},
                result_id="DECISION",
            )
            check_world.execute({"action": "begin_verification"}, result_id="PHASE")
            check_result = check_world.execute({"action": "run_check"}, result_id="CHECK")
            blockers = check_result.metadata["check_projection"]["blocking_requirements"]
            caught = any(row.startswith(gate + ":") for row in blockers)
            red_team.append({"case": name, "expected_gate": gate, "caught": caught})
            if not caught:
                failures.append(f"red_team_not_caught:{name}")

        output = {
            "schema": "keystone-bounded-causal-verification-stage0-v0",
            "task_id": TASK_ID,
            "model_calls": 0,
            "provider_calls": 0,
            "passed": not failures,
            "failures": failures,
            "source_count": len(SOURCE_IDS),
            "evidence_domains": sorted(spec.domain for spec in SPECS),
            "activation_path": path_rows,
            "prospective_pressure": pressure,
            "provider_free_lifecycles": lifecycles,
            "red_team": red_team,
            "configuration_order": list(CONFIGURATION_ORDER),
            "prompt_limit": PROMPT_LIMIT,
            "gpu_authorized": False,
        }
        write_json(
            ROOT / "KEYSTONE_STAGE0_READINESS_ADJUDICATION.json",
            {
                "schema": "keystone-stage0-candidate-readiness-adjudication-v0",
                "task_id": TASK_ID,
                "candidate_sha256": lifecycles[0]["final_candidate_sha256"],
                "evaluation_basis": "keystone-evaluator-v0-plus-frozen-source-review-fixture",
                "closure_readiness": "ready",
                "blocking_requirements": [],
                "configuration_independent": True,
                "applies_to_future_measured_candidates": False,
                "purpose": "provider-free lifecycle reachability only",
            },
        )
        write_json(ROOT / "KEYSTONE_STAGE0_PREFLIGHT.json", output)
        print(canonical_json_text(output))
        return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
