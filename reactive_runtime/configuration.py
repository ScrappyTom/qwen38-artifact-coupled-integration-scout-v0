from __future__ import annotations

from dataclasses import dataclass


CONFIGURATIONS = ("D0_DETACHED", "A1_COUPLED")
BLUEHAVEN_CONFIGURATIONS = ("B1_BATCHED_COUPLED", "W1_DIRECT_WORK")


@dataclass(frozen=True)
class Configuration:
    configuration_id: str
    artifact_coupled: bool


def configuration(configuration_id: str) -> Configuration:
    if configuration_id not in CONFIGURATIONS:
        raise ValueError(f"unknown configuration: {configuration_id}")
    return Configuration(
        configuration_id=configuration_id,
        artifact_coupled=configuration_id == "A1_COUPLED",
    )


def ordinary_actions() -> tuple[str, ...]:
    return (
        "read_source",
        "read_batch",
        "reopen_exact",
        "replace_evidence_ledger",
        "upsert_decision_section",
        "replace_decision",
        "run_check",
        "submit",
    )


def bluehaven_actor_actions(configuration_id: str) -> tuple[str, ...]:
    """Return the actor surface for one complete Bluehaven operating policy.

    B1 assigns evidence-ledger replacement to the batched maintenance pass.
    W1 has no maintenance provider, so its ordinary actor owns that exact work
    operation. Both retain the same evidence, decision, feedback, and closure
    actions otherwise.
    """
    if configuration_id not in BLUEHAVEN_CONFIGURATIONS:
        raise ValueError(f"unknown Bluehaven configuration: {configuration_id}")
    actions = ordinary_actions()
    if configuration_id == "B1_BATCHED_COUPLED":
        return tuple(action for action in actions if action != "replace_evidence_ledger")
    return actions
