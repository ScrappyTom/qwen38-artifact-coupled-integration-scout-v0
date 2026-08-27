from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.orchard_world import OrchardWorld
from tools import audit_aster_pressure_screen as shared


# Deliberately do not import ``run_orchard_pressure_screen`` here. That frozen
# launcher configures the generic Solace runner by module-level assignment and
# would contaminate later legacy audits in the same Python process. The
# independent auditor needs only these immutable contract constants.
runner = SimpleNamespace(
    RUN_ID="2026-08-27-orchard-phase-lifecycle-pressure-screen-v0",
    SCOPE="orchard_phase_lifecycle_pressure_screen_v0",
    TASK_ID="orchard-biologics-restart-decision-v0",
    SEED=642_901,
    MAX_CALLS=30,
    PROMPT_LIMIT=20_992,
)


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
        "HANDOFF_CLAIM_LIMIT": shared.HANDOFF_CLAIM_LIMIT,
    }
    try:
        shared.runner = runner
        shared.TASK = repository_root.resolve() / "task_orchard"
        shared.AUDIT_NAME = "ORCHARD_PRESSURE_SCREEN_AUDIT.json"
        shared.HANDOFF_NAME = "ORCHARD_PRESSURE_BOUNDARY_HANDOFF.json"
        shared.FREEZE_COMMIT = "444ab65a745f1d5cbadbd30e1ed07c99a88ee173"
        shared.WORLD_CLASS = OrchardWorld
        # The frozen pressure runner intentionally reuses the audited Solace
        # envelope schemas. Orchard identity remains independently bound by
        # task ID, task lock, model lock, run ID, and freeze commit.
        shared.SCHEMA_PREFIX = "solace"
        shared.HANDOFF_SCHEMA_VERSION = "orchard-pressure-boundary-handoff-v0"
        shared.MODEL_LOCK_NAME = "ORCHARD_MODEL_PROFILE_LOCK.json"
        shared.CONTRACT_NAME = "ORCHARD_PRESSURE_SCREEN_CONTRACT.json"
        shared.HANDOFF_CLAIM_LIMIT = (
            "This handoff qualifies one exact common pre-treatment Orchard "
            "pressure fork. It establishes no scaffold, construction, "
            "verification-lifecycle, or F0/P1 utility claim and authorizes no "
            "continuation."
        )
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
