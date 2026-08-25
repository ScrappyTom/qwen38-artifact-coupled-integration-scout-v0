from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from reactive_runtime.bluehaven_boundary import hydrate_bluehaven_pressure_boundary
from reactive_runtime.integration import (
    IntegrationArtifact,
    batched_integration_messages,
    observed_source_ids,
)
from reactive_runtime.records import ResultRecord
from reactive_runtime.world import ArchitectureWorld


@dataclass(frozen=True)
class BluehavenMaintenanceQualificationCase:
    case_id: str
    seed: int
    messages: list[dict[str, str]]
    input_result_ids: tuple[str, ...]
    allowed_source_ids: tuple[str, ...]
    prior: IntegrationArtifact | None


def _source_ids(records: tuple[ResultRecord, ...]) -> tuple[str, ...]:
    values: set[str] = set()
    for record in records:
        values.update(observed_source_ids(record))
    return tuple(sorted(values))


def deterministic_replacement_prior() -> IntegrationArtifact:
    body = """# Evidence Integration Ledger

R01: distinguish public-health order, operational restoration, checking, handoff, expenditure, and closure authority [S01].
R02: preserve residual and benzene units, the conservative plume branch, and two-round release requirements [S02].
R03: keep potable demand, overlapping vulnerability, registry coverage, loss, and critical demand distinct [S03].
R04: retain the shared treatment constraint and bind it to hydraulic delivery rather than summing dependent capacities [S04][S05].
R07: bind generator endurance and fuel resupply to treatment, laboratory, and staffing continuity [S06].
R12: readiness remains unresolved; exact checking and independent candidate-bound adjudication are still required [S01][S02].
"""
    return IntegrationArtifact(
        version=1,
        body=body,
        body_tokens=0,
        input_result_ids=("RESULT-001", "RESULT-002", "RESULT-003"),
        observed_source_ids=("S01", "S02", "S03", "S04", "S05", "S06"),
    )


def build_bluehaven_maintenance_cases(
    repository_root: Path,
) -> tuple[BluehavenMaintenanceQualificationCase, ...]:
    root = repository_root.resolve()
    task = root / "task_bluehaven"
    task_text = (task / "TASK.md").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as temporary:
        world = ArchitectureWorld(task, Path(temporary))
        boundary = hydrate_bluehaven_pressure_boundary(
            repository_root=root,
            world=world,
        )
        records = tuple(boundary.ledger.get(f"RESULT-{ordinal:03d}") for ordinal in range(1, 7))
    first = records[:3]
    second = records[3:]
    prior = deterministic_replacement_prior()
    return (
        BluehavenMaintenanceQualificationCase(
            case_id="Q1_INITIAL_THREE_RESULT_BATCH",
            seed=910_272,
            messages=batched_integration_messages(
                task_text=task_text,
                prior=None,
                newly_externalized=first,
                allowed_source_ids=_source_ids(first),
            ),
            input_result_ids=tuple(record.result_id for record in first),
            allowed_source_ids=_source_ids(first),
            prior=None,
        ),
        BluehavenMaintenanceQualificationCase(
            case_id="Q2_REPLACEMENT_THREE_RESULT_BATCH",
            seed=910_273,
            messages=batched_integration_messages(
                task_text=task_text,
                prior=prior,
                newly_externalized=second,
                allowed_source_ids=tuple(
                    sorted(set(prior.observed_source_ids) | set(_source_ids(second)))
                ),
            ),
            input_result_ids=tuple(record.result_id for record in second),
            allowed_source_ids=tuple(
                sorted(set(prior.observed_source_ids) | set(_source_ids(second)))
            ),
            prior=prior,
        ),
    )
