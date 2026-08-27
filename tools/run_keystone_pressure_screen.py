from __future__ import annotations

from reactive_runtime.configuration import phase_lifecycle_actor_actions
from reactive_runtime.keystone_world import KeystoneWorld
from tools import run_solace_pressure_screen as runner


RUN_ID = "2026-08-27-keystone-bounded-causal-pressure-screen-v0"
SCOPE = "keystone_bounded_causal_pressure_screen_v0"
TASK_ID = "keystone-rail-restoration-decision-v0"
SEED = 743_211
MAX_CALLS = 30
MAX_SERIALIZED = 900_000


def configure() -> None:
    """Configure the shared runner only at execution time.

    Importing this prospective runner must not mutate historical audit modules.
    """

    runner.RUN_ID = RUN_ID
    runner.SCOPE = SCOPE
    runner.TASK_ID = TASK_ID
    runner.SEED = SEED
    runner.MAX_CALLS = MAX_CALLS
    runner.MAX_SERIALIZED = MAX_SERIALIZED
    runner.TASK = runner.ROOT / "task_keystone"
    runner.CONTRACT = runner.ROOT / "KEYSTONE_PRESSURE_SCREEN_CONTRACT.json"
    runner.MODEL_LOCK = runner.ROOT / "KEYSTONE_MODEL_PROFILE_LOCK.json"
    runner.MIN_QUALIFYING_SOURCES = 10
    runner.MIN_QUALIFYING_DOMAINS = 10
    runner.SolaceWorld = KeystoneWorld
    runner.anchored_relational_actor_actions = lambda _configuration_id: (
        phase_lifecycle_actor_actions(
            "F0_FIXED_SCAFFOLD_APPEND_ONLY_VERIFICATION", phase="construction"
        )
    )


def main() -> int:
    configure()
    return runner.main()


if __name__ == "__main__":
    raise SystemExit(main())
