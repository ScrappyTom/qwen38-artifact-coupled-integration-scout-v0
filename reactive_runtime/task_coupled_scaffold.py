"""Requirement coupling layered over the proven anchored-provenance carrier."""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path
from typing import Callable, Mapping, Sequence

from reactive_runtime.anchored_provenance import (
    AnchoredProvenanceRegister,
    ClaimAdmission,
    DeltaAdmission,
    admit_anchored_delta,
)
from reactive_runtime.records import ResultRecord


REQUIREMENT_TAG = re.compile(r"^\[REQUIREMENTS:([A-Z0-9_, -]+)\]\s+", re.IGNORECASE)


def statement_requirements(statement: str) -> tuple[str, ...]:
    match = REQUIREMENT_TAG.match(statement)
    if match is None:
        return ()
    return tuple(
        dict.fromkeys(value.strip().upper() for value in match.group(1).split(",") if value.strip())
    )


def admit_task_coupled_delta(
    text: str,
    *,
    count_text: Callable[[str], int],
    source_catalog: Mapping[str, Mapping[str, object]],
    task_root: Path,
    newly_externalized: Sequence[ResultRecord],
    current_source_versions: Mapping[str, str],
    requirement_ids: Sequence[str],
) -> DeltaAdmission:
    """Apply exact-anchor admission, then independently reject unbound claims."""

    base = admit_anchored_delta(
        text,
        count_text=count_text,
        source_catalog=source_catalog,
        task_root=task_root,
        newly_externalized=newly_externalized,
        current_source_versions=current_source_versions,
    )
    if base.disposition == "global_reject":
        return base
    allowed = set(requirement_ids)
    records: list[ClaimAdmission] = []
    for record in base.records:
        if not record.admitted or record.claim is None:
            records.append(record)
            continue
        links = statement_requirements(record.claim.statement)
        issues = list(record.issues)
        if not links:
            issues.append("target_requirements_missing")
        elif any(link not in allowed for link in links):
            issues.append("target_requirement_unknown")
        if issues:
            records.append(
                replace(
                    record,
                    admitted=False,
                    code=issues[0],
                    issues=tuple(dict.fromkeys(issues)),
                )
            )
        else:
            records.append(record)
    return replace(base, records=tuple(records))


def requirement_index(
    register: AnchoredProvenanceRegister,
) -> dict[str, tuple[str, ...]]:
    index: dict[str, list[str]] = {}
    for claim in register.claims:
        for requirement in statement_requirements(claim.statement):
            index.setdefault(requirement, []).append(claim.claim_id)
    return {key: tuple(values) for key, values in sorted(index.items())}
