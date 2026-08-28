from __future__ import annotations

# ruff: noqa: E402

import json
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.actions import action_json_schema, parse_action
from reactive_runtime.anchored_provenance import AnchoredProvenanceRegister
from reactive_runtime.canonical import sha256_file, write_json
from reactive_runtime.configuration import causal_verification_actor_actions
from reactive_runtime.keystone_event_fork import (
    CommonForkState,
    branch_binding,
    clone_common_state,
)
from reactive_runtime.keystone_world import KeystoneWorld
from reactive_runtime.records import ResultLedger
from reactive_runtime.verification_causal_lifecycle import verification_frame
from tools.preflight_keystone_event_fork import preflight, trigger_fixture
from tools.run_keystone_event_fork import (
    CONFIGURATION_ORDER,
    MAX_BRANCH_CALLS,
    MAX_COMMON_MODEL_CALLS,
    MAX_NEW_MODEL_CALLS,
    MAX_NEW_SERIALIZED_TOKENS,
    PARENT_RUN,
    RUN_ID,
    SCOPE,
    TASK,
    verify_frozen_inputs,
)


OUTPUT = ROOT / "KEYSTONE_EVENT_FORK_RUNNER_QUALIFICATION.json"


def qualify(*, write_output: bool = True) -> dict[str, Any]:
    failures: list[str] = []
    contract = verify_frozen_inputs()
    preflight_result = preflight(write_outputs=False)
    if preflight_result.get("passed") is not True:
        failures.append("parent_preflight")

    budgets = contract["budgets"]
    observed_budgets = {
        "maximum_common_continuation_calls": MAX_COMMON_MODEL_CALLS,
        "maximum_calls_per_arm": MAX_BRANCH_CALLS,
        "maximum_new_model_calls": MAX_NEW_MODEL_CALLS,
        "maximum_new_serialized_tokens": MAX_NEW_SERIALIZED_TOKENS,
    }
    for key, value in observed_budgets.items():
        if budgets.get(key) != value:
            failures.append(f"budget:{key}")
    runner_sha256 = sha256_file(ROOT / "tools" / "run_keystone_event_fork.py")
    runner_source_bound = (
        contract.get("runner", {}).get("runner_sha256") == runner_sha256
    )
    if not runner_source_bound:
        failures.append("runner_source_binding")

    actions = causal_verification_actor_actions(
        "V1_BOUNDED_CAUSAL_CONTINUITY", phase="verification"
    )
    world: KeystoneWorld | None = None
    clone_equal = False
    clone_independent = False
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        world = KeystoneWorld(
            TASK,
            root / "common",
            candidate_seed_root=PARENT_RUN / "trajectory" / "world" / "candidate",
        )
        repair = {
            "action": "replace_artifact_section",
            "candidate_sha256": "1" * 64,
            "artifact_sha256": "2" * 64,
            "section_heading": world.decision_headings[0],
            "expected_section_sha256": "3" * 64,
            "replacement_section": f"## {world.decision_headings[0]}\n\nExact replacement.\n",
        }
        try:
            parse_action(
                json.dumps(repair), actions, decision_headings=world.decision_headings
            )
            schema = action_json_schema(
                actions,
                source_ids=world.sources,
                reopen_result_ids=(),
                decision_headings=world.decision_headings,
            )
            advertised = {
                row["properties"]["action"]["const"]
                for row in schema["json_schema"]["schema"]["oneOf"]
            }
            if "replace_artifact_section" not in advertised:
                failures.append("bound_repair_not_advertised")
        except ValueError as exc:
            failures.append(f"bound_repair_schema:{type(exc).__name__}")

        initial = world.candidate_sha256
        fixture = trigger_fixture(initial)
        ledger = ResultLedger()
        common = CommonForkState(
            messages=[{"role": "user", "content": "exact pending fixture"}],
            ledger=ledger,
            trace=deepcopy(fixture),
            register=AnchoredProvenanceRegister(),
            phase="construction",
            pending_result_id=None,
            next_result_ordinal=10,
            latest_effect_result_id=None,
            actor_calls_completed=14,
            model_calls_completed=0,
            serialized_tokens=0,
        )
        # The fixture trace describes verification, so the world is advanced only
        # for cloning mechanics; no semantic event is inferred from it.
        world.phase = "construction"
        left = clone_common_state(common, world, root / "left")
        right = clone_common_state(common, world, root / "right")
        clone_equal = branch_binding(left) == common.binding(world) and branch_binding(
            right
        ) == common.binding(world)
        left.messages.append({"role": "user", "content": "left-only"})
        clone_independent = left.messages != right.messages and common.messages == [
            {"role": "user", "content": "exact pending fixture"}
        ]
        if not clone_equal:
            failures.append("branch_binding")
        if not clone_independent:
            failures.append("branch_independence")

        v0 = verification_frame(
            CONFIGURATION_ORDER[0], fixture, history_handle="history://qualification"
        )
        v1 = verification_frame(
            CONFIGURATION_ORDER[1], fixture, history_handle="history://qualification"
        )
        if v0.get("active_rejected_action") is not None:
            failures.append("v0_treatment_leak")
        if (v1.get("active_rejected_action") or {}).get("rejection_code") != (
            "section_version_mismatch"
        ):
            failures.append("v1_treatment_missing")

    authorization = json.loads(
        (ROOT / "KEYSTONE_EVENT_FORK_AUTHORIZATION_REQUEST.json").read_text(
            encoding="utf-8"
        )
    )
    if authorization.get("authorized") is not False:
        failures.append("gpu_authorization_not_closed")
    result = {
        "schema": "keystone-event-fork-runner-provider-free-qualification-v0",
        "passed": not failures,
        "failures": failures,
        "run_id": RUN_ID,
        "scope": SCOPE,
        "runner_path": "tools/run_keystone_event_fork.py",
        "runner_sha256": runner_sha256,
        "runner_source_bound": runner_source_bound,
        "model_calls": 0,
        "provider_calls": 0,
        "gpu_authorized": False,
        "parent_preflight_passed": preflight_result.get("passed") is True,
        "branch_bindings_equal_before_projection": clone_equal,
        "branch_mutable_state_independent": clone_independent,
        "bound_repair_live_schema_closed": "replace_artifact_section" in actions,
        "configuration_order": list(CONFIGURATION_ORDER),
        "budgets": observed_budgets,
        "claim_limits": [
            "provider-free qualification proves runner topology and contracts only",
            "the live actor may never reach the causal trigger",
            "the V1 treatment may not improve repair, recheck, or closure",
            "GPU execution still requires a separate exact external authorization receipt",
        ],
    }
    if write_output:
        write_json(OUTPUT, result)
    return result


def main() -> int:
    result = qualify(write_output=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
