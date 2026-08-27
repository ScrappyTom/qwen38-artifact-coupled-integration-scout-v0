from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from reactive_runtime.canonical import canonical_json_text
from reactive_runtime.solace_world import SolaceWorld
from reactive_runtime.world import ActionRejected, ExecutionResult


class OrchardWorld(SolaceWorld):
    """Fresh biologics-restart world with a mechanical phase milestone."""

    def __init__(
        self,
        task_root: Path,
        cell_root: Path,
        *,
        count_text: Callable[[str], int] | None = None,
        candidate_seed_root: Path | None = None,
        candidate_seed_version_index: int = 0,
        evaluator_config_path: Path | None = None,
        evaluator_script_path: Path | None = None,
    ) -> None:
        super().__init__(
            task_root,
            cell_root,
            count_text=count_text,
            candidate_seed_root=candidate_seed_root,
            candidate_seed_version_index=candidate_seed_version_index,
            evaluator_config_path=evaluator_config_path,
            evaluator_script_path=evaluator_script_path,
        )
        self.phase = "construction"

    def _begin_verification(self) -> ExecutionResult:
        if self.phase != "construction":
            raise ActionRejected("phase_already_changed", "verification phase already active")
        milestone = self.construction_milestone()
        if not milestone["passed"]:
            raise ActionRejected("construction_milestone_not_met", canonical_json_text(milestone))
        self.phase = "verification"
        return ExecutionResult(
            "phase_effect",
            "phase:verification",
            self.candidate_version,
            canonical_json_text(
                {
                    "candidate_sha256": self.candidate_sha256,
                    "candidate_version": self.candidate_version,
                    "effect": "verification_phase_entered",
                    "milestone": milestone,
                    "readiness": "not_adjudicated",
                    "schema": "orchard-phase-effect-v0",
                }
            ),
            self.candidate_sha256,
            metadata={"phase": self.phase, "milestone": milestone},
        )

    def execute(self, action: dict[str, Any], *, result_id: str, ledger=None) -> ExecutionResult:
        if action["action"] == "begin_verification":
            return self._begin_verification()
        return super().execute(action, result_id=result_id, ledger=ledger)
