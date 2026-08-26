from __future__ import annotations

# ruff: noqa: E402

import argparse
import json
import sys
import time
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.actions import (
    MAX_SOURCE_RESULT_TOKENS,
    action_json_schema,
    parse_action,
    render_action_rejection,
)
from reactive_runtime.anchored_provenance import (
    DELTA_TOKEN_BUDGET,
    REGISTER_PREFIX,
    AnchoredProvenanceRegister,
    admit_anchored_delta,
    anchored_delta_messages,
)
from reactive_runtime.canonical import sha256_bytes, sha256_file, write_json
from reactive_runtime.configuration import (
    ANCHORED_RELATIONAL_CONFIGURATIONS,
    anchored_relational_actor_actions,
)
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger, ResultRecord
from reactive_runtime.seal import seal_tree
from reactive_runtime.solace_boundary import verify_solace_pressure_handoff
from reactive_runtime.solace_world import SolaceWorld
from reactive_runtime.trajectory_budget import ConstructionBudget
from reactive_runtime.world import ActionRejected
from tools.live_common import (
    LiveTokenizer,
    complete_custodied,
    git_commit,
    provider_payload,
    require_clean_tree,
    start_server,
    stop_server,
)
from tools.verify_runtime_assets import verify as verify_runtime_assets


RUN_ID = "2026-08-26-solace-anchored-provenance-interaction-measured-v0"
SCOPE = "solace_anchored_provenance_interaction_measured_v0"
CONFIGURATION_ORDER = ANCHORED_RELATIONAL_CONFIGURATIONS
ACTOR_SEED = 531_701
MAINTENANCE_SEED = 531_702
CONTEXT_TOKENS = 25_088
PROMPT_LIMIT = 20_992
ACTOR_MAX_TOKENS = 4_096
MAX_PRECONSTRUCTION_CALLS_PER_CELL = 26
POSTCONSTRUCTION_CALLS_PER_CELL = 8
MAX_ACTOR_CALLS_PER_CELL = 34
MAX_MAINTENANCE_CALLS_L1 = 18
MAX_PROVIDER_CALLS = 86
MAX_SERIALIZED_TOKENS_PER_CELL = 1_600_000
MAX_WALL_SECONDS_PER_CELL = 10_800
TASK = ROOT / "task_solace"
CONTRACT = ROOT / "SOLACE_ANCHORED_INTERACTION_CONTRACT.json"
REQUEST = ROOT / "SOLACE_ANCHORED_INTERACTION_AUTHORIZATION_REQUEST.json"
PREFLIGHT = ROOT / "SOLACE_ANCHORED_INTERACTION_PREFLIGHT.json"
MODEL_LOCK = ROOT / "SOLACE_MODEL_PROFILE_LOCK.json"
PRESSURE_RUN = ROOT / "runs" / "2026-08-26-solace-anchored-provenance-pressure-screen-v0"


class BudgetStop(RuntimeError):
    pass


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def validate_authorization(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if resolved.is_relative_to(ROOT.resolve()):
        raise RuntimeError("authorization receipt must remain outside repository")
    receipt = load(resolved)
    request = load(REQUEST)
    commit = git_commit()
    expected = {
        "authorized": True,
        "authorized_freeze_commit": commit,
        "authorized_scope": SCOPE,
        "authorized_run_id": RUN_ID,
        "configuration_order": list(CONFIGURATION_ORDER),
        "maximum_actor_calls": 68,
        "maximum_maintenance_calls": MAX_MAINTENANCE_CALLS_L1,
        "maximum_provider_calls": MAX_PROVIDER_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
        "authorization_text": request["expected_user_quote_template"].replace(
            "{commit}", commit
        ),
    }
    failures = [key for key, value in expected.items() if receipt.get(key) != value]
    if failures:
        raise RuntimeError(f"authorization receipt mismatch: {failures}")
    return receipt


def verify_task_lock() -> None:
    lock = load(TASK / "TASK_SOURCE_LOCK.json")
    if lock.get("task_id") != "solace-water-recovery-decision-v0":
        raise RuntimeError("Solace task lock identity mismatch")
    for row in lock.get("files", []):
        path = TASK / str(row.get("path"))
        if not path.is_file() or sha256_file(path) != row.get("sha256"):
            raise RuntimeError(f"Solace task lock mismatch: {row.get('path')}")


def checked_usage(
    provider: dict[str, Any], expected_prompt: int, maximum_completion: int
) -> dict[str, Any]:
    usage = provider.get("usage")
    if not isinstance(usage, dict):
        raise RuntimeError("provider usage missing")
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    total = usage.get("total_tokens")
    if prompt != expected_prompt:
        raise RuntimeError(f"provider prompt mismatch: {prompt} != {expected_prompt}")
    if type(completion) is not int or not 0 <= completion <= maximum_completion:
        raise RuntimeError("provider completion count invalid")
    if total != prompt + completion:
        raise RuntimeError("provider usage arithmetic mismatch")
    details = usage.get("prompt_tokens_details") or {}
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "cached_tokens": details.get("cached_tokens"),
    }


def source_catalog() -> dict[str, dict[str, object]]:
    value = load(TASK / "SOURCE_CATALOG.json")
    return {str(row["source_id"]): row for row in value.get("sources", [])}


def register_message_index(messages: Sequence[dict[str, str]]) -> int | None:
    for index, message in enumerate(messages):
        if message.get("role") == "user" and message.get("content", "").startswith(
            REGISTER_PREFIX
        ):
            return index
    return None


def expose_register(
    messages: list[dict[str, str]], register: AnchoredProvenanceRegister
) -> None:
    index = register_message_index(messages)
    if not register.claims:
        return
    message = {"role": "user", "content": register.render()}
    if index is None:
        messages.append(message)
    else:
        messages[index] = message


def result_message_index(messages: Sequence[dict[str, str]], record: ResultRecord) -> int:
    matches = [
        index
        for index, message in enumerate(messages)
        if message == {"role": "user", "content": record.exact_content}
    ]
    if len(matches) != 1:
        raise RuntimeError(f"result message binding is not unique: {record.result_id}")
    return matches[0]


def external_evaluation(world: SolaceWorld, cell_root: Path) -> dict[str, Any]:
    execution = world._run_check("EXTERNAL-FINAL-EVALUATION")
    projection = execution.metadata.get("check_projection")
    value = {
        "schema": "solace-external-evaluation-v0",
        "actor_visible": False,
        "candidate_sha256": world.candidate_sha256,
        "evaluated_candidate_sha256": execution.evaluated_candidate_sha256,
        "projection": projection,
        "exact_projection_body": execution.body,
    }
    write_json(cell_root / "evaluation" / "MECHANICAL_FINAL_EVALUATION.json", value)
    if not isinstance(projection, dict) or projection.get("protocol_error_class") is not None:
        raise RuntimeError("external evaluator protocol failure")
    return value


def run_cell(configuration_id: str, run_root: Path) -> dict[str, Any]:
    if configuration_id not in CONFIGURATION_ORDER:
        raise ValueError(configuration_id)
    treatment = configuration_id == "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE"
    cell_root = run_root / "cells" / configuration_id
    cell_root.mkdir(parents=True, exist_ok=False)
    process = stdout = stderr = None
    release: dict[str, Any] | None = None
    failure: dict[str, Any] | None = None
    started = time.monotonic()
    actor_trace: list[dict[str, Any]] = []
    maintenance_trace: list[dict[str, Any]] = []
    relief_trace: list[dict[str, Any]] = []
    lifecycle: list[dict[str, Any]] = []
    serialized = 0
    terminal = "uninitialized"
    world: SolaceWorld | None = None
    final_evaluation: dict[str, Any] | None = None
    register = AnchoredProvenanceRegister()
    try:
        assets = verify_runtime_assets()
        write_json(cell_root / "RUNTIME_ASSET_VERIFICATION.json", assets)
        if assets.get("passed") is not True:
            raise RuntimeError(f"runtime assets failed: {assets.get('failures')}")
        process, stdout, stderr, _ = start_server(cell_root / "model")
        tokenizer = LiveTokenizer()
        boundary = load(PRESSURE_RUN / "PRESSURE_BOUNDARY.json")
        messages = [dict(row) for row in boundary["messages"]]
        ledger = ResultLedger.from_dict(boundary["result_ledger"])
        pending_result_id: str | None = str(boundary["pending_result_id"])
        world = SolaceWorld(TASK, cell_root / "trajectory")
        if world.candidate_sha256 != boundary["candidate_sha256"]:
            raise RuntimeError("common fork candidate mismatch")
        next_result = 7
        budget = ConstructionBudget(
            maximum_preconstruction_calls=MAX_PRECONSTRUCTION_CALLS_PER_CELL,
            postconstruction_calls=POSTCONSTRUCTION_CALLS_PER_CELL,
        )
        catalog = source_catalog()

        def elapsed() -> float:
            return time.monotonic() - started

        def admit_cost(prompt_tokens: int, maximum: int) -> None:
            if elapsed() >= MAX_WALL_SECONDS_PER_CELL:
                raise BudgetStop("wall_clock_budget_exhausted")
            if serialized + prompt_tokens + maximum > MAX_SERIALIZED_TOKENS_PER_CELL:
                raise BudgetStop("serialized_token_budget_exhausted")

        def run_maintenance(records: Sequence[ResultRecord], trigger: str) -> None:
            nonlocal register, serialized
            if not records or not treatment:
                return
            if len(maintenance_trace) >= MAX_MAINTENANCE_CALLS_L1:
                raise BudgetStop("maintenance_call_budget_exhausted")
            ordinal = len(maintenance_trace) + 1
            call_root = cell_root / "maintenance" / f"call-{ordinal:03d}"
            maintenance_messages = anchored_delta_messages(
                task_text=(TASK / "TASK.md").read_text(encoding="utf-8"),
                register=register,
                newly_externalized=records,
                source_versions=world.source_versions,
            )
            prompt_tokens, rendered = tokenizer.count_messages(maintenance_messages)
            if prompt_tokens + DELTA_TOKEN_BUDGET > CONTEXT_TOKENS:
                raise BudgetStop("maintenance_prompt_infeasible")
            admit_cost(prompt_tokens, DELTA_TOKEN_BUDGET)
            write_json(call_root / "messages.json", maintenance_messages)
            (call_root / "rendered_prompt.txt").parent.mkdir(parents=True, exist_ok=True)
            (call_root / "rendered_prompt.txt").write_text(
                rendered, encoding="utf-8", newline=""
            )
            provider = complete_custodied(
                provider_payload(
                    maintenance_messages,
                    MAINTENANCE_SEED,
                    {"type": "text"},
                    max_tokens=DELTA_TOKEN_BUDGET,
                ),
                call_root / "provider_attempt",
                timeout=max(1, min(900, int(MAX_WALL_SECONDS_PER_CELL - elapsed()))),
            )
            usage = checked_usage(provider, prompt_tokens, DELTA_TOKEN_BUDGET)
            serialized += int(usage["total_tokens"])
            output = str(provider["content"])
            (call_root / "assistant_content.txt").write_text(
                output, encoding="utf-8", newline=""
            )
            admission = admit_anchored_delta(
                output,
                count_text=lambda text: len(tokenizer.tokenize(text)),
                source_catalog=catalog,
                task_root=TASK,
                newly_externalized=records,
                current_source_versions=world.source_versions,
            )
            transition = register.apply(
                admission,
                current_source_versions=world.source_versions,
                count_text=lambda text: len(tokenizer.tokenize(text)),
            )
            register = transition.register
            expose_register(messages, register)
            row = {
                "maintenance_call": ordinal,
                "trigger": trigger,
                "input_result_ids": [record.result_id for record in records],
                "input_source_ids": sorted(
                    {
                        str(source_id)
                        for record in records
                        for source_id in record.metadata.get("source_ids", [])
                    }
                ),
                "prompt_tokens": prompt_tokens,
                "finish_reason": provider.get("finish_reason"),
                "usage": usage,
                "output_sha256": sha256_bytes(output.encode("utf-8")),
                "admission": asdict(admission),
                "transition": asdict(transition),
                "register_sha256": register.sha256,
                "register_claims": len(register.claims),
            }
            maintenance_trace.append(row)
            lifecycle.append({"event": "semantic_maintenance", **row})
            write_json(call_root / "RESULT.json", row)
            write_json(cell_root / "CURRENT_REGISTER.json", {
                "sha256": register.sha256,
                "claims": [asdict(claim) for claim in register.claims],
                "rendered": register.render(),
            })

        def restore_feasibility(trigger: str) -> None:
            while True:
                before = tokenizer.count_messages(messages)[0]
                if before <= PROMPT_LIMIT:
                    return
                protected = () if pending_result_id is None else (pending_result_id,)
                step = positive_savings_first_fit_step(
                    messages=messages,
                    ledger=ledger,
                    prompt_limit=PROMPT_LIMIT,
                    count_messages=lambda value: tokenizer.count_messages(value)[0],
                    protected_result_ids=protected,
                )
                row = {
                    "relief_event": len(relief_trace) + 1,
                    "trigger": trigger,
                    "before_tokens": before,
                    "after_tokens": step.prompt_tokens,
                    "selected_result_ids": list(step.selected_result_ids),
                    "feasible": step.feasible,
                    "audits": [asdict(value) for value in step.audits],
                }
                relief_trace.append(row)
                lifecycle.append({"event": "first_fit_relief", **row})
                if not step.selected_result_ids:
                    raise BudgetStop("context_pressure_without_feasible_relief")
                externalized = [ledger.get(result_id) for result_id in step.selected_result_ids]
                source_records = [
                    record
                    for record in externalized
                    if record.result_kind == "source_observation"
                ]
                run_maintenance(source_records, "positive_savings_externalization")

        # The common exact fork is already over limit. Both cells apply the same
        # first-fit transition; only L1 performs the charged semantic operation.
        restore_feasibility("common_pressure_fork")
        initial = {
            "schema": "solace-cell-initial-state-v0",
            "configuration_id": configuration_id,
            "common_actor_calls": boundary["actor_calls_completed"],
            "pending_result_id": pending_result_id,
            "candidate_sha256": world.candidate_sha256,
            "messages": messages,
            "result_ledger": ledger.as_dict(include_exact_content=True),
            "register_sha256": register.sha256,
            "register_claims": len(register.claims),
        }
        write_json(cell_root / "INITIAL_STATE.json", initial)

        while budget.can_call():
            restore_feasibility("ordinary_actor_prompt")
            actor_call = budget.actor_calls + 1
            global_call = int(boundary["actor_calls_completed"]) + actor_call
            if pending_result_id is not None:
                pending = ledger.get(pending_result_id)
                ledger.mark_model_visible(
                    pending_result_id,
                    call_index=global_call,
                    message_index=result_message_index(messages, pending),
                )
                lifecycle.append(
                    {
                        "event": "result_delivery",
                        "actor_call": actor_call,
                        "result_id": pending_result_id,
                    }
                )
                pending_result_id = None
            prompt_tokens, rendered = tokenizer.count_messages(messages)
            admit_cost(prompt_tokens, ACTOR_MAX_TOKENS)
            call_root = cell_root / "actor" / f"call-{actor_call:03d}"
            write_json(call_root / "messages.json", messages)
            (call_root / "rendered_prompt.txt").parent.mkdir(parents=True, exist_ok=True)
            (call_root / "rendered_prompt.txt").write_text(
                rendered, encoding="utf-8", newline=""
            )
            external = tuple(
                record.result_id
                for record in ledger.records()
                if record.previously_visible and not record.resident
            )
            schema = action_json_schema(
                anchored_relational_actor_actions(configuration_id),
                source_ids=world.sources,
                reopen_result_ids=external,
                decision_headings=world.decision_headings,
                schema_name=f"solace_{configuration_id.casefold()}_actor_action_v0",
            )
            provider = complete_custodied(
                provider_payload(messages, ACTOR_SEED, schema, max_tokens=ACTOR_MAX_TOKENS),
                call_root / "provider_attempt",
                timeout=max(1, min(900, int(MAX_WALL_SECONDS_PER_CELL - elapsed()))),
            )
            usage = checked_usage(provider, prompt_tokens, ACTOR_MAX_TOKENS)
            serialized += int(usage["total_tokens"])
            output = str(provider["content"])
            (call_root / "assistant_content.txt").write_text(
                output, encoding="utf-8", newline=""
            )
            messages.append({"role": "assistant", "content": output})
            before = world.candidate_sha256
            parsed: dict[str, Any] | None = None
            result_record: ResultRecord | None = None
            rejection: str | None = None
            try:
                parsed = parse_action(
                    output,
                    anchored_relational_actor_actions(configuration_id),
                    decision_headings=world.decision_headings,
                )
                result_id = f"RESULT-{next_result:03d}"
                next_result += 1
                execution = world.execute(parsed, result_id=result_id, ledger=ledger)
                result_record = world.make_result_record(
                    execution, result_id=result_id, acquired_call=global_call
                )
                if (
                    result_record.result_kind == "source_observation"
                    and len(tokenizer.tokenize(result_record.exact_content))
                    > MAX_SOURCE_RESULT_TOKENS
                ):
                    rejection = "source_result_too_large"
                    pending_text = render_action_rejection(
                        call_index=global_call,
                        code=rejection,
                        message="exact source result exceeded the frozen cap and remains audit-only",
                        candidate_sha256=world.candidate_sha256,
                    )
                    result_record = None
                else:
                    ledger.add(result_record)
                    pending_text = result_record.exact_content
            except json.JSONDecodeError as exc:
                rejection = "invalid_json"
                pending_text = render_action_rejection(
                    call_index=global_call,
                    code=rejection,
                    message=str(exc),
                    candidate_sha256=world.candidate_sha256,
                )
            except ActionRejected as exc:
                rejection = exc.code
                pending_text = render_action_rejection(
                    call_index=global_call,
                    code=exc.code,
                    message=exc.message,
                    candidate_sha256=world.candidate_sha256,
                )
            except ValueError as exc:
                rejection = "invalid_action"
                pending_text = render_action_rejection(
                    call_index=global_call,
                    code=rejection,
                    message=str(exc),
                    candidate_sha256=world.candidate_sha256,
                )
            row = {
                "actor_call": actor_call,
                "global_actor_call": global_call,
                "prompt_tokens": prompt_tokens,
                "finish_reason": provider.get("finish_reason"),
                "usage": usage,
                "output_sha256": sha256_bytes(output.encode("utf-8")),
                "parsed_action": parsed,
                "rejection_code": rejection,
                "result_id": None if result_record is None else result_record.result_id,
                "result_kind": None if result_record is None else result_record.result_kind,
                "candidate_sha256_before": before,
                "candidate_sha256_after": world.candidate_sha256,
                "current_check_binding": world.current_check_binding(),
                "register_sha256": register.sha256,
                "register_claims": len(register.claims),
            }
            actor_trace.append(row)
            write_json(call_root / "RESULT.json", row)
            if result_record is not None:
                write_json(
                    call_root / "RESULT_RECORD.json",
                    result_record.as_dict(include_exact_content=True),
                )
            messages.append({"role": "user", "content": pending_text})
            if result_record is not None:
                pending_result_id = result_record.result_id
            crossed = budget.record_call(
                construction_milestone_passed=world.construction_milestone()["passed"]
            )
            lifecycle.append(
                {
                    "event": "actor_decision",
                    "actor_call": actor_call,
                    "action": None if parsed is None else parsed.get("action"),
                    "rejection_code": rejection,
                    "candidate_changed": before != world.candidate_sha256,
                    "construction_milestone_crossed": crossed,
                }
            )
            if parsed is not None and parsed.get("action") == "submit" and rejection is None:
                terminal = "submission_proposed"
                break
        else:
            terminal = budget.exhaustion_disposition()

        final_evaluation = external_evaluation(world, cell_root)
        result = {
            "schema": "solace-anchored-interaction-cell-result-v0",
            "configuration_id": configuration_id,
            "terminal_disposition": terminal,
            "actor_calls": len(actor_trace),
            "maintenance_calls": len(maintenance_trace),
            "provider_calls": len(actor_trace) + len(maintenance_trace),
            "serialized_tokens": serialized,
            "candidate_sha256": world.candidate_sha256,
            "candidate_changed": world.candidate_sha256 != boundary["candidate_sha256"],
            "candidate_submitted": world.submitted,
            "construction_budget": budget.as_dict(),
            "construction_milestone": world.construction_milestone(),
            "current_check_binding": world.current_check_binding(),
            "external_evaluation": final_evaluation,
            "relief_events": len(relief_trace),
            "externalized_result_ids": [
                result_id
                for row in relief_trace
                for result_id in row["selected_result_ids"]
            ],
            "register_sha256": register.sha256,
            "register_claims": len(register.claims),
            "maintenance_dispositions": [
                row["admission"]["disposition"] for row in maintenance_trace
            ],
        }
        write_json(cell_root / "ACTOR_TRACE.json", actor_trace)
        write_json(cell_root / "MAINTENANCE_TRACE.json", maintenance_trace)
        write_json(cell_root / "RELIEF_TRACE.json", relief_trace)
        write_json(cell_root / "LIFECYCLE.json", lifecycle)
        write_json(cell_root / "FINAL_MESSAGES.json", messages)
        write_json(cell_root / "RESULT_LEDGER.json", ledger.as_dict(include_exact_content=True))
        write_json(cell_root / "CELL_RESULT.json", result)
    except BudgetStop as exc:
        terminal = str(exc)
        if world is not None:
            final_evaluation = external_evaluation(world, cell_root)
        result = {
            "schema": "solace-anchored-interaction-cell-result-v0",
            "configuration_id": configuration_id,
            "terminal_disposition": terminal,
            "actor_calls": len(actor_trace),
            "maintenance_calls": len(maintenance_trace),
            "provider_calls": len(actor_trace) + len(maintenance_trace),
            "serialized_tokens": serialized,
            "candidate_sha256": None if world is None else world.candidate_sha256,
            "candidate_submitted": False if world is None else world.submitted,
            "external_evaluation": final_evaluation,
            "register_sha256": register.sha256,
            "register_claims": len(register.claims),
        }
        write_json(cell_root / "BUDGET_STOP.json", {"terminal_disposition": terminal})
        write_json(cell_root / "ACTOR_TRACE.json", actor_trace)
        write_json(cell_root / "MAINTENANCE_TRACE.json", maintenance_trace)
        write_json(cell_root / "RELIEF_TRACE.json", relief_trace)
        write_json(cell_root / "LIFECYCLE.json", lifecycle)
        write_json(cell_root / "CELL_RESULT.json", result)
    except BaseException as exc:
        failure = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "no_retry": True,
        }
        write_json(cell_root / "RUN_FAILURE.json", failure)
        raise
    finally:
        if process is not None:
            release = stop_server(process, stdout, stderr, cell_root / "model")
        write_json(cell_root / "FINALIZATION.json", {"failure": failure, "release": release})
        seal_tree(cell_root, cell_root / "RUN_SEAL.json")
    if release is None or release.get("released") is not True:
        raise RuntimeError(f"runtime release failed for {configuration_id}")
    return load(cell_root / "CELL_RESULT.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization-receipt", required=True, type=Path)
    args = parser.parse_args()
    require_clean_tree()
    verify_task_lock()
    handoff = verify_solace_pressure_handoff(ROOT)
    authorization = validate_authorization(args.authorization_receipt)
    preflight = load(PREFLIGHT)
    if preflight.get("passed") is not True:
        raise RuntimeError("frozen preflight did not pass")
    run_root = ROOT / "runs" / RUN_ID
    if run_root.exists():
        raise FileExistsError(f"run root exists: {run_root}")
    run_root.mkdir(parents=True)
    write_json(run_root / "AUTHORIZATION_RECEIPT.json", authorization)
    write_json(
        run_root / "FREEZE_BINDING.json",
        {
            "schema": "solace-anchored-interaction-freeze-v0",
            "commit": git_commit(),
            "run_id": RUN_ID,
            "pressure_handoff": handoff,
            "pressure_handoff_sha256": sha256_file(
                ROOT / "SOLACE_PRESSURE_BOUNDARY_HANDOFF.json"
            ),
            "contract_sha256": sha256_file(CONTRACT),
            "preflight_sha256": sha256_file(PREFLIGHT),
            "task_source_lock_sha256": sha256_file(TASK / "TASK_SOURCE_LOCK.json"),
            "model_profile_lock_sha256": sha256_file(MODEL_LOCK),
        },
    )
    results: list[dict[str, Any]] = []
    failure: dict[str, Any] | None = None
    try:
        for configuration_id in CONFIGURATION_ORDER:
            results.append(run_cell(configuration_id, run_root))
    except BaseException as exc:
        failure = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "no_retry": True,
        }
        write_json(run_root / "RUN_FAILURE.json", failure)
    aggregate = {
        "schema": "solace-anchored-interaction-result-v0",
        "run_id": RUN_ID,
        "freeze_commit": git_commit(),
        "configuration_order": list(CONFIGURATION_ORDER),
        "cells_completed": len(results),
        "actor_calls": sum(int(row["actor_calls"]) for row in results),
        "maintenance_calls": sum(int(row["maintenance_calls"]) for row in results),
        "provider_calls": sum(int(row["provider_calls"]) for row in results),
        "serialized_tokens": sum(int(row["serialized_tokens"]) for row in results),
        "cells": results,
        "failure": failure,
    }
    write_json(run_root / "RUN_RESULT.json", aggregate)
    seal_tree(run_root, run_root / "RUN_SEAL.json")
    print(json.dumps(aggregate, indent=2, sort_keys=True))
    return 0 if failure is None and len(results) == len(CONFIGURATION_ORDER) else 1


if __name__ == "__main__":
    raise SystemExit(main())
