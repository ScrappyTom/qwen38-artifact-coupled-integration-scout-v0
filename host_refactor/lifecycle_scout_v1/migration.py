from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from host_refactor.lifecycle_scout.migration import (
    MigrationOutcome,
    migrate_e96_donor,
)
from host_refactor.lifecycle_scout_v1.system import build_system


def migrate_donor(
    *,
    repository_root: Path,
    trajectory_root: Path,
    count_messages: Callable[[list[dict[str, str]]], int],
    count_text: Callable[[str], int],
    maintenance_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    checkpoint_output: Path | None = None,
    receipt_output: Path | None = None,
) -> MigrationOutcome:
    return migrate_e96_donor(
        repository_root=repository_root,
        trajectory_root=trajectory_root,
        count_messages=count_messages,
        count_text=count_text,
        maintenance_complete=maintenance_complete,
        checkpoint_output=checkpoint_output,
        receipt_output=receipt_output,
        system_builder=build_system,
    )
