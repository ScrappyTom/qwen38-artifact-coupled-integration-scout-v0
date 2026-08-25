from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.actions import (
    MAX_SOURCE_RESULT_TOKENS,
    action_json_schema,
    parse_action,
    render_action_rejection,
)
from reactive_runtime.activation import boundary_eligibility_failures
from reactive_runtime.canonical import sha256_bytes, sha256_file, write_json
from reactive_runtime.configuration import delta_common_actions
from reactive_runtime.meridian_world import MeridianWorld
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger
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
from tools.verify_runtime_assets import verify as verify_runtime_assets


RUN_ID = "2026-08-25-meridian-source-local-delta-pressure-screen-v0"
SCOPE = "meridian_source_local_delta_pressure_screen_v0"
TASK_ID = "meridian-sterile-infusion-recovery-v0"
SEED = 427_031
MAX_CALLS = 24
MAX_SERIALIZED = 800_000
MAX_WALL = 8_000
PROMPT_LIMIT = 20_992
ACTOR_MAX_TOKENS = 4_096
TASK = ROOT / "task_meridian"
CONTRACT = ROOT / "MERIDIAN_PRESSURE_SCREEN_CONTRACT.json"
MODEL_LOCK = ROOT / "MERIDIAN_MODEL_PROFILE_LOCK.json"


class BudgetStop(RuntimeError):
    pass


def verify_task_lock() -> None:
    lock = json.loads((TASK / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
    if lock.get("task_id") != TASK_ID:
        raise RuntimeError("Meridian task lock identity mismatch")
    for row in lock.get("files", []):
        path = TASK / str(row.get("path"))
        if not path.is_file() or sha256_file(path) != row.get("sha256"):
            raise RuntimeError(f"Meridian task lock mismatch: {row.get('path')}")


def authorize(path: Path) -> dict[str, object]:
    receipt = json.loads(path.resolve().read_text(encoding="utf-8"))
    failures: list[str] = []
    if path.resolve().is_relative_to(ROOT.resolve()):
        failures.append("authorization_must_remain_outside_repository")
    expected = {
        "authorized": True,
        "authorized_freeze_commit": git_commit(),
        "authorized_scopes": [SCOPE],
        "authorized_run_id": RUN_ID,
        "maximum_model_calls": MAX_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            failures.append(f"{key}_mismatch")
    if failures:
        raise RuntimeError(f"authorization failed: {failures}")
    return receipt


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


def stripped_boundary(boundary: dict[str, object] | None) -> dict[str, object] | None:
    if boundary is None:
        return None
    hidden = {"messages", "result_ledger", "candidate_packet"}
    return {key: value for key, value in boundary.items() if key not in hidden}


def counterfactual_relief(
    *,
    messages: list[dict[str, str]],
    ledger: ResultLedger,
    tokenizer: LiveTokenizer,
    pending_result_id: str,
) -> tuple[list[str], int]:
    candidate_messages = [dict(message) for message in messages]
    candidate_ledger = ResultLedger.from_dict(ledger.as_dict(include_exact_content=True))
    selected: list[str] = []
    prompt_tokens = tokenizer.count_messages(candidate_messages)[0]
    while prompt_tokens > PROMPT_LIMIT:
        step = positive_savings_first_fit_step(
            messages=candidate_messages,
            ledger=candidate_ledger,
            prompt_limit=PROMPT_LIMIT,
            count_messages=lambda value: tokenizer.count_messages(value)[0],
            protected_result_ids=(pending_result_id,),
        )
        if not step.selected_result_ids:
            break
        selected.extend(step.selected_result_ids)
        prompt_tokens = step.prompt_tokens
    return selected, prompt_tokens


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization-receipt", required=True, type=Path)
    args = parser.parse_args()
    require_clean_tree()
    verify_task_lock()
    authorization = authorize(args.authorization_receipt)
    run_root = ROOT / "runs" / RUN_ID
    if run_root.exists():
        raise FileExistsError(f"run root exists: {run_root}")
    run_root.mkdir(parents=True)
    write_json(run_root / "AUTHORIZATION_RECEIPT.json", authorization)
    write_json(
        run_root / "FREEZE_BINDING.json",
        {
            "schema": "meridian-pressure-screen-freeze-binding-v0",
            "commit": git_commit(),
            "run_id": RUN_ID,
            "task_source_lock_sha256": sha256_file(TASK / "TASK_SOURCE_LOCK.json"),
            "model_profile_lock_sha256": sha256_file(MODEL_LOCK),
            "screen_contract_sha256": sha256_file(CONTRACT),
        },
    )
    assets = verify_runtime_assets()
    write_json(run_root / "RUNTIME_ASSET_VERIFICATION.json", assets)
    if assets["passed"] is not True:
        raise RuntimeError(f"runtime assets failed: {assets['failures']}")

    process = stdout = stderr = None
    release = failure = None
    world: MeridianWorld | None = None
    trace: list[dict[str, object]] = []
    serialized = 0
    started = time.monotonic()
    try:
        process, stdout, stderr, _ = start_server(run_root / "model")
        tokenizer = LiveTokenizer()
        world = MeridianWorld(TASK, run_root / "trajectory")
        initial_candidate_sha256 = world.candidate_sha256
        ledger = ResultLedger()
        messages = base_messages(world)
        pending_result_id: str | None = None
        next_result = 1
        terminal = "actor_call_budget_exhausted"
        boundary: dict[str, object] | None = None

        for actor_call in range(1, MAX_CALLS + 1):
            prompt_tokens, rendered = tokenizer.count_messages(messages)
            if prompt_tokens > PROMPT_LIMIT:
                if pending_result_id is None:
                    raise RuntimeError("prompt overflow lacks a newly pending exact result")
                pending = ledger.get(pending_result_id)
                ineligible, activation = boundary_eligibility_failures(
                    pending=pending,
                    ledger=ledger,
                    world=world,
                    initial_candidate_sha256=initial_candidate_sha256,
                )
                relief_result_ids, relief_prompt_tokens = counterfactual_relief(
                    messages=messages,
                    ledger=ledger,
                    tokenizer=tokenizer,
                    pending_result_id=pending_result_id,
                )
                if not relief_result_ids or relief_prompt_tokens > PROMPT_LIMIT:
                    ineligible = [*ineligible, "no_positive_feasible_first_fit_relief"]
                boundary = {
                    "schema": "meridian-authentic-pressure-boundary-v0",
                    "task_id": TASK_ID,
                    "actor_calls_completed": actor_call - 1,
                    "pending_result_id": pending_result_id,
                    "ordinary_prospective_prompt_tokens": prompt_tokens,
                    "prompt_limit": PROMPT_LIMIT,
                    "overflow_tokens": prompt_tokens - PROMPT_LIMIT,
                    "messages": messages,
                    "result_ledger": ledger.as_dict(include_exact_content=True),
                    "candidate_sha256": world.candidate_sha256,
                    "candidate_packet": world.candidate_packet(),
                    "activation_snapshot": activation.as_dict(),
                    "eligibility_failures": ineligible,
                    "counterfactual_positive_relief_result_ids": relief_result_ids,
                    "counterfactual_relief_prompt_tokens": relief_prompt_tokens,
                }
                write_json(run_root / "PRESSURE_BOUNDARY.json", boundary)
                if not ineligible:
                    terminal = "authentic_result_delivery_pressure"
                elif any(
                    item in {
                        "insufficient_delivered_source_coverage",
                        "insufficient_delivered_evidence_domains",
                    }
                    for item in ineligible
                ):
                    terminal = "pressure_before_ingress_aligned_activation"
                else:
                    terminal = "pressure_boundary_ineligible"
                break

            if time.monotonic() - started >= MAX_WALL:
                raise BudgetStop("wall_clock_budget_exhausted")
            if serialized + prompt_tokens + ACTOR_MAX_TOKENS > MAX_SERIALIZED:
                raise BudgetStop("serialized_token_budget_exhausted")

            call_root = run_root / "actor" / f"call-{actor_call:03d}"
            write_json(call_root / "messages.json", messages)
            (call_root / "rendered_prompt.txt").parent.mkdir(parents=True, exist_ok=True)
            (call_root / "rendered_prompt.txt").write_text(rendered, encoding="utf-8", newline="")
            external = tuple(
                record.result_id
                for record in ledger.records()
                if record.previously_visible and not record.resident
            )
            schema = action_json_schema(
                delta_common_actions(),
                source_ids=world.sources,
                reopen_result_ids=external,
                decision_headings=world.decision_headings,
                schema_name="meridian_common_actor_action_v0",
            )
            provider = complete_custodied(
                provider_payload(messages, SEED, schema, max_tokens=ACTOR_MAX_TOKENS),
                call_root / "provider_attempt",
            )
            usage = provider.get("usage", {})
            total = usage.get("total_tokens")
            if not isinstance(total, int) or total < prompt_tokens:
                raise RuntimeError("provider usage is absent or inconsistent")
            serialized += total
            output = provider["content"]
            (call_root / "assistant_content.txt").write_text(output, encoding="utf-8", newline="")

            if pending_result_id is not None:
                ledger.mark_model_visible(
                    pending_result_id,
                    call_index=actor_call,
                    message_index=len(messages) - 1,
                )
                pending_result_id = None
            messages.append({"role": "assistant", "content": output})

            parsed = result_record = None
            rejection: str | None = None
            before = world.candidate_sha256
            try:
                parsed = parse_action(
                    output,
                    delta_common_actions(),
                    decision_headings=world.decision_headings,
                )
                result_id = f"RESULT-{next_result:03d}"
                next_result += 1
                execution = world.execute(parsed, result_id=result_id, ledger=ledger)
                result_record = world.make_result_record(
                    execution, result_id=result_id, acquired_call=actor_call
                )
                if (
                    result_record.result_kind == "source_observation"
                    and len(tokenizer.tokenize(result_record.exact_content))
                    > MAX_SOURCE_RESULT_TOKENS
                ):
                    rejection = "source_result_too_large"
                    pending_text = render_action_rejection(
                        call_index=actor_call,
                        code=rejection,
                        message="exact source result exceeded the frozen model-visible token cap and remains audit-only",
                        candidate_sha256=world.candidate_sha256,
                    )
                    result_record = None
                else:
                    ledger.add(result_record)
                    pending_text = result_record.exact_content
            except json.JSONDecodeError as exc:
                rejection = "invalid_json"
                pending_text = render_action_rejection(
                    call_index=actor_call,
                    code=rejection,
                    message=str(exc),
                    candidate_sha256=world.candidate_sha256,
                )
            except ActionRejected as exc:
                rejection = exc.code
                pending_text = render_action_rejection(
                    call_index=actor_call,
                    code=exc.code,
                    message=exc.message,
                    candidate_sha256=world.candidate_sha256,
                )
            except ValueError as exc:
                rejection = "invalid_action"
                pending_text = render_action_rejection(
                    call_index=actor_call,
                    code=rejection,
                    message=str(exc),
                    candidate_sha256=world.candidate_sha256,
                )

            row = {
                "actor_call": actor_call,
                "prompt_tokens": prompt_tokens,
                "usage": usage,
                "finish_reason": provider["finish_reason"],
                "output_sha256": sha256_bytes(output.encode("utf-8")),
                "parsed_action": parsed,
                "rejection_code": rejection,
                "result_id": None if result_record is None else result_record.result_id,
                "result_kind": None if result_record is None else result_record.result_kind,
                "candidate_sha256_before": before,
                "candidate_sha256_after": world.candidate_sha256,
            }
            trace.append(row)
            write_json(call_root / "RESULT.json", row)
            if result_record is not None:
                write_json(
                    call_root / "RESULT_RECORD.json",
                    result_record.as_dict(include_exact_content=True),
                )
            messages.append({"role": "user", "content": pending_text})
            if result_record is not None:
                pending_result_id = result_record.result_id
            if world.candidate_sha256 != initial_candidate_sha256:
                terminal = "candidate_changed_before_pressure"
                break
            if parsed is not None and parsed.get("action") == "run_check":
                terminal = "check_ran_before_pressure"
                break
            if parsed is not None and parsed.get("action") == "submit":
                terminal = "submitted_before_pressure"
                break

        result = {
            "schema": "meridian-pressure-screen-result-v0",
            "task_id": TASK_ID,
            "task_source_lock_sha256": sha256_file(TASK / "TASK_SOURCE_LOCK.json"),
            "model_profile_lock_sha256": sha256_file(MODEL_LOCK),
            "freeze_commit": git_commit(),
            "run_id": RUN_ID,
            "seed": SEED,
            "actor_calls": len(trace),
            "serialized_tokens": serialized,
            "terminal_disposition": terminal,
            "pressure_qualified": terminal == "authentic_result_delivery_pressure",
            "boundary": stripped_boundary(boundary),
            "candidate_sha256": world.candidate_sha256,
            "candidate_submitted": world.submitted,
        }
        write_json(run_root / "CALL_TRACE.json", trace)
        write_json(run_root / "FINAL_MESSAGES.json", messages)
        write_json(run_root / "RESULT_LEDGER.json", ledger.as_dict(include_exact_content=True))
        write_json(run_root / "SCREEN_RESULT.json", result)
    except BudgetStop as exc:
        write_json(run_root / "BUDGET_STOP.json", {"terminal_disposition": str(exc)})
        write_json(
            run_root / "SCREEN_RESULT.json",
            {
                "schema": "meridian-pressure-screen-result-v0",
                "task_id": TASK_ID,
                "freeze_commit": git_commit(),
                "run_id": RUN_ID,
                "actor_calls": len(trace),
                "serialized_tokens": serialized,
                "terminal_disposition": str(exc),
                "pressure_qualified": False,
                "candidate_sha256": None if world is None else world.candidate_sha256,
                "candidate_submitted": False if world is None else world.submitted,
            },
        )
    except BaseException as exc:
        failure = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "no_retry": True,
        }
        write_json(run_root / "RUN_FAILURE.json", failure)
        raise
    finally:
        if process is not None:
            release = stop_server(process, stdout, stderr, run_root / "model")
        write_json(run_root / "FINALIZATION.json", {"failure": failure, "release": release})
        seal_tree(run_root, run_root / "RUN_SEAL.json")
    if release is None or release.get("released") is not True:
        raise RuntimeError("runtime release did not qualify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
