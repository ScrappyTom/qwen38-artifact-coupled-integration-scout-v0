from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.configuration import artifact_centered_actor_actions
from reactive_runtime.keystone_world import KeystoneWorld
from tools import run_solace_pressure_screen as runner


RUN_ID = "2026-08-28-trellis-artifact-centered-pressure-screen-v0"
SCOPE = "trellis_artifact_centered_pressure_screen_v0"
TASK_ID = "trellis-heat-continuity-decision-v0"
SEED = 884_219
MAX_CALLS = 30
MAX_SERIALIZED = 900_000


def configure() -> None:
    runner.RUN_ID = RUN_ID
    runner.SCOPE = SCOPE
    runner.TASK_ID = TASK_ID
    runner.SEED = SEED
    runner.MAX_CALLS = MAX_CALLS
    runner.MAX_SERIALIZED = MAX_SERIALIZED
    runner.TASK = runner.ROOT / "task_trellis"
    runner.CONTRACT = runner.ROOT / "TRELLIS_PRESSURE_SCREEN_CONTRACT.json"
    runner.MODEL_LOCK = runner.ROOT / "TRELLIS_MODEL_PROFILE_LOCK.json"
    runner.MIN_QUALIFYING_SOURCES = 8
    runner.MIN_QUALIFYING_DOMAINS = 8
    runner.SolaceWorld = KeystoneWorld
    runner.anchored_relational_actor_actions = lambda _configuration_id: (
        artifact_centered_actor_actions("A0_MATRIX_AND_DECISION", phase="construction")
    )


def main() -> int:
    configure()
    return runner.main()


if __name__ == "__main__":
    raise SystemExit(main())
