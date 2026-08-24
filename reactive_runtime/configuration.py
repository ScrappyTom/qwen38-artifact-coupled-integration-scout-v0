from __future__ import annotations

from dataclasses import dataclass


CONFIGURATIONS = ("D0_DETACHED", "A1_COUPLED")


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
