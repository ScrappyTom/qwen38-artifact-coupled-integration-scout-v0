from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json


DONOR = Path("E:/qwen38-ingress-work-interaction-scout-v0")
DONOR_COMMIT = "ea03f6c7e5d11e0f9f1013eef573215767c58ad1"
RUN = DONOR / "runs" / "2026-08-24-ingress-work-interaction-measured-v0" / "cells"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def main() -> int:
    observed = subprocess.check_output(["git", "-C", str(DONOR), "rev-parse", "HEAD"], text=True).strip()
    if observed != DONOR_COMMIT:
        raise RuntimeError("E40 donor checkout is not at its result commit")
    rows = []
    for configuration_id in ("I3", "I4"):
        root = RUN / configuration_id
        cell = load(root / "CELL_RESULT.json")
        state = load(root / "PERSISTENT_STATE.json")
        lifecycle = json.loads((root / "LIFECYCLE_EVENTS.json").read_text(encoding="utf-8"))
        accepted = [event for event in lifecycle if event.get("event") == "work_replacement" and event.get("accepted") is True]
        candidate_path = root / "trajectory" / "world" / "candidate" / "CEIBA_90_DAY_DECISION_CHARTER.md"
        work = state.get("work")
        rows.append({
            "configuration_id": configuration_id,
            "accepted_work_replacements": len(accepted),
            "final_work_body_sha256": None if work is None else work.get("body_sha256"),
            "final_work_body_tokens": None if work is None else work.get("body_tokens"),
            "final_work_source_ids": [] if work is None else work.get("source_ids", []),
            "candidate_sha256": cell["candidate_sha256"],
            "candidate_file_sha256": sha256_file(candidate_path),
            "candidate_changed": cell["candidate_changed"],
            "candidate_effect_count": cell["candidate_effect_count"],
            "candidate_effects_visible": cell["candidate_effects_visible"],
            "check_count": cell["check_count"],
            "submitted": cell["candidate_submitted"],
            "work_was_task_candidate": False,
            "work_was_effect_bound": False,
            "work_was_check_bound": False,
        })
    result = {
        "schema": "e40-work-to-artifact-gap-audit-v0",
        "donor_repository": "ScrappyTom/qwen38-ingress-work-interaction-scout-v0",
        "donor_result_commit": DONOR_COMMIT,
        "passed": all(row["accepted_work_replacements"] > 0 and row["candidate_changed"] is False and row["candidate_effect_count"] == 0 and row["check_count"] == 0 for row in rows),
        "finding": "E40 produced accepted bounded semantic replacement state, but those bytes never became the exact task candidate, never generated a candidate effect, and were never evaluated by an actor-invoked candidate-bound check.",
        "cells": rows,
    }
    write_json(ROOT / "E40_WORK_TO_ARTIFACT_GAP_AUDIT.json", result)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
