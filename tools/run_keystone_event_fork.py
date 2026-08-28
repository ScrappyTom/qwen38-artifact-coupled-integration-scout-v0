from __future__ import annotations

# ruff: noqa: E402

import argparse
import json
import sys
import time
import traceback
from copy import deepcopy
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
from reactive_runtime.canonical import (
    canonical_json_text,
    sha256_bytes,
    sha256_file,
    write_json,
)
from reactive_runtime.causal_activation import (
    activation_tax,
    detect_causal_fork_activation,
)
from reactive_runtime.configuration import causal_verification_actor_actions
from reactive_runtime.keystone_event_fork import (
    CommonForkState,
    branch_binding,
    clone_common_state,
)
from reactive_runtime.keystone_world import KeystoneWorld
from reactive_runtime.policy import positive_savings_first_fit_step
from reactive_runtime.records import ResultLedger, ResultRecord
from reactive_runtime.seal import seal_tree, verify_tree_seal
from reactive_runtime.verification_causal_lifecycle import verification_messages
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


RUN_ID = "2026-08-27-keystone-event-triggered-causal-continuation-v0"
SCOPE = "keystone_event_triggered_causal_continuation_v0"
TASK_ID = "keystone-rail-restoration-decision-v0"
PARENT_RUN = ROOT / "runs" / "2026-08-27-keystone-bounded-causal-pressure-screen-v0"
CONTRACT = ROOT / "KEYSTONE_EVENT_FORK_CONTRACT.json"
PREFLIGHT = ROOT / "KEYSTONE_EVENT_FORK_PREFLIGHT.json"
TASK = ROOT / "task_keystone"
MODEL_LOCK = ROOT / "KEYSTONE_MODEL_PROFILE_LOCK.json"
CONFIGURATION_ORDER = ("V0_CURRENT_ONLY", "V1_BOUNDED_CAUSAL_CONTINUITY")
PROMPT_LIMIT = 20_992
CONTEXT_TOKENS = 25_088
ACTOR_MAX_TOKENS = 4_096
MAX_COMMON_MODEL_CALLS = 18
MAX_BRANCH_CALLS = 8
MAX_NEW_MODEL_CALLS = 34
MAX_NEW_SERIALIZED_TOKENS = 700_000
MAX_WALL_SECONDS = 18_000
HISTORY_HANDLE = f"history://{RUN_ID}/common-prefix"


class BudgetStop(RuntimeError):
    pass


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


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
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "cached_tokens": (usage.get("prompt_tokens_details") or {}).get(
            "cached_tokens"
        ),
    }


def validate_authorization(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if resolved.is_relative_to(ROOT.resolve()):
        raise RuntimeError("authorization receipt must remain outside the repository")
    receipt = load(resolved)
    expected = {
        "authorized": True,
        "authorized_freeze_commit": git_commit(),
        "authorized_scopes": [SCOPE],
        "authorized_run_id": RUN_ID,
        "maximum_model_calls": MAX_NEW_MODEL_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
    }
    failures = [key for key, value in expected.items() if receipt.get(key) != value]
    if not isinstance(receipt.get("authorization_id"), str) or not receipt.get(
        "authorization_id"
    ):
        failures.append("authorization_id")
    if failures:
        raise RuntimeError(f"authorization failed: {sorted(failures)}")
    return receipt


def verify_frozen_inputs(*, verify_runner_binding: bool = True) -> dict[str, Any]:
    contract = load(CONTRACT)
    preflight = load(PREFLIGHT)
    if preflight.get("passed") is not True:
        raise RuntimeError("frozen provider-free preflight did not pass")
    if preflight.get("contract_sha256") != sha256_file(CONTRACT):
        raise RuntimeError("frozen preflight does not bind the current contract")
    if verify_runner_binding:
        runner = contract.get("runner")
        if not isinstance(runner, dict):
            raise RuntimeError("frozen contract lacks runner binding")
        runner_path = ROOT / str(runner.get("path"))
        qualification_path = ROOT / str(runner.get("qualification_path"))
        if runner.get("runner_sha256") != sha256_file(runner_path):
            raise RuntimeError("frozen contract does not bind the live runner")
        if runner.get("qualification_sha256") != sha256_file(qualification_path):
            raise RuntimeError("frozen contract does not bind runner qualification")
        qualification = load(qualification_path)
        if qualification.get("passed") is not True:
            raise RuntimeError("frozen runner qualification did not pass")
        if qualification.get("runner_source_bound") is not True:
            raise RuntimeError("runner qualification did not bind its source")
        if qualification.get("runner_sha256") != runner.get("runner_sha256"):
            raise RuntimeError("runner qualification binds a different runner")
    parent = contract["parent"]
    locks = contract["source_locks"]
    expected = {
        PARENT_RUN / "RUN_SEAL.json": parent["run_seal_sha256"],
        PARENT_RUN / "PRESSURE_BOUNDARY.json": parent["pressure_boundary_sha256"],
        PARENT_RUN / "SCREEN_RESULT.json": parent["screen_result_sha256"],
        TASK / "TASK_SOURCE_LOCK.json": locks["task_source_lock_sha256"],
        MODEL_LOCK: locks["model_profile_lock_sha256"],
        ROOT / "MODEL_PROFILE_LOCK.json": locks["tokenizer_projection_lock_sha256"],
    }
    failures = [
        path.relative_to(ROOT).as_posix()
        for path, digest in expected.items()
        if not path.is_file() or sha256_file(path) != digest
    ]
    failures.extend(verify_tree_seal(PARENT_RUN, PARENT_RUN / "RUN_SEAL.json"))
    if failures:
        raise RuntimeError(f"frozen input verification failed: {failures}")
    return contract


def source_catalog() -> dict[str, dict[str, object]]:
    value = load(TASK / "SOURCE_CATALOG.json")
    return {str(row["source_id"]): row for row in value["sources"]}


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
    if not register.claims:
        return
    message = {"role": "user", "content": register.render()}
    index = register_message_index(messages)
    if index is None:
        messages.append(message)
    else:
        messages[index] = message


def result_message_index(
    messages: Sequence[dict[str, str]], record: ResultRecord
) -> int:
    matches = [
        index
        for index, message in enumerate(messages)
        if message == {"role": "user", "content": record.exact_content}
    ]
    if len(matches) != 1:
        raise RuntimeError(f"result message binding is not unique: {record.result_id}")
    return matches[0]


def current_submission_authorized(world: KeystoneWorld) -> bool:
    binding = world.current_check_binding()
    return bool(
        binding
        and binding.get("currency") == "current"
        and binding.get("passed") is True
        and binding.get("evaluated_candidate_sha256") == world.candidate_sha256
    )


def external_evaluation(world: KeystoneWorld, output_root: Path) -> dict[str, Any]:
    prior = deepcopy(world.last_check_projection)
    execution = world._run_check("EXTERNAL-FINAL-EVALUATION")
    projection = execution.metadata.get("check_projection")
    world.last_check_projection = prior
    value = {
        "schema": "keystone-external-evaluation-v0",
        "actor_visible": False,
        "candidate_sha256": world.candidate_sha256,
        "evaluated_candidate_sha256": execution.evaluated_candidate_sha256,
        "projection": projection,
        "exact_projection_body": execution.body,
    }
    write_json(output_root / "evaluation" / "MECHANICAL_FINAL_EVALUATION.json", value)
    if (
        not isinstance(projection, dict)
        or projection.get("protocol_error_class") is not None
    ):
        raise RuntimeError("external evaluator protocol failure")
    return value


def trace_metrics(
    trace: list[dict[str, Any]], *, fork_trace_length: int
) -> dict[str, Any]:
    post = trace[fork_trace_length:]
    effect_rows = [row for row in post if row.get("result_kind") == "candidate_effect"]
    rechecks = [row for row in post if row.get("result_kind") == "check_observation"]
    submitted = any(row.get("result_kind") == "submission_effect" for row in post)
    alternative = None
    if effect_rows:
        alternative = {
            "actor_call": effect_rows[0]["actor_call"],
            "result_id": effect_rows[0]["result_id"],
            "candidate_sha256_after": effect_rows[0]["candidate_sha256_after"],
        }
    effect_uptake = False
    if effect_rows:
        effect_call = int(effect_rows[0]["actor_call"])
        effect_uptake = any(int(row["actor_call"]) > effect_call for row in post)
    return {
        "alternative_repair": alternative,
        "effect_uptake": effect_uptake,
        "current_recheck": (
            None
            if not rechecks
            else {
                "actor_call": rechecks[-1]["actor_call"],
                "result_id": rechecks[-1]["result_id"],
                "binding": rechecks[-1].get("current_check_binding"),
            }
        ),
        "submission_effect": submitted,
    }


def run_common(
    run_root: Path,
    contract: dict[str, Any],
    started: float,
) -> tuple[CommonForkState | None, KeystoneWorld, dict[str, Any]]:
    common_root = run_root / "common"
    common_root.mkdir(parents=True, exist_ok=False)
    process = stdout = stderr = None
    release: dict[str, Any] | None = None
    failure: dict[str, Any] | None = None
    boundary = load(PARENT_RUN / "PRESSURE_BOUNDARY.json")
    parent = contract["parent"]
    messages = deepcopy(boundary["messages"])
    ledger = ResultLedger.from_dict(deepcopy(boundary["result_ledger"]))
    world = KeystoneWorld(
        TASK,
        common_root / "trajectory",
        candidate_seed_root=PARENT_RUN / "trajectory" / "world" / "candidate",
    )
    if world.candidate_sha256 != parent["candidate_sha256"]:
        raise RuntimeError("restored parent candidate mismatch")
    pending_result_id: str | None = str(boundary["pending_result_id"])
    next_result = 10
    trace: list[dict[str, Any]] = []
    maintenance_trace: list[dict[str, Any]] = []
    relief_trace: list[dict[str, Any]] = []
    lifecycle: list[dict[str, Any]] = []
    register = AnchoredProvenanceRegister()
    phase = "construction"
    latest_effect_result_id: str | None = None
    actor_calls = int(parent["actor_calls"])
    model_calls = 0
    serialized = 0
    terminal = "uninitialized"
    activation = detect_causal_fork_activation(
        trace, initial_candidate_sha256=str(parent["candidate_sha256"])
    )
    task_system = (TASK / "SYSTEM.md").read_text(encoding="utf-8")
    task_text = (TASK / "TASK.md").read_text(encoding="utf-8")
    verification_actions = (TASK / "VERIFICATION_ACTIONS.md").read_text(
        encoding="utf-8"
    )
    catalog = source_catalog()
    model_lock = load(MODEL_LOCK)
    actor_seed = int(model_lock["measured_actor_seed"])
    maintenance_seed = int(model_lock["measured_maintenance_seed"])
    common_state: CommonForkState | None = None

    try:
        process, stdout, stderr, _ = start_server(common_root / "model")
        tokenizer = LiveTokenizer()

        def count(rows: list[dict[str, str]]) -> int:
            return int(tokenizer.count_messages(rows)[0])

        def admit_cost(prompt_tokens: int, maximum: int) -> None:
            if time.monotonic() - started >= MAX_WALL_SECONDS:
                raise BudgetStop("wall_clock_budget_exhausted")
            if model_calls >= MAX_COMMON_MODEL_CALLS:
                raise BudgetStop("common_model_call_budget_exhausted")
            if serialized + prompt_tokens + maximum > MAX_NEW_SERIALIZED_TOKENS:
                raise BudgetStop("global_serialized_token_budget_exhausted")

        def write_register_state() -> None:
            write_json(
                common_root / "CURRENT_REGISTER.json",
                {
                    "sha256": register.sha256,
                    "claims": [asdict(claim) for claim in register.claims],
                    "rendered": register.render(),
                },
            )

        def run_maintenance(records: Sequence[ResultRecord], trigger: str) -> None:
            nonlocal register, model_calls, serialized
            if not records or phase != "construction":
                return
            ordinal = len(maintenance_trace) + 1
            call_root = common_root / "maintenance" / f"call-{ordinal:03d}"
            maintenance_messages = anchored_delta_messages(
                task_text=task_text,
                register=register,
                newly_externalized=records,
                source_versions=world.source_versions,
            )
            prompt_tokens, rendered = tokenizer.count_messages(maintenance_messages)
            if prompt_tokens + DELTA_TOKEN_BUDGET > CONTEXT_TOKENS:
                raise BudgetStop("maintenance_prompt_infeasible")
            admit_cost(prompt_tokens, DELTA_TOKEN_BUDGET)
            write_json(call_root / "messages.json", maintenance_messages)
            (call_root / "rendered_prompt.txt").parent.mkdir(
                parents=True, exist_ok=True
            )
            (call_root / "rendered_prompt.txt").write_text(
                rendered, encoding="utf-8", newline=""
            )
            provider = complete_custodied(
                provider_payload(
                    maintenance_messages,
                    maintenance_seed,
                    {"type": "text"},
                    max_tokens=DELTA_TOKEN_BUDGET,
                ),
                call_root / "provider_attempt",
            )
            usage = checked_usage(provider, prompt_tokens, DELTA_TOKEN_BUDGET)
            model_calls += 1
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
                "prompt_tokens": prompt_tokens,
                "usage": usage,
                "finish_reason": provider.get("finish_reason"),
                "output_sha256": sha256_bytes(output.encode("utf-8")),
                "admission": asdict(admission),
                "transition": asdict(transition),
                "register_sha256": register.sha256,
                "register_claims": len(register.claims),
            }
            maintenance_trace.append(row)
            lifecycle.append({"event": "semantic_maintenance", **row})
            write_json(call_root / "RESULT.json", row)
            write_register_state()

        def restore_feasibility(trigger: str) -> None:
            while count(messages) > PROMPT_LIMIT:
                protected = () if pending_result_id is None else (pending_result_id,)
                before = count(messages)
                step = positive_savings_first_fit_step(
                    messages=messages,
                    ledger=ledger,
                    prompt_limit=PROMPT_LIMIT,
                    count_messages=count,
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
                run_maintenance(
                    [
                        ledger.get(result_id)
                        for result_id in step.selected_result_ids
                        if ledger.get(result_id).result_kind == "source_observation"
                    ],
                    "positive_savings_externalization",
                )

        def compose_verification(pending_text: str | None) -> None:
            nonlocal messages
            for record in ledger.records():
                if record.previously_visible:
                    ledger.mark_external(record.result_id)
            scaffold_handle = f"scaffold://{RUN_ID}/common/{register.sha256}"
            messages = verification_messages(
                "V0_CURRENT_ONLY",
                system_text=task_system,
                task_text=task_text,
                action_text=verification_actions,
                source_catalog=world.source_catalog_for_actor(),
                candidate_packet=world.candidate_packet(),
                trace=trace,
                history_handle=HISTORY_HANDLE,
                scaffold_handle=scaffold_handle,
                pending_exact_result=pending_text,
            )
            if pending_result_id is not None:
                record = ledger.get(pending_result_id)
                record.resident = True
                record.message_index = len(messages) - 1

        if pending_result_id is None:
            raise RuntimeError("sealed parent boundary lacks its pending result")
        first_relief = positive_savings_first_fit_step(
            messages=messages,
            ledger=ledger,
            prompt_limit=PROMPT_LIMIT,
            count_messages=count,
            protected_result_ids=(pending_result_id,),
        )
        expected_relief = contract["common_continuation"]["first_relief_result_ids"]
        if list(first_relief.selected_result_ids) != expected_relief:
            raise RuntimeError(
                "common first-fit selection disagrees with frozen contract"
            )
        relief_trace.append(
            {
                "relief_event": 1,
                "trigger": "sealed_parent_pressure",
                "before_tokens": boundary["ordinary_prospective_prompt_tokens"],
                "after_tokens": first_relief.prompt_tokens,
                "selected_result_ids": list(first_relief.selected_result_ids),
                "feasible": first_relief.feasible,
                "audits": [asdict(value) for value in first_relief.audits],
            }
        )
        run_maintenance(
            [ledger.get(result_id) for result_id in first_relief.selected_result_ids],
            "sealed_parent_pressure",
        )
        messages.append(
            {
                "role": "user",
                "content": (
                    "# Current Keystone lifecycle phase\n"
                    "Phase: construction. Build exact task work and use "
                    "`begin_verification` only after the frozen mechanical "
                    "construction milestone is met."
                ),
            }
        )
        restore_feasibility("post_relief_scaffold_and_phase_status")

        while model_calls < MAX_COMMON_MODEL_CALLS:
            restore_feasibility("ordinary_common_actor_prompt")
            actor_calls += 1
            if pending_result_id is not None:
                pending = ledger.get(pending_result_id)
                ledger.mark_model_visible(
                    pending_result_id,
                    call_index=actor_calls,
                    message_index=result_message_index(messages, pending),
                )
                lifecycle.append(
                    {
                        "event": "result_delivery",
                        "actor_call": actor_calls,
                        "result_id": pending_result_id,
                    }
                )
                pending_result_id = None
            prompt_tokens, rendered = tokenizer.count_messages(messages)
            if prompt_tokens > PROMPT_LIMIT:
                raise BudgetStop("common_prompt_infeasible_after_relief")
            admit_cost(prompt_tokens, ACTOR_MAX_TOKENS)
            local_call = actor_calls - int(parent["actor_calls"])
            call_root = common_root / "actor" / f"call-{local_call:03d}"
            write_json(call_root / "messages.json", messages)
            (call_root / "rendered_prompt.txt").parent.mkdir(
                parents=True, exist_ok=True
            )
            (call_root / "rendered_prompt.txt").write_text(
                rendered, encoding="utf-8", newline=""
            )
            actions = causal_verification_actor_actions("V0_CURRENT_ONLY", phase=phase)
            external = tuple(
                record.result_id
                for record in ledger.records()
                if record.previously_visible and not record.resident
            )
            schema = action_json_schema(
                actions,
                source_ids=world.sources,
                reopen_result_ids=external,
                decision_headings=world.decision_headings,
                schema_name=f"keystone_common_{phase}_action_v0",
            )
            provider = complete_custodied(
                provider_payload(
                    messages, actor_seed, schema, max_tokens=ACTOR_MAX_TOKENS
                ),
                call_root / "provider_attempt",
            )
            usage = checked_usage(provider, prompt_tokens, ACTOR_MAX_TOKENS)
            model_calls += 1
            serialized += int(usage["total_tokens"])
            output = str(provider["content"])
            (call_root / "assistant_content.txt").write_text(
                output, encoding="utf-8", newline=""
            )
            if phase == "construction":
                messages.append({"role": "assistant", "content": output})
            before = world.candidate_sha256
            phase_before = phase
            parsed: dict[str, Any] | None = None
            result_record: ResultRecord | None = None
            rejection: str | None = None
            pending_text: str
            try:
                parsed = parse_action(
                    output, actions, decision_headings=world.decision_headings
                )
                if parsed["action"] == "submit" and not current_submission_authorized(
                    world
                ):
                    raise ActionRejected(
                        "submission_without_current_passing_check",
                        "submission requires a current passing candidate-bound check",
                    )
                result_id = f"RESULT-{next_result:03d}"
                next_result += 1
                execution = world.execute(parsed, result_id=result_id, ledger=ledger)
                result_record = world.make_result_record(
                    execution, result_id=result_id, acquired_call=actor_calls
                )
                if (
                    result_record.result_kind == "source_observation"
                    and len(tokenizer.tokenize(result_record.exact_content))
                    > MAX_SOURCE_RESULT_TOKENS
                ):
                    rejection = "source_result_too_large"
                    pending_text = render_action_rejection(
                        call_index=actor_calls,
                        code=rejection,
                        message="exact source result exceeded the frozen cap and remains audit-only",
                        candidate_sha256=world.candidate_sha256,
                    )
                    result_record = None
                else:
                    ledger.add(result_record)
                    pending_result_id = result_record.result_id
                    pending_text = result_record.exact_content
                    if result_record.result_kind in {
                        "candidate_effect",
                        "phase_effect",
                    }:
                        latest_effect_result_id = result_record.result_id
            except json.JSONDecodeError as exc:
                rejection = "invalid_json"
                pending_text = render_action_rejection(
                    call_index=actor_calls,
                    code=rejection,
                    message=str(exc),
                    candidate_sha256=world.candidate_sha256,
                )
            except ActionRejected as exc:
                rejection = exc.code
                pending_text = render_action_rejection(
                    call_index=actor_calls,
                    code=exc.code,
                    message=exc.message,
                    candidate_sha256=world.candidate_sha256,
                )
            except ValueError as exc:
                rejection = "invalid_action"
                pending_text = render_action_rejection(
                    call_index=actor_calls,
                    code=rejection,
                    message=str(exc),
                    candidate_sha256=world.candidate_sha256,
                )
            if world.phase == "verification":
                phase = "verification"
            row = {
                "actor_call": actor_calls,
                "common_actor_call": local_call,
                "phase_before": phase_before,
                "phase_after": phase,
                "prompt_tokens": prompt_tokens,
                "usage": usage,
                "finish_reason": provider.get("finish_reason"),
                "output_sha256": sha256_bytes(output.encode("utf-8")),
                "parsed_action": parsed,
                "rejection_code": rejection,
                "result_id": None if result_record is None else result_record.result_id,
                "result_kind": None
                if result_record is None
                else result_record.result_kind,
                "candidate_sha256_before": before,
                "candidate_sha256_after": world.candidate_sha256,
                "current_check_binding": world.current_check_binding(),
                "register_sha256": register.sha256,
                "register_claims": len(register.claims),
            }
            trace.append(row)
            lifecycle.append(
                {
                    "event": "actor_decision",
                    "actor_call": actor_calls,
                    "phase": phase_before,
                    "action": None if parsed is None else parsed.get("action"),
                    "rejection_code": rejection,
                    "candidate_changed": before != world.candidate_sha256,
                }
            )
            write_json(call_root / "RESULT.json", row)
            if result_record is not None:
                write_json(
                    call_root / "RESULT_RECORD.json",
                    result_record.as_dict(include_exact_content=True),
                )

            if phase == "verification":
                compose_verification(pending_text)
                activation = detect_causal_fork_activation(
                    trace,
                    initial_candidate_sha256=str(parent["candidate_sha256"]),
                )
                if activation.qualified:
                    terminal = "causal_trigger_observed_before_next_actor_decision"
                    common_state = CommonForkState(
                        messages=deepcopy(messages),
                        ledger=ResultLedger.from_dict(
                            deepcopy(ledger.as_dict(include_exact_content=True))
                        ),
                        trace=deepcopy(trace),
                        register=register,
                        phase=phase,
                        pending_result_id=pending_result_id,
                        next_result_ordinal=next_result,
                        latest_effect_result_id=latest_effect_result_id,
                        actor_calls_completed=actor_calls,
                        model_calls_completed=model_calls,
                        serialized_tokens=serialized,
                    )
                    break
            else:
                messages.append({"role": "user", "content": pending_text})
                expose_register(messages, register)
            if (
                result_record is not None
                and result_record.result_kind == "submission_effect"
            ):
                terminal = "submitted_before_causal_trigger"
                break
        else:
            terminal = "causal_trigger_not_observed"
    except BudgetStop as exc:
        terminal = str(exc)
    except BaseException as exc:
        failure = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "no_retry": True,
        }
        write_json(common_root / "RUN_FAILURE.json", failure)
        raise
    finally:
        if process is not None:
            release = stop_server(process, stdout, stderr, common_root / "model")
        write_json(
            common_root / "FINALIZATION.json", {"failure": failure, "release": release}
        )
        write_json(common_root / "ACTOR_TRACE.json", trace)
        write_json(common_root / "MAINTENANCE_TRACE.json", maintenance_trace)
        write_json(common_root / "RELIEF_TRACE.json", relief_trace)
        write_json(common_root / "LIFECYCLE.json", lifecycle)
        write_json(common_root / "FINAL_MESSAGES.json", messages)
        write_json(
            common_root / "RESULT_LEDGER.json",
            ledger.as_dict(include_exact_content=True),
        )
        if common_state is not None:
            write_json(
                common_root / "COMMON_FORK_STATE.json", common_state.binding(world)
            )
    if release is None or release.get("released") is not True:
        raise RuntimeError("common runtime release failed")
    result = {
        "schema": "keystone-common-continuation-result-v0",
        "terminal_disposition": terminal,
        "trigger_observed": common_state is not None,
        "actor_calls": len(trace),
        "model_calls": model_calls,
        "maintenance_calls": len(maintenance_trace),
        "serialized_tokens": serialized,
        "candidate_sha256": world.candidate_sha256,
        "phase": phase,
        "activation": activation.as_dict(),
        "activation_tax": activation_tax(
            activation,
            parent_calls=int(parent["actor_calls"]),
            parent_serialized_tokens=int(parent["serialized_tokens"]),
            continuation_trace=trace,
        ),
    }
    write_json(common_root / "COMMON_RESULT.json", result)
    seal_tree(common_root, common_root / "RUN_SEAL.json")
    return common_state, world, result


def run_branch(
    configuration_id: str,
    common: CommonForkState,
    common_world: KeystoneWorld,
    run_root: Path,
    *,
    serialized_budget: int,
    started: float,
) -> dict[str, Any]:
    branch_root = run_root / "branches" / configuration_id
    branch_root.mkdir(parents=True, exist_ok=False)
    state = clone_common_state(common, common_world, branch_root / "trajectory")
    before_binding = branch_binding(state)
    common_binding = common.binding(common_world)
    if before_binding != common_binding:
        raise RuntimeError(f"branch clone mismatch: {configuration_id}")
    write_json(branch_root / "FORK_BINDING.json", before_binding)
    process = stdout = stderr = None
    release: dict[str, Any] | None = None
    failure: dict[str, Any] | None = None
    local_trace: list[dict[str, Any]] = []
    lifecycle: list[dict[str, Any]] = []
    branch_serialized = 0
    terminal = "stop_incomplete"
    model_lock = load(MODEL_LOCK)
    actor_seed = int(model_lock["measured_actor_seed"])
    task_system = (TASK / "SYSTEM.md").read_text(encoding="utf-8")
    task_text = (TASK / "TASK.md").read_text(encoding="utf-8")
    verification_actions = (TASK / "VERIFICATION_ACTIONS.md").read_text(
        encoding="utf-8"
    )
    fork_trace_length = len(state.trace)

    def compose(pending_text: str | None) -> None:
        for record in state.ledger.records():
            if record.previously_visible:
                state.ledger.mark_external(record.result_id)
        state.messages = verification_messages(
            configuration_id,
            system_text=task_system,
            task_text=task_text,
            action_text=verification_actions,
            source_catalog=state.world.source_catalog_for_actor(),
            candidate_packet=state.world.candidate_packet(),
            trace=state.trace,
            history_handle=HISTORY_HANDLE,
            scaffold_handle=f"scaffold://{RUN_ID}/common/{state.register.sha256}",
            pending_exact_result=pending_text,
        )
        if state.pending_result_id is not None:
            record = state.ledger.get(state.pending_result_id)
            record.resident = True
            record.message_index = len(state.messages) - 1

    pending_text = (
        None
        if state.pending_result_id is None
        else state.ledger.get(state.pending_result_id).exact_content
    )
    compose(pending_text)
    first_prompt_hash = sha256_bytes(
        canonical_json_text(state.messages).encode("utf-8")
    )

    try:
        process, stdout, stderr, _ = start_server(branch_root / "model")
        tokenizer = LiveTokenizer()
        for branch_call in range(1, MAX_BRANCH_CALLS + 1):
            if time.monotonic() - started >= MAX_WALL_SECONDS:
                raise BudgetStop("wall_clock_budget_exhausted")
            if state.pending_result_id is not None:
                record = state.ledger.get(state.pending_result_id)
                state.ledger.mark_model_visible(
                    state.pending_result_id,
                    call_index=state.actor_calls_completed + 1,
                    message_index=result_message_index(state.messages, record),
                )
                lifecycle.append(
                    {
                        "event": "result_delivery",
                        "branch_call": branch_call,
                        "actor_call": state.actor_calls_completed + 1,
                        "result_id": state.pending_result_id,
                    }
                )
                state.pending_result_id = None
            prompt_tokens, rendered = tokenizer.count_messages(state.messages)
            if prompt_tokens > PROMPT_LIMIT:
                terminal = "exact_branch_infeasible"
                break
            if branch_serialized + prompt_tokens + ACTOR_MAX_TOKENS > serialized_budget:
                terminal = "branch_serialized_token_budget_exhausted"
                break
            call_root = branch_root / "actor" / f"call-{branch_call:03d}"
            write_json(call_root / "messages.json", state.messages)
            (call_root / "rendered_prompt.txt").parent.mkdir(
                parents=True, exist_ok=True
            )
            (call_root / "rendered_prompt.txt").write_text(
                rendered, encoding="utf-8", newline=""
            )
            actions = causal_verification_actor_actions(
                configuration_id, phase="verification"
            )
            external = tuple(
                record.result_id
                for record in state.ledger.records()
                if record.previously_visible and not record.resident
            )
            schema = action_json_schema(
                actions,
                source_ids=state.world.sources,
                reopen_result_ids=external,
                decision_headings=state.world.decision_headings,
                schema_name=f"keystone_{configuration_id.lower()}_action_v0",
            )
            provider = complete_custodied(
                provider_payload(
                    state.messages, actor_seed, schema, max_tokens=ACTOR_MAX_TOKENS
                ),
                call_root / "provider_attempt",
            )
            usage = checked_usage(provider, prompt_tokens, ACTOR_MAX_TOKENS)
            branch_serialized += int(usage["total_tokens"])
            state.model_calls_completed += 1
            state.actor_calls_completed += 1
            output = str(provider["content"])
            (call_root / "assistant_content.txt").write_text(
                output, encoding="utf-8", newline=""
            )
            before = state.world.candidate_sha256
            parsed: dict[str, Any] | None = None
            result_record: ResultRecord | None = None
            rejection: str | None = None
            try:
                parsed = parse_action(
                    output, actions, decision_headings=state.world.decision_headings
                )
                if parsed["action"] == "submit" and not current_submission_authorized(
                    state.world
                ):
                    raise ActionRejected(
                        "submission_without_current_passing_check",
                        "submission requires a current passing candidate-bound check",
                    )
                result_id = f"RESULT-{state.next_result_ordinal:03d}"
                state.next_result_ordinal += 1
                execution = state.world.execute(
                    parsed, result_id=result_id, ledger=state.ledger
                )
                result_record = state.world.make_result_record(
                    execution,
                    result_id=result_id,
                    acquired_call=state.actor_calls_completed,
                )
                if (
                    result_record.result_kind == "source_observation"
                    and len(tokenizer.tokenize(result_record.exact_content))
                    > MAX_SOURCE_RESULT_TOKENS
                ):
                    rejection = "source_result_too_large"
                    pending_text = render_action_rejection(
                        call_index=state.actor_calls_completed,
                        code=rejection,
                        message="exact source result exceeded the frozen cap and remains audit-only",
                        candidate_sha256=state.world.candidate_sha256,
                    )
                    result_record = None
                else:
                    state.ledger.add(result_record)
                    state.pending_result_id = result_record.result_id
                    pending_text = result_record.exact_content
                    if result_record.result_kind in {
                        "candidate_effect",
                        "phase_effect",
                    }:
                        state.latest_effect_result_id = result_record.result_id
            except json.JSONDecodeError as exc:
                rejection = "invalid_json"
                pending_text = render_action_rejection(
                    call_index=state.actor_calls_completed,
                    code=rejection,
                    message=str(exc),
                    candidate_sha256=state.world.candidate_sha256,
                )
            except ActionRejected as exc:
                rejection = exc.code
                pending_text = render_action_rejection(
                    call_index=state.actor_calls_completed,
                    code=exc.code,
                    message=exc.message,
                    candidate_sha256=state.world.candidate_sha256,
                )
            except ValueError as exc:
                rejection = "invalid_action"
                pending_text = render_action_rejection(
                    call_index=state.actor_calls_completed,
                    code=rejection,
                    message=str(exc),
                    candidate_sha256=state.world.candidate_sha256,
                )
            row = {
                "actor_call": state.actor_calls_completed,
                "branch_call": branch_call,
                "configuration_id": configuration_id,
                "prompt_tokens": prompt_tokens,
                "usage": usage,
                "finish_reason": provider.get("finish_reason"),
                "output_sha256": sha256_bytes(output.encode("utf-8")),
                "parsed_action": parsed,
                "rejection_code": rejection,
                "result_id": None if result_record is None else result_record.result_id,
                "result_kind": None
                if result_record is None
                else result_record.result_kind,
                "candidate_sha256_before": before,
                "candidate_sha256_after": state.world.candidate_sha256,
                "current_check_binding": state.world.current_check_binding(),
            }
            state.trace.append(row)
            local_trace.append(row)
            lifecycle.append(
                {
                    "event": "actor_decision",
                    "branch_call": branch_call,
                    "actor_call": state.actor_calls_completed,
                    "action": None if parsed is None else parsed.get("action"),
                    "rejection_code": rejection,
                    "candidate_changed": before != state.world.candidate_sha256,
                }
            )
            write_json(call_root / "RESULT.json", row)
            if result_record is not None:
                write_json(
                    call_root / "RESULT_RECORD.json",
                    result_record.as_dict(include_exact_content=True),
                )
            compose(pending_text)
            if (
                result_record is not None
                and result_record.result_kind == "submission_effect"
            ):
                terminal = "submitted"
                break
        else:
            terminal = "stop_incomplete"
    except BudgetStop as exc:
        terminal = str(exc)
    except BaseException as exc:
        failure = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "no_retry": True,
        }
        write_json(branch_root / "RUN_FAILURE.json", failure)
        raise
    finally:
        if process is not None:
            release = stop_server(process, stdout, stderr, branch_root / "model")
        write_json(
            branch_root / "FINALIZATION.json", {"failure": failure, "release": release}
        )
    if release is None or release.get("released") is not True:
        raise RuntimeError(f"branch runtime release failed: {configuration_id}")

    evaluation = external_evaluation(state.world, branch_root)
    metrics = trace_metrics(state.trace, fork_trace_length=fork_trace_length)
    result = {
        "schema": "keystone-event-triggered-causal-branch-result-v0",
        "configuration_id": configuration_id,
        "terminal_disposition": terminal,
        "branch_calls": len(local_trace),
        "branch_serialized_tokens": branch_serialized,
        "branch_serialized_token_budget": serialized_budget,
        "first_treatment_prompt_sha256": first_prompt_hash,
        "candidate_sha256": state.world.candidate_sha256,
        "candidate_submitted": state.world.submitted,
        "current_check_binding": state.world.current_check_binding(),
        "external_evaluation": evaluation,
        "readiness": (
            "mechanically_ready"
            if (evaluation.get("projection") or {}).get("passed") is True
            else "not_ready"
        ),
        "truthful_closure": terminal in {"submitted", "stop_incomplete"},
        **metrics,
    }
    write_json(branch_root / "ACTOR_TRACE.json", local_trace)
    write_json(branch_root / "FULL_TRACE.json", state.trace)
    write_json(branch_root / "LIFECYCLE.json", lifecycle)
    write_json(branch_root / "FINAL_MESSAGES.json", state.messages)
    write_json(
        branch_root / "RESULT_LEDGER.json",
        state.ledger.as_dict(include_exact_content=True),
    )
    write_json(branch_root / "BRANCH_RESULT.json", result)
    seal_tree(branch_root, branch_root / "RUN_SEAL.json")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization-receipt", required=True, type=Path)
    args = parser.parse_args()
    require_clean_tree()
    contract = verify_frozen_inputs()
    authorization = validate_authorization(args.authorization_receipt)
    run_root = ROOT / "runs" / RUN_ID
    if run_root.exists():
        raise FileExistsError(f"run root exists: {run_root}")
    run_root.mkdir(parents=True)
    write_json(run_root / "AUTHORIZATION_RECEIPT.json", authorization)
    write_json(
        run_root / "FREEZE_BINDING.json",
        {
            "schema": "keystone-event-triggered-causal-freeze-v0",
            "commit": git_commit(),
            "run_id": RUN_ID,
            "contract_sha256": sha256_file(CONTRACT),
            "preflight_sha256": sha256_file(PREFLIGHT),
            "parent_run_seal_sha256": sha256_file(PARENT_RUN / "RUN_SEAL.json"),
            "task_source_lock_sha256": sha256_file(TASK / "TASK_SOURCE_LOCK.json"),
            "model_profile_lock_sha256": sha256_file(MODEL_LOCK),
        },
    )
    assets = verify_runtime_assets()
    write_json(run_root / "RUNTIME_ASSET_VERIFICATION.json", assets)
    if assets.get("passed") is not True:
        raise RuntimeError(f"runtime assets failed: {assets.get('failures')}")

    started = time.monotonic()
    failure: dict[str, Any] | None = None
    branches: list[dict[str, Any]] = []
    common_result: dict[str, Any] | None = None
    try:
        common, common_world, common_result = run_common(run_root, contract, started)
        if common is not None:
            remaining = MAX_NEW_SERIALIZED_TOKENS - common.serialized_tokens
            per_branch_serialized = remaining // len(CONFIGURATION_ORDER)
            for configuration_id in CONFIGURATION_ORDER:
                branches.append(
                    run_branch(
                        configuration_id,
                        common,
                        common_world,
                        run_root,
                        serialized_budget=per_branch_serialized,
                        started=started,
                    )
                )
    except BaseException as exc:
        failure = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "no_retry": True,
        }
        write_json(run_root / "RUN_FAILURE.json", failure)

    common_calls = 0 if common_result is None else int(common_result["model_calls"])
    branch_calls = sum(int(row["branch_calls"]) for row in branches)
    common_tokens = (
        0 if common_result is None else int(common_result["serialized_tokens"])
    )
    branch_tokens = sum(int(row["branch_serialized_tokens"]) for row in branches)
    aggregate = {
        "schema": "keystone-event-triggered-causal-continuation-result-v0",
        "run_id": RUN_ID,
        "freeze_commit": git_commit(),
        "configuration_order": list(CONFIGURATION_ORDER),
        "common": common_result,
        "branches": branches,
        "branches_completed": len(branches),
        "new_model_calls": common_calls + branch_calls,
        "new_serialized_tokens": common_tokens + branch_tokens,
        "elapsed_seconds": time.monotonic() - started,
        "treatment_activated": bool(
            common_result and common_result.get("trigger_observed") is True
        ),
        "failure": failure,
        "promotion_authorized": False,
    }
    write_json(run_root / "RUN_RESULT.json", aggregate)
    seal_tree(run_root, run_root / "RUN_SEAL.json")
    print(json.dumps(aggregate, indent=2, sort_keys=True))
    observed_model_calls = common_calls + branch_calls
    observed_serialized_tokens = common_tokens + branch_tokens
    common_terminal = (
        None if common_result is None else common_result.get("terminal_disposition")
    )
    passed = (
        failure is None
        and common_result is not None
        and common_terminal
        in {
            "causal_trigger_not_observed",
            "causal_trigger_observed_before_next_actor_decision",
        }
        and (
            common_result.get("trigger_observed") is False
            or len(branches) == len(CONFIGURATION_ORDER)
        )
        and observed_model_calls <= MAX_NEW_MODEL_CALLS
        and observed_serialized_tokens <= MAX_NEW_SERIALIZED_TOKENS
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
