from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from reactive_runtime.actions import action_json_schema, parse_action
from reactive_runtime.canonical import canonical_json_text, sha256_file
from reactive_runtime.records import ResultLedger
from reactive_runtime.solace_world import SolaceWorld
from tools.offline_tokenizer import OfflineTokenizer


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "task_solace"
DONOR_CELL = (
    ROOT
    / "runs"
    / "2026-08-26-solace-anchored-provenance-interaction-measured-v0"
    / "cells"
    / "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE"
)
DONOR_CANDIDATE = DONOR_CELL / "trajectory" / "candidate_versions" / "version-008"
DONOR_REGISTER = DONOR_CELL / "CURRENT_REGISTER.json"
DONOR_EFFECT = DONOR_CELL / "actor" / "call-009" / "RESULT_RECORD.json"
DONOR_INITIAL_STATE = DONOR_CELL / "INITIAL_STATE.json"
EVALUATOR_CONFIG = TASK / "EVALUATOR_V1.json"
EVALUATOR_SCRIPT = TASK / "evaluator_v1" / "evaluate.py"
CONFIGURATION_ORDER = (
    "A0_EXACT_ARTIFACT_ONLY",
    "A1_EXACT_ARTIFACT_PLUS_FROZEN_REGISTER",
)
ALLOWED_ACTIONS = (
    "patch_decision",
    "run_check",
    "read_source",
    "read_batch",
    "reopen_exact",
    "submit",
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def donor_register_text() -> str:
    value = load(DONOR_REGISTER)
    claims = value.get("claims")
    rendered = value.get("rendered")
    if not isinstance(claims, list) or len(claims) != 20 or not isinstance(rendered, str):
        raise ValueError("frozen donor register is not the expected 20-claim state")
    return rendered


def donor_effect_text() -> str:
    value = load(DONOR_EFFECT)
    if value.get("result_id") != "RESULT-015" or value.get("first_model_visible_call") is not None:
        raise ValueError("frozen donor effect binding changed")
    return str(value["exact_content"])


def create_world(cell_root: Path) -> SolaceWorld:
    return SolaceWorld(
        TASK,
        cell_root,
        candidate_seed_root=DONOR_CANDIDATE,
        candidate_seed_version_index=8,
        evaluator_config_path=EVALUATOR_CONFIG,
        evaluator_script_path=EVALUATOR_SCRIPT,
    )


def donor_ledger() -> ResultLedger:
    ledger = ResultLedger.from_dict(load(DONOR_INITIAL_STATE)["result_ledger"])
    for record in ledger.records():
        if record.previously_visible:
            ledger.mark_external(record.result_id)
    return ledger


def external_result_ids() -> tuple[str, ...]:
    ledger = donor_ledger()
    return tuple(
        record.result_id
        for record in ledger.records()
        if record.previously_visible and not record.resident
    )


def current_state_message(world: SolaceWorld) -> str:
    return "\n".join(
        (
            "# Fresh exact verification frame",
            "This is chronology-free reentry after construction. It does not assert readiness.",
            canonical_json_text(
                {
                    "current_candidate_sha256": world.candidate_sha256,
                    "current_candidate_version": world.candidate_version,
                    "latest_effect_result_id": "RESULT-015",
                    "latest_effect_delivery": "visible_in_this_frame",
                    "latest_check": None,
                    "current_candidate_verification_status": "not_run_after_candidate_effect",
                    "full_history_handle": "run://2026-08-26-solace-anchored-provenance-interaction-measured-v0/cells/L1_FAULT_TOLERANT_ANCHORED_PROVENANCE",
                    "semantic_readiness": "not_adjudicated",
                    "schema": "solace-verification-current-state-v0",
                }
            ),
            "--- exact latest admitted effect ---",
            donor_effect_text(),
        )
    )


def verification_messages(configuration_id: str, world: SolaceWorld) -> list[dict[str, str]]:
    if configuration_id not in CONFIGURATION_ORDER:
        raise ValueError(configuration_id)
    messages = [
        {"role": "system", "content": (TASK / "SYSTEM.md").read_text(encoding="utf-8")},
        {"role": "user", "content": (TASK / "TASK.md").read_text(encoding="utf-8")},
        {"role": "user", "content": (TASK / "VERIFICATION_ACTIONS.md").read_text(encoding="utf-8")},
        {"role": "user", "content": world.source_catalog_for_actor()},
        {"role": "user", "content": world.candidate_packet()},
        {"role": "user", "content": current_state_message(world)},
    ]
    if configuration_id == "A1_EXACT_ARTIFACT_PLUS_FROZEN_REGISTER":
        messages.append({"role": "user", "content": donor_register_text()})
    return messages


def repair_patch_action() -> dict[str, Any]:
    return {
        "action": "patch_decision",
        "edits": [
            {
                "old": "The north-zone distribution system currently holds a minimum pressure of 42 psi [BASTION].",
                "new": "The north-zone distribution system currently holds a minimum pressure of 42 psi [BASTION]. Restoration requires at least 35 psi at every critical node for three consecutive 30-minute windows [BASTION].",
            },
            {
                "old": "Clearance requires two complete sampling rounds spaced at least sixteen hours apart; one clean round is insufficient [CIPHER].",
                "new": "Clearance requires two complete sampling rounds spaced at least sixteen hours apart; each complete round contains 48 samples, and one clean round is insufficient [CIPHER].",
            },
            {
                "old": "The shared-main limit under staged demand requires that DELTA pump capacity not exceed the 6.5 MW usable grid feed plus any available generator margin without triggering cavitation constraints [DELTA, ECHO, BASTION].",
                "new": "The shared-main limit under staged demand requires that DELTA pump capacity not exceed the 6.5 MW usable grid feed plus any available generator margin without triggering cavitation constraints [DELTA, ECHO, BASTION]. DELTA reports a nominal station capacity of 18 MGD, a 14.5 MGD shared-main ceiling, and a current inspected capacity of 12.8 MGD. Demand may advance through 10, 30, 60, and 100 percent stages only after two consecutive 30-minute windows meet pressure, turbidity, power, and storage gates [DELTA].",
            },
            {
                "old": "Critical-signal telemetry coverage stands at 96 percent, with 4 percent of monitored points unobserved; this coverage gap does not prove the uninstrumented zones are healthy, only that they are not currently observable [INDIGO].",
                "new": "Critical-signal telemetry coverage stands at 96 percent, with 4 percent of monitored points unobserved; this coverage gap does not prove the uninstrumented zones are healthy, only that they are not currently observable [INDIGO]. The primary observation path must remain at or below 700 milliseconds p95 and 1,200 milliseconds p99 [INDIGO].",
            },
            {"old": "## Treatment barriers, turbidity, disinfectant, and source blend", "new": "### Treatment barriers, turbidity, disinfectant, and source blend"},
            {"old": "## Contamination hypotheses, investigation holds, and falsifiers", "new": "### Contamination hypotheses, investigation holds, and falsifiers"},
            {"old": "## Access, control-system integrity, and evidence custody", "new": "## Security, telemetry, and evidence custody"},
            {"old": "## Telemetry coverage, alerts, delays, and uncertainty", "new": "### Telemetry coverage, alerts, delays, and uncertainty"},
            {"old": "## Environmental determination, notice clock, permits, and discharge", "new": "## Public health, environmental, and communication continuity"},
            {"old": "## Public advisories, accessibility, alternate water, and communications", "new": "### Public advisories, accessibility, alternate water, and communications"},
            {
                "old": "## Candidate lineage, rollback, effect uptake, checks, blockers, and closure",
                "new": "## Execution, rollback, and contingencies\n\nExecute restoration in bounded stages only after the applicable hydraulic, laboratory, power, treatment, security, and communication gates are current. Roll back an affected stage when a governing source version or validation result changes; preserve candidate lineage and rerun the candidate-bound check before closure [AURORA, BASTION, CIPHER, DELTA, ECHO, FALCON, HELIX, LUMEN, MOSAIC, NEXUS].\n\n## Verification, blockers, falsifiers, and closure",
            },
        ],
    }


def provider_free_lifecycle(configuration_id: str, root: Path) -> dict[str, Any]:
    world = create_world(root)
    ledger = donor_ledger()
    initial_hash = world.candidate_sha256
    initial = world.execute({"action": "run_check"}, result_id="PREFLIGHT-CHECK-INITIAL", ledger=ledger)
    initial_projection = initial.metadata["check_projection"]
    patch = repair_patch_action()
    parsed = parse_action(json.dumps(patch), ALLOWED_ACTIONS, decision_headings=world.decision_headings)
    effect = world.execute(parsed, result_id="PREFLIGHT-PATCH", ledger=ledger)
    stale = world.current_check_binding()
    repaired = world.execute({"action": "run_check"}, result_id="PREFLIGHT-CHECK-REPAIRED", ledger=ledger)
    repaired_projection = repaired.metadata["check_projection"]
    submission = world.execute({"action": "submit"}, result_id="PREFLIGHT-SUBMIT", ledger=ledger)
    return {
        "configuration_id": configuration_id,
        "initial_candidate_sha256": initial_hash,
        "initial_blocking_requirements": initial_projection["blocking_requirements"],
        "initial_check_passed": initial_projection["passed"],
        "patch_result_kind": effect.result_kind,
        "patched_candidate_sha256": world.candidate_sha256,
        "prior_check_stale_after_patch": bool(stale and stale.get("currency") == "stale"),
        "recheck_passed": repaired_projection["passed"],
        "recheck_blocking_requirements": repaired_projection["blocking_requirements"],
        "submitted": world.submitted,
        "submission_result_kind": submission.result_kind,
        "final_check_currency": world.current_check_binding(),
    }


def build_stage0() -> dict[str, Any]:
    tokenizer = OfflineTokenizer()
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        geometries: dict[str, Any] = {}
        fixtures: list[dict[str, Any]] = []
        for configuration_id in CONFIGURATION_ORDER:
            world = create_world(temporary_root / f"geometry-{configuration_id}")
            messages = verification_messages(configuration_id, world)
            prompt_tokens = tokenizer.count_messages(messages)
            schema = action_json_schema(
                ALLOWED_ACTIONS,
                source_ids=world.sources,
                reopen_result_ids=external_result_ids(),
                decision_headings=world.decision_headings,
                schema_name=f"solace_{configuration_id.casefold()}_verification_action_v0",
            )
            geometries[configuration_id] = {
                "prompt_tokens": prompt_tokens,
                "candidate_sha256": world.candidate_sha256,
                "candidate_version": world.candidate_version,
                "register_present": configuration_id.startswith("A1_"),
                "action_schema_one_of": len(schema["json_schema"]["schema"]["oneOf"]),
            }
            fixtures.append(provider_free_lifecycle(configuration_id, temporary_root / f"fixture-{configuration_id}"))
    return {
        "schema": "solace-verification-lifecycle-stage0-v0",
        "provider_calls": 0,
        "configuration_order": list(CONFIGURATION_ORDER),
        "donor": {
            "candidate_sha256": "82d14bff607d8e323899d09b72739ee4bf14bc067013c6675365b580093ecf5a",
            "candidate_version": "candidate-v008:82d14bff607d8e323899d09b72739ee4bf14bc067013c6675365b580093ecf5a",
            "register_sha256": load(DONOR_REGISTER)["sha256"],
            "register_claims": len(load(DONOR_REGISTER)["claims"]),
            "effect_result_id": load(DONOR_EFFECT)["result_id"],
            "candidate_manifest_sha256": sha256_file(DONOR_CANDIDATE / "CANDIDATE_MANIFEST.json"),
        },
        "geometry": geometries,
        "provider_free_lifecycles": fixtures,
        "claim_limit": "Provider-free qualification of exact donor reentry, evaluator-v1 defect coverage, bounded exact patch transport, check currentness, recheck, and submission mechanics. It provides no model behavior or A0/A1 utility evidence.",
    }
