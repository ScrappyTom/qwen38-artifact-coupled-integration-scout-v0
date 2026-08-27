from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import write_json  # noqa: E402
from reactive_runtime.verification_causal_frame import (  # noqa: E402
    apply_bound_section_replacement,
    build_verification_causal_frame,
    section_spans,
    sha256_text,
)
from task_orchard.evaluator.evaluate import evaluate  # noqa: E402
from tools.offline_tokenizer import OfflineTokenizer  # noqa: E402


CELL_ROOT = (
    ROOT
    / "runs"
    / "2026-08-27-orchard-phase-lifecycle-measured-v0"
    / "cells"
    / "P1_PHASE_CONDITIONAL_CURRENT_VERIFICATION"
)
OUTPUT = ROOT / "VERIFICATION_CAUSAL_CONTRACT_PREFLIGHT.json"
DECISION = "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
TARGET_HEADING = "Utilities, materials, staffing, and staged restart"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []
    tokenizer = OfflineTokenizer()
    source_root = CELL_ROOT / "trajectory" / "world" / "candidate"
    trace = load(CELL_ROOT / "ACTOR_TRACE.json")
    original_evaluation = evaluate(source_root)
    document = (source_root / DECISION).read_text(encoding="utf-8")
    sections = {row["heading"]: row for row in section_spans(document)}
    target = sections[TARGET_HEADING]
    addition = (
        "\nThe repair transaction itself is candidate-bound, artifact-bound, and "
        "section-bound; its admission is an exact custody event rather than evidence "
        "of restart readiness [CHANGE].\n"
    )
    replacement = target["text"].rstrip() + addition
    action = {
        "action": "replace_artifact_section",
        "candidate_sha256": original_evaluation["candidate_sha256"],
        "artifact_sha256": sha256_text(document),
        "section_heading": TARGET_HEADING,
        "expected_section_sha256": target["sha256"],
        "replacement_section": replacement,
    }
    action_tokens = tokenizer.count_text(json.dumps(action, ensure_ascii=False, sort_keys=True))
    updated, receipt = apply_bound_section_replacement(
        document,
        action,
        current_candidate_sha256=original_evaluation["candidate_sha256"],
    )
    if receipt.get("status") != "admitted":
        failures.append(f"valid repair rejected:{receipt}")

    stale_action = dict(action)
    stale_action["candidate_sha256"] = "0" * 64
    stale_document, stale_receipt = apply_bound_section_replacement(
        document,
        stale_action,
        current_candidate_sha256=original_evaluation["candidate_sha256"],
    )
    if stale_document != document or stale_receipt.get("code") != "candidate_version_mismatch":
        failures.append("stale candidate binding did not reject without mutation")

    wrong_section_action = dict(action)
    wrong_section_action["expected_section_sha256"] = "f" * 64
    wrong_document, wrong_receipt = apply_bound_section_replacement(
        document,
        wrong_section_action,
        current_candidate_sha256=original_evaluation["candidate_sha256"],
    )
    if wrong_document != document or wrong_receipt.get("code") != "section_version_mismatch":
        failures.append("stale section binding did not reject without mutation")

    with TemporaryDirectory(prefix="verification-causal-contract-") as temporary:
        candidate_root = Path(temporary) / "candidate"
        shutil.copytree(source_root, candidate_root)
        (candidate_root / DECISION).write_text(updated, encoding="utf-8")
        updated_evaluation = evaluate(candidate_root)

    synthetic = list(trace)
    synthetic.append(
        {
            "actor_call": 25,
            "parsed_action": action,
            "candidate_sha256_before": original_evaluation["candidate_sha256"],
            "candidate_sha256_after": updated_evaluation["candidate_sha256"],
            "rejection_code": None,
            "result_id": "PREFLIGHT-EFFECT",
            "result_kind": "candidate_effect",
            "current_check_binding": trace[-1].get("current_check_binding"),
        }
    )
    synthetic.append(
        {
            "actor_call": 26,
            "parsed_action": {"action": "run_check"},
            "candidate_sha256_before": updated_evaluation["candidate_sha256"],
            "candidate_sha256_after": updated_evaluation["candidate_sha256"],
            "rejection_code": None,
            "result_id": "PREFLIGHT-CHECK",
            "result_kind": "check_observation",
            "current_check_binding": {
                "evaluator_id": "orchard-biologics-evaluator-v0",
                "evaluated_candidate_sha256": updated_evaluation["candidate_sha256"],
                "current_candidate_sha256": updated_evaluation["candidate_sha256"],
                "passed": updated_evaluation["passed"],
                "closure_readiness": updated_evaluation["closure_readiness"],
                "criterion_results": updated_evaluation["criterion_results"],
                "blocking_requirements": updated_evaluation["blocking_requirements"],
                "raw_result_handle": "raw-tool://PREFLIGHT-CHECK/evaluator",
            },
        }
    )
    initial_frame = build_verification_causal_frame(
        trace, history_handle="history://E76_ORCHARD_P1"
    )
    repaired_frame = build_verification_causal_frame(
        synthetic, history_handle="history://provider-free-preflight"
    )
    initial_frame_tokens = tokenizer.count_text(
        json.dumps(initial_frame, ensure_ascii=False, sort_keys=True, indent=2)
    )
    repaired_frame_tokens = tokenizer.count_text(
        json.dumps(repaired_frame, ensure_ascii=False, sort_keys=True, indent=2)
    )
    if (initial_frame.get("active_rejected_action") or {}).get("rejection_code") != "patch_anchor_not_unique":
        failures.append("initial frame lost active Orchard rejection")
    if (initial_frame.get("recurrence") or {}).get("count_in_current_candidate_epoch") != 4:
        failures.append("initial frame lost Orchard recurrence")
    if repaired_frame.get("active_rejected_action") is not None:
        failures.append("admitted candidate effect did not clear prior rejection epoch")
    if (repaired_frame.get("current_check") or {}).get("mechanical_currency") != "current":
        failures.append("provider-free recheck is not current")
    if max(initial_frame_tokens, repaired_frame_tokens) > 1400:
        failures.append("bounded frame exceeds 1400 tokens")
    if action_tokens > 1200:
        failures.append("bound repair action exceeds 1200 tokens")

    output = {
        "schema": "verification-causal-contract-preflight-v0",
        "date": "2026-08-27",
        "passed": not failures,
        "failures": failures,
        "new_model_calls": 0,
        "donor": {
            "run_id": "2026-08-27-orchard-phase-lifecycle-measured-v0",
            "configuration_id": "P1_PHASE_CONDITIONAL_CURRENT_VERIFICATION",
            "candidate_sha256": original_evaluation["candidate_sha256"],
        },
        "mechanical_frame": {
            "initial_tokens": initial_frame_tokens,
            "after_repair_recheck_tokens": repaired_frame_tokens,
            "token_ceiling": 1400,
            "initial_active_rejection": initial_frame["active_rejected_action"],
            "initial_recurrence": initial_frame["recurrence"],
            "after_repair_active_rejection": repaired_frame["active_rejected_action"],
            "after_repair_check_currency": repaired_frame["current_check"]["mechanical_currency"],
        },
        "repair_transport": {
            "action_tokens": action_tokens,
            "token_ceiling": 1200,
            "valid_receipt": receipt,
            "stale_candidate_rejection": stale_receipt,
            "stale_section_rejection": wrong_receipt,
            "updated_candidate_sha256": updated_evaluation["candidate_sha256"],
            "updated_check_passed": updated_evaluation["passed"],
            "updated_closure_readiness": updated_evaluation["closure_readiness"],
        },
        "claim_limits": [
            "provider-free reachability only",
            "no evidence that the actor uses the frame",
            "no evidence that the frame prevents recurrence",
            "no readiness or closure benefit established",
            "Orchard remains closed to rerun and tuning",
        ],
    }
    write_json(OUTPUT, output)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
