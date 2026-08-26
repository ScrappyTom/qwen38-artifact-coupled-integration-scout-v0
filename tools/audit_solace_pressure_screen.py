from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.solace_world import SolaceWorld
from tools import audit_aster_pressure_screen as shared
from tools import run_solace_pressure_screen as runner


def audit(
    repository_root: Path = ROOT, *, write_outputs: bool = True
) -> dict[str, Any]:
    saved = {
        "runner": shared.runner,
        "TASK": shared.TASK,
        "AUDIT_NAME": shared.AUDIT_NAME,
        "HANDOFF_NAME": shared.HANDOFF_NAME,
        "FREEZE_COMMIT": shared.FREEZE_COMMIT,
        "WORLD_CLASS": shared.WORLD_CLASS,
        "SCHEMA_PREFIX": shared.SCHEMA_PREFIX,
        "HANDOFF_SCHEMA_VERSION": shared.HANDOFF_SCHEMA_VERSION,
        "MODEL_LOCK_NAME": shared.MODEL_LOCK_NAME,
        "CONTRACT_NAME": shared.CONTRACT_NAME,
    }
    try:
        shared.runner = runner
        shared.TASK = repository_root.resolve() / "task_solace"
        shared.AUDIT_NAME = "SOLACE_PRESSURE_SCREEN_AUDIT.json"
        shared.HANDOFF_NAME = "SOLACE_PRESSURE_BOUNDARY_HANDOFF.json"
        shared.FREEZE_COMMIT = "5af42ca96182ce16dc5aced20f952da9a7c791e4"
        shared.WORLD_CLASS = SolaceWorld
        shared.SCHEMA_PREFIX = "solace"
        shared.HANDOFF_SCHEMA_VERSION = "solace-pressure-boundary-handoff-v0"
        shared.MODEL_LOCK_NAME = "SOLACE_MODEL_PROFILE_LOCK.json"
        shared.CONTRACT_NAME = "SOLACE_PRESSURE_SCREEN_CONTRACT.json"
        return shared.audit(repository_root, write_outputs=write_outputs)
    finally:
        for name, value in saved.items():
            setattr(shared, name, value)


def main() -> int:
    result = audit()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
