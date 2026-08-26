from __future__ import annotations

from dataclasses import dataclass


CONFIGURATIONS = ("D0_DETACHED", "A1_COUPLED")
BLUEHAVEN_CONFIGURATIONS = ("B1_BATCHED_COUPLED", "W1_DIRECT_WORK")
DELTA_CONFIGURATIONS = ("W0_DIRECT_WORK", "L1_LOCAL_DELTA")
RELATIONAL_CONFIGURATIONS = (
    "W0_DIRECT_EXACT_WORK",
    "L1_PROVENANCE_LOCAL_RELATIONAL",
)
ANCHORED_RELATIONAL_CONFIGURATIONS = (
    "W0_DIRECT_EXACT_WORK_FRESH",
    "L1_FAULT_TOLERANT_ANCHORED_PROVENANCE",
)


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


def delta_common_actions() -> tuple[str, ...]:
    return (
        "read_source",
        "read_batch",
        "reopen_exact",
        "upsert_decision_section",
        "replace_decision",
        "run_check",
        "submit",
    )


def delta_actor_actions(configuration_id: str) -> tuple[str, ...]:
    if configuration_id not in DELTA_CONFIGURATIONS:
        raise ValueError(f"unknown source-delta configuration: {configuration_id}")
    actions = delta_common_actions()
    if configuration_id == "W0_DIRECT_WORK":
        return (*actions[:3], "upsert_evidence_slot", *actions[3:])
    return actions


def relational_actor_actions(configuration_id: str) -> tuple[str, ...]:
    if configuration_id not in RELATIONAL_CONFIGURATIONS:
        raise ValueError(f"unknown provenance-relational configuration: {configuration_id}")
    return ordinary_actions()


def anchored_relational_actor_actions(configuration_id: str) -> tuple[str, ...]:
    if configuration_id not in ANCHORED_RELATIONAL_CONFIGURATIONS:
        raise ValueError(f"unknown anchored-provenance configuration: {configuration_id}")
    return ordinary_actions()
