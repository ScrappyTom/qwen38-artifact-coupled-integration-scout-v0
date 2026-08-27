from __future__ import annotations

# ruff: noqa: E402

import argparse
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.actions import action_json_schema, parse_action, render_action_rejection
from reactive_runtime.canonical import sha256_bytes, sha256_file, write_json
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultRecord
from reactive_runtime.seal import seal_tree
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
from tools.solace_verification_lifecycle_stage0 import (
    ALLOWED_ACTIONS,
    CONFIGURATION_ORDER,
    DONOR_EFFECT,
    DONOR_REGISTER,
    EVALUATOR_CONFIG,
    EVALUATOR_SCRIPT,
    TASK,
    create_world,
    donor_ledger,
    verification_messages,
)
from tools.verify_runtime_assets import verify as verify_runtime_assets


RUN_ID = "2026-08-27-solace-verification-lifecycle-measured-v0"
SCOPE = "solace_verification_lifecycle_measured_v0"
SEED = 531_703
CONTEXT_TOKENS = 25_088
PROMPT_LIMIT = 20_992
MAX_TOKENS = 4_096
MAX_ACTOR_CALLS_PER_CELL = 12
MAX_PROVIDER_CALLS = 24
MAX_SERIALIZED_TOKENS_PER_CELL = 500_000
MAX_WALL_SECONDS_PER_CELL = 3_600
CONTRACT = ROOT / "SOLACE_VERIFICATION_LIFECYCLE_CONTRACT.json"
PREFLIGHT = ROOT / "SOLACE_VERIFICATION_LIFECYCLE_PREFLIGHT.json"
REQUEST = ROOT / "SOLACE_VERIFICATION_LIFECYCLE_AUTHORIZATION_REQUEST.json"
MODEL_LOCK = ROOT / "SOLACE_MODEL_PROFILE_LOCK.json"
DONOR_LOCK = ROOT / "SOLACE_VERIFICATION_LIFECYCLE_DONOR_LOCK.json"


class BudgetStop(RuntimeError):
    pass


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def checked_usage(provider: dict[str, Any], expected_prompt: int) -> dict[str, Any]:
    usage = provider.get("usage")
    if not isinstance(usage, dict):
        raise RuntimeError("provider usage missing")
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    total = usage.get("total_tokens")
    if prompt != expected_prompt or type(completion) is not int or not 0 <= completion <= MAX_TOKENS:
        raise RuntimeError("provider usage mismatch")
    if total != prompt + completion:
        raise RuntimeError("provider usage arithmetic mismatch")
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "cached_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens"),
    }


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
        "maximum_actor_calls": 24,
        "maximum_provider_calls": MAX_PROVIDER_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
        "authorization_text": request["expected_user_quote_template"].replace("{commit}", commit),
    }
    failures = [key for key, value in expected.items() if receipt.get(key) != value]
    if failures:
        raise RuntimeError(f"authorization receipt mismatch: {failures}")
    return receipt


def restore_feasibility(
    messages: list[dict[str, str]], ledger: Any, tokenizer: LiveTokenizer, trace: list[dict[str, Any]]
) -> None:
    while tokenizer.count_messages(messages)[0] > PROMPT_LIMIT:
        step = positive_savings_first_fit_step(
            messages=messages,
            ledger=ledger,
            prompt_limit=PROMPT_LIMIT,
            count_messages=lambda rows: tokenizer.count_messages(rows)[0],
            protected_result_ids=(),
        )
        trace.append(
            {
                "event": len(trace) + 1,
                "selected_result_ids": list(step.selected_result_ids),
                "prompt_tokens": step.prompt_tokens,
                "feasible": step.feasible,
            }
        )
        if not step.selected_result_ids:
            raise BudgetStop("verification_prompt_pressure_without_feasible_relief")


def run_cell(configuration_id: str, run_root: Path) -> dict[str, Any]:
    cell_root = run_root / "cells" / configuration_id
    cell_root.mkdir(parents=True, exist_ok=False)
    process = stdout = stderr = None
    release: dict[str, Any] | None = None
    failure: dict[str, Any] | None = None
    world = None
    started = time.monotonic()
    serialized = 0
    trace: list[dict[str, Any]] = []
    relief: list[dict[str, Any]] = []
    terminal = "uninitialized"
    try:
        assets = verify_runtime_assets()
        write_json(cell_root / "RUNTIME_ASSET_VERIFICATION.json", assets)
        if assets.get("passed") is not True:
            raise RuntimeError("runtime assets failed")
        process, stdout, stderr, _ = start_server(cell_root / "model")
        tokenizer = LiveTokenizer()
        world = create_world(cell_root / "trajectory")
        messages = verification_messages(configuration_id, world)
        ledger = donor_ledger()
        effect_record = ResultRecord.from_dict(load(DONOR_EFFECT))
        ledger.add(effect_record)
        state_index = 5
        ledger.mark_model_visible("RESULT-015", call_index=16, message_index=state_index)
        next_result = 16
        write_json(
            cell_root / "INITIAL_STATE.json",
            {
                "configuration_id": configuration_id,
                "candidate_sha256": world.candidate_sha256,
                "candidate_version": world.candidate_version,
                "register_sha256": load(DONOR_REGISTER)["sha256"] if configuration_id.startswith("A1_") else None,
                "messages": messages,
                "result_ledger": ledger.as_dict(include_exact_content=True),
            },
        )

        for call_index in range(1, MAX_ACTOR_CALLS_PER_CELL + 1):
            restore_feasibility(messages, ledger, tokenizer, relief)
            if time.monotonic() - started >= MAX_WALL_SECONDS_PER_CELL:
                raise BudgetStop("wall_clock_budget_exhausted")
            prompt_tokens, rendered = tokenizer.count_messages(messages)
            if serialized + prompt_tokens + MAX_TOKENS > MAX_SERIALIZED_TOKENS_PER_CELL:
                raise BudgetStop("serialized_token_budget_exhausted")
            call_root = cell_root / "actor" / f"call-{call_index:03d}"
            write_json(call_root / "messages.json", messages)
            (call_root / "rendered_prompt.txt").parent.mkdir(parents=True, exist_ok=True)
            (call_root / "rendered_prompt.txt").write_text(rendered, encoding="utf-8", newline="")
            external = tuple(
                record.result_id for record in ledger.records() if record.previously_visible and not record.resident
            )
            schema = action_json_schema(
                ALLOWED_ACTIONS,
                source_ids=world.sources,
                reopen_result_ids=external,
                decision_headings=world.decision_headings,
                schema_name=f"solace_{configuration_id.casefold()}_verification_action_v0",
            )
            provider = complete_custodied(
                provider_payload(messages, SEED, schema, max_tokens=MAX_TOKENS),
                call_root / "provider_attempt",
                timeout=max(1, min(900, int(MAX_WALL_SECONDS_PER_CELL - (time.monotonic() - started)))),
            )
            usage = checked_usage(provider, prompt_tokens)
            serialized += int(usage["total_tokens"])
            output = str(provider["content"])
            (call_root / "assistant_content.txt").write_text(output, encoding="utf-8", newline="")
            messages.append({"role": "assistant", "content": output})
            before = world.candidate_sha256
            parsed = None
            record = None
            rejection = None
            try:
                parsed = parse_action(output, ALLOWED_ACTIONS, decision_headings=world.decision_headings)
                result_id = f"RESULT-{next_result:03d}"
                next_result += 1
                execution = world.execute(parsed, result_id=result_id, ledger=ledger)
                record = world.make_result_record(execution, result_id=result_id, acquired_call=15 + call_index)
                ledger.add(record)
                pending = record.exact_content
                if record.result_kind == "candidate_effect":
                    for prior in ledger.records():
                        if prior.result_kind == "check_observation" and prior.evaluated_candidate_sha256 != world.candidate_sha256:
                            prior.relief_eligible = True
            except json.JSONDecodeError as exc:
                rejection = "invalid_json"
                pending = render_action_rejection(call_index=call_index, code=rejection, message=str(exc), candidate_sha256=world.candidate_sha256)
            except ActionRejected as exc:
                rejection = exc.code
                pending = render_action_rejection(call_index=call_index, code=exc.code, message=exc.message, candidate_sha256=world.candidate_sha256)
            except ValueError as exc:
                rejection = "invalid_action"
                pending = render_action_rejection(call_index=call_index, code=rejection, message=str(exc), candidate_sha256=world.candidate_sha256)
            messages.append({"role": "user", "content": pending})
            if record is not None:
                ledger.mark_model_visible(record.result_id, call_index=16 + call_index, message_index=len(messages) - 1)
            row = {
                "actor_call": call_index,
                "prompt_tokens": prompt_tokens,
                "usage": usage,
                "finish_reason": provider.get("finish_reason"),
                "output_sha256": sha256_bytes(output.encode("utf-8")),
                "parsed_action": parsed,
                "rejection_code": rejection,
                "result_id": None if record is None else record.result_id,
                "result_kind": None if record is None else record.result_kind,
                "candidate_sha256_before": before,
                "candidate_sha256_after": world.candidate_sha256,
                "current_check_binding": world.current_check_binding(),
            }
            trace.append(row)
            write_json(call_root / "RESULT.json", row)
            if record is not None:
                write_json(call_root / "RESULT_RECORD.json", record.as_dict(include_exact_content=True))
            if parsed is not None and parsed.get("action") == "submit" and rejection is None:
                terminal = "submission_proposed"
                break
        else:
            terminal = "actor_call_budget_exhausted"

        external_evaluation = world._run_check("EXTERNAL-FINAL-EVALUATION")
        result = {
            "schema": "solace-verification-lifecycle-cell-result-v0",
            "configuration_id": configuration_id,
            "terminal_disposition": terminal,
            "actor_calls": len(trace),
            "provider_calls": len(trace),
            "serialized_tokens": serialized,
            "candidate_sha256": world.candidate_sha256,
            "candidate_changed": world.candidate_sha256 != "82d14bff607d8e323899d09b72739ee4bf14bc067013c6675365b580093ecf5a",
            "candidate_submitted": world.submitted,
            "current_check_binding": world.current_check_binding(),
            "external_evaluation": external_evaluation.metadata["check_projection"],
            "relief_events": relief,
        }
        write_json(cell_root / "ACTOR_TRACE.json", trace)
        write_json(cell_root / "RELIEF_TRACE.json", relief)
        write_json(cell_root / "FINAL_MESSAGES.json", messages)
        write_json(cell_root / "RESULT_LEDGER.json", ledger.as_dict(include_exact_content=True))
        write_json(cell_root / "CELL_RESULT.json", result)
    except BudgetStop as exc:
        terminal = str(exc)
        result = {
            "schema": "solace-verification-lifecycle-cell-result-v0",
            "configuration_id": configuration_id,
            "terminal_disposition": terminal,
            "actor_calls": len(trace),
            "provider_calls": len(trace),
            "serialized_tokens": serialized,
            "candidate_sha256": None if world is None else world.candidate_sha256,
            "candidate_submitted": False if world is None else world.submitted,
            "relief_events": relief,
        }
        write_json(cell_root / "BUDGET_STOP.json", {"terminal_disposition": terminal})
        write_json(cell_root / "ACTOR_TRACE.json", trace)
        write_json(cell_root / "RELIEF_TRACE.json", relief)
        write_json(cell_root / "CELL_RESULT.json", result)
    except BaseException as exc:
        failure = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(), "no_retry": True}
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
    authorization = validate_authorization(args.authorization_receipt)
    preflight = load(PREFLIGHT)
    if preflight.get("passed") is not True:
        raise RuntimeError("frozen preflight did not pass")
    run_root = ROOT / "runs" / RUN_ID
    if run_root.exists():
        raise FileExistsError(run_root)
    run_root.mkdir(parents=True)
    write_json(run_root / "AUTHORIZATION_RECEIPT.json", authorization)
    write_json(
        run_root / "FREEZE_BINDING.json",
        {
            "schema": "solace-verification-lifecycle-freeze-v0",
            "commit": git_commit(),
            "run_id": RUN_ID,
            "contract_sha256": sha256_file(CONTRACT),
            "preflight_sha256": sha256_file(PREFLIGHT),
            "model_profile_lock_sha256": sha256_file(MODEL_LOCK),
            "evaluator_config_sha256": sha256_file(EVALUATOR_CONFIG),
            "evaluator_script_sha256": sha256_file(EVALUATOR_SCRIPT),
            "donor_effect_sha256": sha256_file(DONOR_EFFECT),
            "donor_lock_sha256": sha256_file(DONOR_LOCK),
            "verification_actions_sha256": sha256_file(TASK / "VERIFICATION_ACTIONS.md"),
        },
    )
    results: list[dict[str, Any]] = []
    failure = None
    try:
        for configuration_id in CONFIGURATION_ORDER:
            results.append(run_cell(configuration_id, run_root))
    except BaseException as exc:
        failure = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(), "no_retry": True}
        write_json(run_root / "RUN_FAILURE.json", failure)
    aggregate = {
        "schema": "solace-verification-lifecycle-result-v0",
        "run_id": RUN_ID,
        "freeze_commit": git_commit(),
        "configuration_order": list(CONFIGURATION_ORDER),
        "cells_completed": len(results),
        "actor_calls": sum(int(row["actor_calls"]) for row in results),
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
