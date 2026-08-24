from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.actions import MAX_BATCH_RESULT_TOKENS, action_json_schema, parse_action, render_action_rejection
from reactive_runtime.canonical import sha256_bytes, sha256_file, write_json
from reactive_runtime.configuration import ordinary_actions
from reactive_runtime.records import ResultLedger
from reactive_runtime.seal import seal_tree
from reactive_runtime.world import ActionRejected, ArchitectureWorld
from tools.live_common import LiveTokenizer, complete_custodied, git_commit, provider_payload, require_clean_tree, start_server, stop_server
from tools.verify_runtime_assets import verify as verify_runtime_assets


RUN_ID = "2026-08-24-northstar-transfer-pressure-screen-v0"
SCOPE = "northstar_transfer_pressure_screen_v0"
SEED = 860_241
MAX_CALLS = 18
MAX_SERIALIZED = 500_000
MAX_WALL = 7200
PROMPT_LIMIT = 20_992
ACTOR_MAX_TOKENS = 4096


class BudgetStop(RuntimeError):
    pass


def verify_task_lock() -> None:
    lock = json.loads((ROOT / "task" / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
    if lock.get("task_id") != "northstar-migration-architecture-package-v0":
        raise RuntimeError("task lock identity mismatch")
    for row in lock.get("files", []):
        path = ROOT / "task" / str(row.get("path"))
        if not path.is_file() or sha256_file(path) != row.get("sha256"):
            raise RuntimeError(f"task lock mismatch: {row.get('path')}")


def boundary_eligibility_failures(
    *, pending: object, ledger: ResultLedger, world: ArchitectureWorld, initial_candidate_sha256: str
) -> list[str]:
    """Classify a realized overflow without inferring semantic task readiness."""
    failures: list[str] = []
    if getattr(pending, "result_kind", None) != "source_observation":
        failures.append("pending_result_is_not_source_observation")
    delivered_sources = sum(
        record.result_kind == "source_observation" and record.previously_visible
        for record in ledger.records()
    )
    if delivered_sources < 4:
        failures.append("fewer_than_four_source_observations_delivered")
    if world.candidate_sha256 != initial_candidate_sha256:
        failures.append("candidate_changed_before_pressure")
    if world.submitted:
        failures.append("candidate_submitted_before_pressure")
    if any(record.result_kind == "check_observation" for record in ledger.records()):
        failures.append("check_ran_before_pressure")
    return failures


def authorize(path: Path) -> dict[str, object]:
    receipt = json.loads(path.resolve().read_text(encoding="utf-8"))
    failures = []
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
            "schema": "northstar-pressure-screen-freeze-binding-v0",
            "commit": git_commit(),
            "run_id": RUN_ID,
            "task_source_lock_sha256": sha256_file(
                ROOT / "task" / "TASK_SOURCE_LOCK.json"
            ),
            "model_profile_lock_sha256": sha256_file(ROOT / "MODEL_PROFILE_LOCK.json"),
            "screen_contract_sha256": sha256_file(ROOT / "PRESSURE_SCREEN_CONTRACT.json"),
        },
    )
    assets = verify_runtime_assets()
    write_json(run_root / "RUNTIME_ASSET_VERIFICATION.json", assets)
    if assets["passed"] is not True:
        raise RuntimeError(f"runtime assets failed: {assets['failures']}")
    process = stdout = stderr = None
    release = failure = None
    world = None
    trace = []
    serialized = 0
    started = time.monotonic()
    try:
        process, stdout, stderr, _ = start_server(run_root / "model")
        tokenizer = LiveTokenizer()
        world = ArchitectureWorld(ROOT / "task", run_root / "trajectory")
        initial_candidate_sha256 = world.candidate_sha256
        ledger = ResultLedger()
        messages = [
            {"role": "system", "content": (ROOT / "task" / "SYSTEM.md").read_text(encoding="utf-8")},
            {"role": "user", "content": (ROOT / "task" / "TASK.md").read_text(encoding="utf-8")},
            {"role": "user", "content": (ROOT / "task" / "ACTIONS.md").read_text(encoding="utf-8") + "\n\n# Exact source catalog\n" + world.source_catalog_for_actor()},
            {"role": "user", "content": "# Exact current candidate\n" + world.candidate_packet()},
        ]
        pending_result_id = None
        next_result = 1
        terminal = "actor_call_budget_exhausted"
        boundary = None
        for actor_call in range(1, MAX_CALLS + 1):
            prompt_tokens, rendered = tokenizer.count_messages(messages)
            if prompt_tokens > PROMPT_LIMIT:
                if pending_result_id is None:
                    raise RuntimeError("prompt overflow lacks a newly pending exact result")
                pending = ledger.get(pending_result_id)
                delivered_sources = sum(
                    record.result_kind == "source_observation" and record.previously_visible
                    for record in ledger.records()
                )
                ineligible = boundary_eligibility_failures(
                    pending=pending,
                    ledger=ledger,
                    world=world,
                    initial_candidate_sha256=initial_candidate_sha256,
                )
                boundary = {"schema": "northstar-authentic-pressure-boundary-v0", "task_id": "northstar-migration-architecture-package-v0", "actor_calls_completed": actor_call - 1, "pending_result_id": pending_result_id, "ordinary_prospective_prompt_tokens": prompt_tokens, "prompt_limit": PROMPT_LIMIT, "overflow_tokens": prompt_tokens - PROMPT_LIMIT, "messages": messages, "result_ledger": ledger.as_dict(include_exact_content=True), "candidate_sha256": world.candidate_sha256, "candidate_packet": world.candidate_packet(), "delivered_source_observations": delivered_sources, "eligibility_failures": ineligible}
                write_json(run_root / "PRESSURE_BOUNDARY.json", boundary)
                terminal = "authentic_result_delivery_pressure" if not ineligible else "pressure_boundary_ineligible"
                break
            if time.monotonic() - started >= MAX_WALL:
                raise BudgetStop("wall_clock_budget_exhausted")
            if serialized + prompt_tokens + ACTOR_MAX_TOKENS > MAX_SERIALIZED:
                raise BudgetStop("serialized_token_budget_exhausted")
            call_root = run_root / "actor" / f"call-{actor_call:03d}"
            write_json(call_root / "messages.json", messages)
            (call_root / "rendered_prompt.txt").parent.mkdir(parents=True, exist_ok=True)
            (call_root / "rendered_prompt.txt").write_text(rendered, encoding="utf-8", newline="")
            external = tuple(record.result_id for record in ledger.records() if record.previously_visible and not record.resident)
            schema = action_json_schema(ordinary_actions(), source_ids=world.sources, reopen_result_ids=external)
            provider = complete_custodied(provider_payload(messages, SEED, schema, max_tokens=ACTOR_MAX_TOKENS), call_root / "provider_attempt")
            usage = provider.get("usage", {})
            total = usage.get("total_tokens")
            if not isinstance(total, int) or total < prompt_tokens:
                raise RuntimeError("provider usage is absent or inconsistent")
            serialized += total
            output = provider["content"]
            (call_root / "assistant_content.txt").write_text(output, encoding="utf-8", newline="")
            if pending_result_id is not None:
                ledger.mark_model_visible(pending_result_id, call_index=actor_call, message_index=len(messages) - 1)
                pending_result_id = None
            messages.append({"role": "assistant", "content": output})
            parsed = result_record = None
            rejection = None
            before = world.candidate_sha256
            try:
                parsed = parse_action(output, ordinary_actions())
                result_id = f"RESULT-{next_result:03d}"
                next_result += 1
                execution = world.execute(parsed, result_id=result_id, ledger=ledger)
                result_record = world.make_result_record(execution, result_id=result_id, acquired_call=actor_call)
                if parsed["action"] == "read_batch" and len(tokenizer.tokenize(result_record.exact_content)) > MAX_BATCH_RESULT_TOKENS:
                    rejection = "batch_result_too_large"
                    pending_text = render_action_rejection(call_index=actor_call, code=rejection, message="exact batch result exceeded the frozen model-visible token cap and remains audit-only", candidate_sha256=world.candidate_sha256)
                    result_record = None
                else:
                    ledger.add(result_record)
                    pending_text = result_record.exact_content
            except json.JSONDecodeError as exc:
                rejection = "invalid_json"
                pending_text = render_action_rejection(call_index=actor_call, code=rejection, message=str(exc), candidate_sha256=world.candidate_sha256)
            except ActionRejected as exc:
                rejection = exc.code
                pending_text = render_action_rejection(call_index=actor_call, code=exc.code, message=exc.message, candidate_sha256=world.candidate_sha256)
            except ValueError as exc:
                rejection = "invalid_action"
                pending_text = render_action_rejection(call_index=actor_call, code=rejection, message=str(exc), candidate_sha256=world.candidate_sha256)
            row = {"actor_call": actor_call, "prompt_tokens": prompt_tokens, "usage": usage, "finish_reason": provider["finish_reason"], "output_sha256": sha256_bytes(output.encode("utf-8")), "parsed_action": parsed, "rejection_code": rejection, "result_id": None if result_record is None else result_record.result_id, "result_kind": None if result_record is None else result_record.result_kind, "candidate_sha256_before": before, "candidate_sha256_after": world.candidate_sha256}
            trace.append(row)
            write_json(call_root / "RESULT.json", row)
            if result_record is not None:
                write_json(call_root / "RESULT_RECORD.json", result_record.as_dict(include_exact_content=True))
            if parsed is not None and parsed.get("action") == "submit" and result_record is not None:
                terminal = "submitted_before_pressure"
                break
            messages.append({"role": "user", "content": pending_text})
            if result_record is not None:
                pending_result_id = result_record.result_id
        result = {"schema": "northstar-transfer-pressure-screen-result-v0", "task_id": "northstar-migration-architecture-package-v0", "freeze_commit": git_commit(), "run_id": RUN_ID, "seed": SEED, "actor_calls": len(trace), "serialized_tokens": serialized, "terminal_disposition": terminal, "pressure_qualified": terminal == "authentic_result_delivery_pressure", "boundary": None if boundary is None else {key: value for key, value in boundary.items() if key not in {"messages", "result_ledger", "candidate_packet"}}, "candidate_sha256": world.candidate_sha256, "candidate_submitted": world.submitted}
        write_json(run_root / "CALL_TRACE.json", trace)
        write_json(run_root / "FINAL_MESSAGES.json", messages)
        write_json(run_root / "RESULT_LEDGER.json", ledger.as_dict(include_exact_content=True))
        write_json(run_root / "SCREEN_RESULT.json", result)
    except BudgetStop as exc:
        write_json(run_root / "BUDGET_STOP.json", {"terminal_disposition": str(exc)})
        write_json(run_root / "SCREEN_RESULT.json", {"schema": "northstar-transfer-pressure-screen-result-v0", "task_id": "northstar-migration-architecture-package-v0", "freeze_commit": git_commit(), "run_id": RUN_ID, "seed": SEED, "actor_calls": len(trace), "serialized_tokens": serialized, "terminal_disposition": str(exc), "pressure_qualified": False, "candidate_sha256": None if world is None else world.candidate_sha256, "candidate_submitted": False if world is None else world.submitted})
    except BaseException as exc:
        failure = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(), "no_retry": True}
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
