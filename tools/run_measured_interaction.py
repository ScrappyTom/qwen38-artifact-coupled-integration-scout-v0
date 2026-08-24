from __future__ import annotations

import argparse
import json
import re
import sys
import time
import traceback
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.actions import (  # noqa: E402
    MAX_BATCH_RESULT_TOKENS,
    action_json_schema,
    parse_action,
    render_action_rejection,
)
from reactive_runtime.boundary import (  # noqa: E402
    hydrate_pressure_boundary,
    verify_pressure_handoff,
)
from reactive_runtime.canonical import (  # noqa: E402
    canonical_json_text,
    sha256_bytes,
    sha256_file,
    write_json,
)
from reactive_runtime.configuration import CONFIGURATIONS, ordinary_actions  # noqa: E402
from reactive_runtime.integration import (  # noqa: E402
    INTEGRATION_PROVIDER_MAX_TOKENS,
    IntegrationArtifact,
    integration_messages,
    next_artifact,
    observed_source_ids,
    validate_integration,
)
from reactive_runtime.interaction_state import (  # noqa: E402
    current_interaction_state_message,
    exact_history_directory,
)
from reactive_runtime.policy import positive_savings_first_fit_step  # noqa: E402
from reactive_runtime.records import ResultLedger, ResultRecord  # noqa: E402
from reactive_runtime.seal import seal_tree  # noqa: E402
from reactive_runtime.world import ActionRejected, ArchitectureWorld  # noqa: E402
from tools.live_common import (  # noqa: E402
    LiveTokenizer,
    complete_custodied,
    git_commit,
    provider_payload,
    require_clean_tree,
    start_server,
    stop_server,
)
from tools.verify_runtime_assets import verify as verify_runtime_assets  # noqa: E402


RUN_ID = "2026-08-24-artifact-coupled-interaction-measured-v0"
SCOPE = "artifact_coupled_interaction_measured_v0"
CONFIGURATION_ORDER = ("D0_DETACHED", "A1_COUPLED")
ACTOR_SEED = 271_830
MAINTENANCE_SEED = 271_831
PROMPT_LIMIT = 20_992
CONTEXT_TOKENS = 25_088
ACTOR_MAX_TOKENS = 4_096
MAX_ACTOR_CALLS_PER_CELL = 20
MAX_MAINTENANCE_CALLS_PER_CELL = 12
MAX_REENTRIES_PER_CELL = 2
MAX_PROVIDER_CALLS = len(CONFIGURATION_ORDER) * (
    MAX_ACTOR_CALLS_PER_CELL + MAX_MAINTENANCE_CALLS_PER_CELL
)
MAX_SERIALIZED_TOKENS_PER_CELL = 1_000_000
MAX_WALL_SECONDS_PER_CELL = 7_200


class BudgetStop(RuntimeError):
    def __init__(self, disposition: str) -> None:
        super().__init__(disposition)
        self.disposition = disposition


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def verify_task_lock() -> None:
    lock = load(ROOT / "task" / "TASK_SOURCE_LOCK.json")
    for row in lock.get("files", []):
        path = ROOT / "task" / str(row["path"])
        if not path.is_file() or sha256_file(path) != row.get("sha256"):
            raise RuntimeError(f"task lock mismatch: {row.get('path')}")


def validate_authorization(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise RuntimeError("authorization receipt must remain outside the repository")
    receipt = load(resolved)
    request = load(ROOT / "MEASURED_AUTHORIZATION_REQUEST.json")
    commit = git_commit()
    expected = {
        "authorized": True,
        "authorized_freeze_commit": commit,
        "authorized_run_id": RUN_ID,
        "authorized_scope": SCOPE,
        "configuration_order": list(CONFIGURATION_ORDER),
        "maximum_actor_calls": MAX_ACTOR_CALLS_PER_CELL * len(CONFIGURATION_ORDER),
        "maximum_maintenance_calls": MAX_MAINTENANCE_CALLS_PER_CELL
        * len(CONFIGURATION_ORDER),
        "maximum_provider_calls": MAX_PROVIDER_CALLS,
        "attempts_per_call": 1,
        "retries": 0,
        "user_quote": request["expected_user_quote_template"].replace("{commit}", commit),
    }
    failures = [key for key, expected_value in expected.items() if receipt.get(key) != expected_value]
    if not isinstance(receipt.get("authorization_id"), str) or not receipt["authorization_id"]:
        failures.append("authorization_id")
    if failures:
        raise RuntimeError(f"authorization receipt mismatch: {sorted(set(failures))}")
    return receipt


def checked_usage(
    result: dict[str, Any], expected_prompt: int, maximum_completion: int
) -> dict[str, Any]:
    usage = result.get("usage")
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
        raise RuntimeError("provider total count invalid")
    details = usage.get("prompt_tokens_details") or {}
    cached = details.get("cached_tokens")
    if cached is not None and (type(cached) is not int or not 0 <= cached <= prompt):
        raise RuntimeError("cached prompt count invalid")
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "cached_tokens": cached,
    }


def count_messages(tokenizer: LiveTokenizer, messages: list[dict[str, str]]) -> int:
    return tokenizer.count_messages(messages)[0]


def delivered_source_ids(ledger: ResultLedger, include: ResultRecord | None = None) -> tuple[str, ...]:
    values: set[str] = set()
    for record in ledger.records():
        if record.previously_visible or record is include:
            values.update(observed_source_ids(record))
    return tuple(sorted(values))


def current_maintenance_prior(
    configuration_id: str,
    world: ArchitectureWorld,
    integration: IntegrationArtifact | None,
    tokenizer: LiveTokenizer,
    ledger: ResultLedger,
) -> IntegrationArtifact | None:
    if integration is None or configuration_id != "A1_COUPLED":
        return integration
    body = (world.candidate_root / "EVIDENCE_INTEGRATION_LEDGER.md").read_text(
        encoding="utf-8"
    )
    delivered = set(delivered_source_ids(ledger))
    actor_bound_sources = set(
        re.findall(r"(?<![A-Za-z0-9])S(?:0[1-9]|1[0-4])(?![A-Za-z0-9])", body)
    ) & delivered
    return IntegrationArtifact(
        version=integration.version,
        body=body,
        body_tokens=len(tokenizer.tokenize(body)),
        input_result_ids=integration.input_result_ids,
        observed_source_ids=tuple(
            sorted(set(integration.observed_source_ids) | actor_bound_sources)
        ),
    )


def external_evaluation(world: ArchitectureWorld, cell_root: Path) -> dict[str, Any]:
    execution = world._run_check("EXTERNAL-FINAL-EVALUATION")
    projection = execution.metadata.get("check_projection")
    value = {
        "schema": "artifact-coupled-external-evaluation-v0",
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


def run_cell(configuration_id: str, root: Path) -> dict[str, Any]:
    if configuration_id not in CONFIGURATIONS:
        raise ValueError(configuration_id)
    cell_root = root / "cells" / configuration_id
    cell_root.mkdir(parents=True, exist_ok=False)
    process = stdout = stderr = None
    release: dict[str, Any] | None = None
    failure: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    started = time.monotonic()
    try:
        assets = verify_runtime_assets()
        write_json(cell_root / "RUNTIME_ASSET_VERIFICATION.json", assets)
        if assets.get("passed") is not True:
            raise RuntimeError(f"runtime assets failed: {assets.get('failures')}")
        process, stdout, stderr, gate = start_server(cell_root / "model")
        tokenizer = LiveTokenizer()
        world = ArchitectureWorld(ROOT / "task", cell_root / "trajectory")
        boundary = hydrate_pressure_boundary(repository_root=ROOT, world=world)
        messages = boundary.messages
        ledger = boundary.ledger
        pending = ledger.get(boundary.pending_result_id)
        pending.message_index = boundary.pending_message_index
        integration: IntegrationArtifact | None = None
        interaction_state_index: int | None = None
        latest_rejection: str | None = None
        next_result = boundary.next_result_ordinal
        actor_calls = 0
        maintenance_calls = 0
        reentries = 0
        serialized_tokens = 0
        maintenance_effect_ordinal = 0
        lifecycle: list[dict[str, Any]] = []
        trace: list[dict[str, Any]] = []
        maintenance_trace: list[dict[str, Any]] = []

        def elapsed() -> float:
            return time.monotonic() - started

        def admit(prompt_tokens: int, maximum: int, kind: str) -> None:
            if elapsed() >= MAX_WALL_SECONDS_PER_CELL:
                raise BudgetStop("wall_clock_budget_exhausted")
            if serialized_tokens + prompt_tokens + maximum > MAX_SERIALIZED_TOKENS_PER_CELL:
                raise BudgetStop("serialized_token_budget_exhausted")
            if kind == "actor" and actor_calls >= MAX_ACTOR_CALLS_PER_CELL:
                raise BudgetStop("actor_call_budget_exhausted")
            if kind == "maintenance" and maintenance_calls >= MAX_MAINTENANCE_CALLS_PER_CELL:
                raise BudgetStop("maintenance_call_budget_exhausted")

        def refresh_interaction_state() -> None:
            nonlocal interaction_state_index
            state = current_interaction_state_message(
                configuration_id=configuration_id,
                world=world,
                integration=integration,
                embed_integration_body=True,
            )
            if interaction_state_index is None:
                messages.append(state)
                interaction_state_index = len(messages) - 1
            else:
                messages[interaction_state_index] = state

        def append_effect_record(execution: Any) -> ResultRecord:
            nonlocal maintenance_effect_ordinal
            maintenance_effect_ordinal += 1
            result_id = f"MAINT-EFFECT-{maintenance_effect_ordinal:03d}"
            record = world.make_result_record(
                execution,
                result_id=result_id,
                acquired_call=boundary.actor_calls_completed + actor_calls,
            )
            ledger.add(record)
            messages.append({"role": "user", "content": record.exact_content})
            record.message_index = len(messages) - 1
            record.resident = False
            return record

        def run_maintenance(record: ResultRecord, trigger: str) -> None:
            nonlocal maintenance_calls, serialized_tokens, integration
            ordinal = maintenance_calls + 1
            call_root = cell_root / "maintenance" / f"call-{ordinal:03d}-{record.result_id}"
            prior = current_maintenance_prior(
                configuration_id, world, integration, tokenizer, ledger
            )
            allowed = tuple(
                sorted(
                    set(() if prior is None else prior.observed_source_ids)
                    | set(observed_source_ids(record))
                )
            )
            maintenance_messages = integration_messages(
                task_text=(ROOT / "task" / "TASK.md").read_text(encoding="utf-8"),
                prior=prior,
                newly_externalized=record,
                allowed_source_ids=allowed,
            )
            prompt_tokens, rendered = tokenizer.count_messages(maintenance_messages)
            if prompt_tokens + INTEGRATION_PROVIDER_MAX_TOKENS > CONTEXT_TOKENS:
                raise BudgetStop("maintenance_prompt_infeasible")
            admit(prompt_tokens, INTEGRATION_PROVIDER_MAX_TOKENS, "maintenance")
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
                    max_tokens=INTEGRATION_PROVIDER_MAX_TOKENS,
                ),
                call_root / "provider_attempt",
                timeout=max(1, min(900, int(MAX_WALL_SECONDS_PER_CELL - elapsed()))),
            )
            maintenance_calls += 1
            usage = checked_usage(provider, prompt_tokens, INTEGRATION_PROVIDER_MAX_TOKENS)
            serialized_tokens += int(usage["total_tokens"])
            output = provider["content"]
            (call_root / "assistant_content.txt").write_text(
                output, encoding="utf-8", newline=""
            )
            validation = validate_integration(
                output,
                count_text=lambda value: len(tokenizer.tokenize(value)),
                allowed_source_ids=allowed,
            )
            accepted = validation.valid and provider.get("finish_reason") == "stop"
            effect_record: ResultRecord | None = None
            if accepted:
                integration = next_artifact(
                    prior=prior,
                    body=output,
                    body_tokens=validation.output_tokens,
                    result=record,
                )
                execution = world.apply_integration(configuration_id, integration)
                effect_record = append_effect_record(execution)
                refresh_interaction_state()
            else:
                failure_notice = canonical_json_text(
                    {
                        "accepted": False,
                        "configuration_id": configuration_id,
                        "finish_reason": provider.get("finish_reason"),
                        "input_result_id": record.result_id,
                        "output_sha256": sha256_bytes(output.encode("utf-8")),
                        "schema": "artifact-coupled-maintenance-rejection-v0",
                        "validation_code": validation.code,
                    }
                )
                messages.append({"role": "user", "content": failure_notice})
                refresh_interaction_state()
            row = {
                "maintenance_call": maintenance_calls,
                "trigger": trigger,
                "input_result_id": record.result_id,
                "accepted": accepted,
                "allowed_source_ids": list(allowed),
                "effect_result_id": None if effect_record is None else effect_record.result_id,
                "effect_kind": None if effect_record is None else effect_record.result_kind,
                "candidate_sha256_after": world.candidate_sha256,
                "integration_version_after": None if integration is None else integration.version,
                "validation": validation.__dict__,
                "finish_reason": provider.get("finish_reason"),
                "usage": usage,
            }
            maintenance_trace.append(row)
            lifecycle.append({"event": "integration_maintenance", **row})
            write_json(call_root / "RESULT.json", row)

        def mark_delivered(logical_call: int) -> list[str]:
            delivered: list[str] = []
            for record in ledger.records():
                if record.first_model_visible_call is not None or record.message_index is None:
                    continue
                if not 0 <= record.message_index < len(messages):
                    raise RuntimeError(f"pending message index invalid: {record.result_id}")
                if messages[record.message_index] != {
                    "role": "user",
                    "content": record.exact_content,
                }:
                    raise RuntimeError(f"pending message binding invalid: {record.result_id}")
                ledger.mark_model_visible(
                    record.result_id,
                    call_index=logical_call,
                    message_index=record.message_index,
                )
                delivered.append(record.result_id)
            return delivered

        def reenter(trigger: str) -> None:
            nonlocal messages, interaction_state_index, reentries
            if reentries >= MAX_REENTRIES_PER_CELL:
                raise BudgetStop("reactive_reentry_budget_exhausted")
            # Full exact chronology remains in custody. Reentry carries the
            # current exact task world, the current bounded integration in its
            # actual arm-specific location, an exact address directory, and
            # every still-undelivered update. It adds no new source evidence.
            for record in ledger.records():
                if record.previously_visible:
                    ledger.mark_external(record.result_id)
            undelivered = [
                record for record in ledger.records() if not record.previously_visible
            ]
            new_messages = [
                {
                    "role": "system",
                    "content": (ROOT / "task" / "SYSTEM.md").read_text(encoding="utf-8"),
                },
                {
                    "role": "user",
                    "content": (ROOT / "task" / "TASK.md").read_text(encoding="utf-8"),
                },
                {
                    "role": "user",
                    "content": (ROOT / "task" / "ACTIONS.md").read_text(encoding="utf-8")
                    + "\n\n# Exact source catalog\n"
                    + world.source_catalog_for_actor(),
                },
                {
                    "role": "user",
                    "content": "# Exact current candidate\n" + world.candidate_packet(),
                },
                current_interaction_state_message(
                    configuration_id=configuration_id,
                    world=world,
                    integration=integration,
                    embed_integration_body=configuration_id == "D0_DETACHED",
                ),
                {"role": "user", "content": exact_history_directory(ledger)},
            ]
            interaction_state_index = 4
            for record in undelivered:
                new_messages.append({"role": "user", "content": record.exact_content})
                record.message_index = len(new_messages) - 1
                record.resident = False
            if latest_rejection is not None:
                new_messages.append({"role": "user", "content": latest_rejection})
            prompt_tokens = count_messages(tokenizer, new_messages)
            if prompt_tokens > PROMPT_LIMIT:
                raise BudgetStop("reactive_reentry_infeasible")
            messages = new_messages
            reentries += 1
            lifecycle.append(
                {
                    "event": "reactive_exact_reentry",
                    "ordinal": reentries,
                    "trigger": trigger,
                    "prompt_tokens": prompt_tokens,
                    "undelivered_result_ids": [record.result_id for record in undelivered],
                }
            )

        def stabilize(trigger: str) -> None:
            while True:
                before = count_messages(tokenizer, messages)
                if before <= PROMPT_LIMIT:
                    return
                protected = tuple(
                    record.result_id
                    for record in ledger.records()
                    if record.first_model_visible_call is None
                )
                relief = positive_savings_first_fit_step(
                    messages=messages,
                    ledger=ledger,
                    prompt_limit=PROMPT_LIMIT,
                    count_messages=lambda value: count_messages(tokenizer, value),
                    protected_result_ids=protected,
                )
                lifecycle.append(
                    {
                        "event": "pressure_relief_pass",
                        "trigger": trigger,
                        "before_tokens": before,
                        "after_tokens": relief.prompt_tokens,
                        "feasible_before_maintenance": relief.feasible,
                        "selected_result_ids": list(relief.selected_result_ids),
                        "candidate_audits": [audit.__dict__ for audit in relief.audits],
                    }
                )
                if not relief.selected_result_ids:
                    reenter("positive_relief_exhausted")
                    continue
                for result_id in relief.selected_result_ids:
                    run_maintenance(ledger.get(result_id), "positive_savings_externalization")

        def finalize(terminal: str) -> dict[str, Any]:
            mechanical = external_evaluation(world, cell_root)
            write_json(cell_root / "RESULT_LEDGER.json", ledger.as_dict(include_exact_content=True))
            write_json(cell_root / "FINAL_MESSAGES.json", messages)
            write_json(cell_root / "CALL_TRACE.json", trace)
            write_json(cell_root / "MAINTENANCE_TRACE.json", maintenance_trace)
            write_json(cell_root / "LIFECYCLE_EVENTS.json", lifecycle)
            if integration is not None:
                write_json(
                    cell_root / "FINAL_INTEGRATION_STATE.json",
                    {
                        "version": integration.version,
                        "body": integration.body,
                        "body_sha256": integration.body_sha256,
                        "body_tokens": integration.body_tokens,
                        "input_result_ids": list(integration.input_result_ids),
                        "observed_source_ids": list(integration.observed_source_ids),
                    },
                )
            action_counts: dict[str, int] = {}
            for row in trace:
                action = (row.get("parsed_action") or {}).get("action")
                key = "rejected" if action is None else str(action)
                action_counts[key] = action_counts.get(key, 0) + 1
            value = {
                "schema": "artifact-coupled-interaction-cell-result-v0",
                "configuration_id": configuration_id,
                "freeze_commit": git_commit(),
                "actor_calls": actor_calls,
                "maintenance_calls": maintenance_calls,
                "provider_calls": actor_calls + maintenance_calls,
                "serialized_tokens": serialized_tokens,
                "wall_seconds": elapsed(),
                "terminal_disposition": terminal,
                "candidate_sha256": world.candidate_sha256,
                "candidate_changed": world.candidate_sha256 != boundary.candidate_sha256,
                "candidate_submitted": world.submitted,
                "accepted_integration_updates": sum(row["accepted"] for row in maintenance_trace),
                "candidate_effect_count": sum(
                    record.result_kind == "candidate_effect" for record in ledger.records()
                ),
                "candidate_effects_delivered": sum(
                    record.result_kind == "candidate_effect" and record.previously_visible
                    for record in ledger.records()
                ),
                "check_count": sum(
                    record.result_kind == "check_observation" for record in ledger.records()
                ),
                "exact_reopen_count": sum(
                    record.result_kind == "exact_reopen_observation"
                    for record in ledger.records()
                ),
                "externalization_count": sum(
                    event["event"] == "pressure_relief_pass"
                    and bool(event["selected_result_ids"])
                    for event in lifecycle
                ),
                "reactive_reentry_count": reentries,
                "action_counts": action_counts,
                "final_prompt_tokens": count_messages(tokenizer, messages),
                "mechanical_final_evaluation": mechanical,
                "independent_readiness": "pending_condition_blinded_adjudication",
                "useful_completion": "not_adjudicated",
            }
            write_json(cell_root / "CELL_RESULT.json", value)
            return value

        stabilize("inherited_authentic_result_delivery_pressure")
        write_json(
            cell_root / "INITIAL_CONTINUATION_STATE.json",
            {
                "configuration_id": configuration_id,
                "prompt_tokens": count_messages(tokenizer, messages),
                "pending_result_ids": [
                    record.result_id
                    for record in ledger.records()
                    if record.first_model_visible_call is None
                ],
                "resident_result_ids": [
                    record.result_id for record in ledger.records() if record.resident
                ],
                "external_result_ids": [
                    record.result_id
                    for record in ledger.records()
                    if record.previously_visible and not record.resident
                ],
                "maintenance_calls_before_first_actor": maintenance_calls,
                "candidate_sha256": world.candidate_sha256,
            },
        )

        terminal = "actor_call_budget_exhausted"
        while actor_calls < MAX_ACTOR_CALLS_PER_CELL:
            prompt_tokens, rendered = tokenizer.count_messages(messages)
            if prompt_tokens > PROMPT_LIMIT:
                raise RuntimeError("unstabilized actor prompt")
            admit(prompt_tokens, ACTOR_MAX_TOKENS, "actor")
            call_number = actor_calls + 1
            logical_call = boundary.actor_calls_completed + call_number
            call_root = cell_root / "actor" / f"call-{call_number:03d}"
            write_json(call_root / "messages.json", messages)
            (call_root / "rendered_prompt.txt").parent.mkdir(parents=True, exist_ok=True)
            (call_root / "rendered_prompt.txt").write_text(
                rendered, encoding="utf-8", newline=""
            )
            reopen = tuple(
                record.result_id
                for record in ledger.records()
                if record.previously_visible and not record.resident
            )
            schema = action_json_schema(
                ordinary_actions(), source_ids=world.sources, reopen_result_ids=reopen
            )
            provider = complete_custodied(
                provider_payload(
                    messages, ACTOR_SEED, schema, max_tokens=ACTOR_MAX_TOKENS
                ),
                call_root / "provider_attempt",
                timeout=max(1, min(900, int(MAX_WALL_SECONDS_PER_CELL - elapsed()))),
            )
            actor_calls += 1
            usage = checked_usage(provider, prompt_tokens, ACTOR_MAX_TOKENS)
            serialized_tokens += int(usage["total_tokens"])
            output = provider["content"]
            (call_root / "assistant_content.txt").write_text(
                output, encoding="utf-8", newline=""
            )
            delivered = mark_delivered(logical_call)
            messages.append({"role": "assistant", "content": output})
            parsed: dict[str, Any] | None = None
            rejection: str | None = None
            result_record: ResultRecord | None = None
            before_candidate = world.candidate_sha256
            try:
                parsed = parse_action(output, ordinary_actions())
                result_id = f"RESULT-{next_result:03d}"
                next_result += 1
                execution = world.execute(parsed, result_id=result_id, ledger=ledger)
                result_record = world.make_result_record(
                    execution, result_id=result_id, acquired_call=logical_call
                )
                projection = result_record.metadata.get("check_projection")
                if result_record.result_kind == "check_observation" and (
                    not isinstance(projection, dict)
                    or projection.get("protocol_error_class") is not None
                ):
                    write_json(
                        call_root / "RESULT_RECORD.json",
                        result_record.as_dict(include_exact_content=True),
                    )
                    raise RuntimeError("actor-visible evaluator protocol failure")
                result_tokens = len(tokenizer.tokenize(result_record.exact_content))
                if parsed["action"] == "read_batch" and result_tokens > MAX_BATCH_RESULT_TOKENS:
                    write_json(
                        cell_root / "oversized_batch_results" / f"{result_id}.json",
                        {
                            "result": result_record.as_dict(include_exact_content=True),
                            "wrapped_result_tokens": result_tokens,
                            "limit": MAX_BATCH_RESULT_TOKENS,
                            "model_visible": False,
                        },
                    )
                    rejection = "batch_result_too_large"
                    pending_text = render_action_rejection(
                        call_index=logical_call,
                        code=rejection,
                        message=(
                            f"exact batch wrapper contains {result_tokens} tokens; maximum is "
                            f"{MAX_BATCH_RESULT_TOKENS}; result remains audit-only"
                        ),
                        candidate_sha256=world.candidate_sha256,
                    )
                    result_record = None
                else:
                    ledger.add(result_record)
                    pending_text = result_record.exact_content
            except json.JSONDecodeError as exc:
                rejection = "invalid_json"
                pending_text = render_action_rejection(
                    call_index=logical_call,
                    code=rejection,
                    message=str(exc),
                    candidate_sha256=world.candidate_sha256,
                )
            except ActionRejected as exc:
                rejection = exc.code
                pending_text = render_action_rejection(
                    call_index=logical_call,
                    code=exc.code,
                    message=exc.message,
                    candidate_sha256=world.candidate_sha256,
                )
            except ValueError as exc:
                rejection = "invalid_action"
                pending_text = render_action_rejection(
                    call_index=logical_call,
                    code=rejection,
                    message=str(exc),
                    candidate_sha256=world.candidate_sha256,
                )
            messages.append({"role": "user", "content": pending_text})
            latest_rejection = pending_text if result_record is None else None
            if result_record is not None:
                result_record.message_index = len(messages) - 1
                result_record.resident = False
                write_json(
                    call_root / "RESULT_RECORD.json",
                    result_record.as_dict(include_exact_content=True),
                )
            if world.candidate_sha256 != before_candidate or (
                result_record is not None and result_record.result_kind == "check_observation"
            ):
                refresh_interaction_state()
            row = {
                "actor_call": actor_calls,
                "logical_call": logical_call,
                "prompt_tokens": prompt_tokens,
                "usage": usage,
                "finish_reason": provider.get("finish_reason"),
                "output_sha256": sha256_bytes(output.encode("utf-8")),
                "delivered_result_ids": delivered,
                "parsed_action": parsed,
                "rejection_code": rejection,
                "result_id": None if result_record is None else result_record.result_id,
                "result_kind": None if result_record is None else result_record.result_kind,
                "candidate_sha256_before": before_candidate,
                "candidate_sha256_after": world.candidate_sha256,
            }
            trace.append(row)
            write_json(call_root / "RESULT.json", row)
            if (
                parsed is not None
                and parsed.get("action") == "submit"
                and result_record is not None
            ):
                terminal = "submitted"
                break
            if actor_calls < MAX_ACTOR_CALLS_PER_CELL:
                stabilize("post_actor_result_delivery")
        else:
            terminal = "actor_call_budget_exhausted"
        result = finalize(terminal)
    except BudgetStop as exc:
        write_json(
            cell_root / "BUDGET_STOP.json",
            {"type": "BudgetStop", "terminal_disposition": exc.disposition},
        )
        try:
            result = finalize(exc.disposition)
        except BaseException as finalize_exc:
            failure = {
                "type": type(finalize_exc).__name__,
                "message": str(finalize_exc),
                "traceback": traceback.format_exc(),
                "while_finalizing_budget_stop": exc.disposition,
                "no_retry": True,
            }
            write_json(cell_root / "RUN_FAILURE.json", failure)
    except BaseException as exc:
        failure = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "no_retry": True,
        }
        write_json(cell_root / "RUN_FAILURE.json", failure)
    finally:
        if process is not None:
            try:
                release = stop_server(process, stdout, stderr, cell_root / "model")
                if release.get("released") is not True and failure is None:
                    failure = {"type": "RuntimeReleaseFailure", "release": release}
                    write_json(cell_root / "RUN_FAILURE.json", failure)
            except BaseException as exc:
                failure = {
                    "type": "RuntimeReleaseException",
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                }
                write_json(cell_root / "RUN_FAILURE.json", failure)
        write_json(
            cell_root / "CELL_FINALIZATION.json",
            {"release": release, "failure": failure, "result_present": result is not None},
        )
        seal_tree(cell_root, cell_root / "RUN_SEAL.json")
    if failure is not None:
        raise RuntimeError(f"cell failed: {failure}")
    if result is None:
        raise RuntimeError("cell completed without result")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization-receipt", required=True, type=Path)
    args = parser.parse_args()
    require_clean_tree()
    verify_task_lock()
    pressure = verify_pressure_handoff(ROOT)
    authorization = validate_authorization(args.authorization_receipt)
    assets = verify_runtime_assets()
    if assets.get("passed") is not True:
        raise RuntimeError(f"runtime assets failed: {assets.get('failures')}")
    run_root = ROOT / "runs" / RUN_ID
    if run_root.exists():
        raise FileExistsError(run_root)
    run_root.mkdir(parents=True)
    write_json(run_root / "AUTHORIZATION_RECEIPT.json", authorization)
    write_json(
        run_root / "FREEZE_BINDING.json",
        {
            "schema": "artifact-coupled-interaction-freeze-binding-v0",
            "commit": git_commit(),
            "run_id": RUN_ID,
            "configuration_order": list(CONFIGURATION_ORDER),
            "pressure_handoff": pressure,
            "runtime_assets": assets,
            "task_source_lock_sha256": sha256_file(ROOT / "task" / "TASK_SOURCE_LOCK.json"),
        },
    )
    results: list[dict[str, Any]] = []
    failure: dict[str, Any] | None = None
    try:
        for configuration_id in CONFIGURATION_ORDER:
            results.append(run_cell(configuration_id, run_root))
        aggregate = {
            "schema": "artifact-coupled-interaction-measured-result-v0",
            "run_id": RUN_ID,
            "freeze_commit": git_commit(),
            "configuration_order": list(CONFIGURATION_ORDER),
            "cells": results,
            "actor_calls": sum(int(row["actor_calls"]) for row in results),
            "maintenance_calls": sum(int(row["maintenance_calls"]) for row in results),
            "provider_calls": sum(int(row["provider_calls"]) for row in results),
            "serialized_tokens": sum(int(row["serialized_tokens"]) for row in results),
            "independent_adjudication": "pending",
            "interaction_disposition": "pending_external_evaluation",
        }
        write_json(run_root / "AGGREGATE_RESULT.json", aggregate)
    except BaseException as exc:
        failure = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "completed_configurations": [row["configuration_id"] for row in results],
            "no_retry": True,
        }
        write_json(run_root / "AGGREGATE_FAILURE.json", failure)
    finally:
        write_json(run_root / "AGGREGATE_FINALIZATION.json", {"failure": failure})
        seal_tree(run_root, run_root / "RUN_SEAL.json")
    if failure is not None:
        print(json.dumps(failure, indent=2, sort_keys=True))
        return 1
    print(json.dumps(load(run_root / "AGGREGATE_RESULT.json"), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
