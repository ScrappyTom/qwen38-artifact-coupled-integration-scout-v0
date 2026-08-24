from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from reactive_runtime.integration import IntegrationArtifact, integration_messages
from reactive_runtime.world import ArchitectureWorld


@dataclass(frozen=True)
class QualificationCase:
    case_id: str
    seed: int
    messages: list[dict[str, str]]
    allowed_source_ids: tuple[str, ...]


@dataclass(frozen=True)
class ActionQualificationCase:
    case_id: str
    seed: int
    messages: list[dict[str, str]]
    required_action: str


def build_cases(repository_root: Path) -> tuple[QualificationCase, ...]:
    task = repository_root / "task"
    task_text = (task / "TASK.md").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as temporary:
        world = ArchitectureWorld(task, Path(temporary))
        first_execution = world.execute(
            {"action": "read_source", "source_id": "S02", "start_line": 1, "end_line": 180},
            result_id="QUAL-RESULT-001",
        )
        first = world.make_result_record(first_execution, result_id="QUAL-RESULT-001", acquired_call=1)
        second_execution = world.execute(
            {"action": "read_source", "source_id": "S03", "start_line": 1, "end_line": 180},
            result_id="QUAL-RESULT-002",
        )
        second = world.make_result_record(second_execution, result_id="QUAL-RESULT-002", acquired_call=2)
    deterministic_prior = IntegrationArtifact(
        version=1,
        body=(
            "# Evidence Integration Ledger\n\n"
            "R01: exact custody and recovery remain the strongest local substrate [S02].\n\n"
            "R11: system interaction and fresh transfer remain unresolved [S02].\n"
        ),
        body_tokens=36,
        input_result_ids=(first.result_id,),
        observed_source_ids=("S02",),
    )
    return (
        QualificationCase(
            "Q1_INITIALIZE",
            92001,
            integration_messages(
                task_text=task_text,
                prior=None,
                newly_externalized=first,
                allowed_source_ids=("S02",),
            ),
            ("S02",),
        ),
        QualificationCase(
            "Q2_REPLACE",
            92002,
            integration_messages(
                task_text=task_text,
                prior=deterministic_prior,
                newly_externalized=second,
                allowed_source_ids=("S02", "S03"),
            ),
            ("S02", "S03"),
        ),
    )


def build_action_cases(repository_root: Path) -> tuple[ActionQualificationCase, ...]:
    task_text = (repository_root / "task" / "TASK.md").read_text(encoding="utf-8")
    system = (repository_root / "task" / "SYSTEM.md").read_text(encoding="utf-8")
    common = system + "\n\nThis is action-transport qualification, not task execution. Obey the requested action shape exactly."
    return (
        ActionQualificationCase(
            "Q3_INCREMENTAL_SECTION_ACTION",
            92003,
            [
                {"role": "system", "content": common},
                {"role": "user", "content": task_text + "\n\nReturn one upsert_decision_section action for heading `Decision and scope`. Its body must be one concise paragraph explaining that the current question is an exploratory interaction scout, citing [S02]."},
            ],
            "upsert_decision_section",
        ),
        ActionQualificationCase(
            "Q4_TASK_LEDGER_ACTION",
            92004,
            [
                {"role": "system", "content": common},
                {"role": "user", "content": task_text + "\n\nReturn one replace_evidence_ledger action. The content must begin `# Evidence Integration Ledger` and include concise R01 and R11 entries grounded only in [S02]. Do not authorize submission."},
            ],
            "replace_evidence_ledger",
        ),
    )
