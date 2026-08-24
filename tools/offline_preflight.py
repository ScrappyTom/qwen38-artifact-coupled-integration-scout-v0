from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.actions import DECISION_HEADINGS
from reactive_runtime.canonical import sha256_file, write_json
from reactive_runtime.configuration import CONFIGURATIONS, ordinary_actions
from reactive_runtime.integration import INTEGRATION_PROVIDER_MAX_TOKENS, INTEGRATION_TOKEN_BUDGET
from reactive_runtime.world import ArchitectureWorld


def main() -> int:
    lock = json.loads((ROOT / "task" / "TASK_SOURCE_LOCK.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    for row in lock["files"]:
        path = ROOT / "task" / row["path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            failures.append(f"task_lock_mismatch:{row['path']}")
    for receipt_name in ("E40_WORK_TO_ARTIFACT_GAP_AUDIT.json", "STAGE0_INTERACTION_FIXTURE.json"):
        receipt = json.loads((ROOT / receipt_name).read_text(encoding="utf-8"))
        if receipt.get("passed") is not True:
            failures.append(f"receipt_not_passing:{receipt_name}")
    with tempfile.TemporaryDirectory() as temporary:
        world = ArchitectureWorld(ROOT / "task", Path(temporary))
        if len(world.sources) != 14:
            failures.append("source_count")
        if set(CONFIGURATIONS) != {"D0_DETACHED", "A1_COUPLED"}:
            failures.append("configuration_identity")
        if "upsert_decision_section" not in ordinary_actions():
            failures.append("incremental_action_missing")
    result = {
        "schema": "artifact-coupled-stage0-preflight-v0",
        "passed": not failures,
        "failures": failures,
        "configuration_ids": list(CONFIGURATIONS),
        "source_count": len(lock["source_custody"]),
        "source_bytes": sum(row["size_bytes"] for row in lock["source_custody"]),
        "decision_headings": list(DECISION_HEADINGS),
        "integration_body_budget": INTEGRATION_TOKEN_BUDGET,
        "integration_provider_max_tokens": INTEGRATION_PROVIDER_MAX_TOKENS,
        "gpu_authorized": False,
        "offline_apparatus_qualified": not failures,
        "live_expression_qualified": False,
        "authentic_pressure_qualified": False,
        "measured_interaction_eligible": False,
        "next_live_gate": "four-call maintenance and new-action expression qualification",
    }
    write_json(ROOT / "STAGE0_PREFLIGHT.json", result)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
