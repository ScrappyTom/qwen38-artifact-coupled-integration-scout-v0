from __future__ import annotations

from reactive_runtime.configuration import phase_lifecycle_actor_actions
from reactive_runtime.orchard_world import OrchardWorld
from tools import run_solace_pressure_screen as runner


runner.RUN_ID = "2026-08-27-orchard-phase-lifecycle-pressure-screen-v0"
runner.SCOPE = "orchard_phase_lifecycle_pressure_screen_v0"
runner.TASK_ID = "orchard-biologics-restart-decision-v0"
runner.SEED = 642_901
runner.MAX_CALLS = 30
runner.MAX_SERIALIZED = 900_000
runner.TASK = runner.ROOT / "task_orchard"
runner.CONTRACT = runner.ROOT / "ORCHARD_PRESSURE_SCREEN_CONTRACT.json"
runner.MODEL_LOCK = runner.ROOT / "ORCHARD_MODEL_PROFILE_LOCK.json"
runner.MIN_QUALIFYING_SOURCES = 10
runner.MIN_QUALIFYING_DOMAINS = 10
runner.SolaceWorld = OrchardWorld
runner.anchored_relational_actor_actions = lambda _configuration_id: phase_lifecycle_actor_actions(
    "F0_FIXED_SCAFFOLD_APPEND_ONLY_VERIFICATION", phase="construction"
)


if __name__ == "__main__":
    raise SystemExit(runner.main())
