from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from reactive_runtime.canonical import canonical_json_text
from reactive_runtime.solace_world import SolaceWorld
from reactive_runtime.verification_causal_frame import apply_bound_section_replacement
from reactive_runtime.world import ActionRejected, ExecutionResult


class KeystoneWorld(SolaceWorld):
    """Fresh rail-restoration world with mechanical verification transition."""

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
            raise ActionRejected(
                "construction_milestone_not_met", canonical_json_text(milestone)
            )
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
                    "schema": "keystone-phase-effect-v0",
                }
            ),
            self.candidate_sha256,
            metadata={"phase": self.phase, "milestone": milestone},
        )

    def _replace_artifact_section(self, action: dict[str, Any]) -> ExecutionResult:
        path = self.candidate_root / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
        current = path.read_text(encoding="utf-8")
        updated, disposition = apply_bound_section_replacement(
            current,
            action,
            current_candidate_sha256=self.candidate_sha256,
        )
        if disposition["status"] != "admitted":
            raise ActionRejected(str(disposition["code"]), canonical_json_text(disposition))
        return self._replace_file(
            path.name,
            updated,
            "actor_bound_section_replacement",
        )

    def execute(self, action: dict[str, Any], *, result_id: str, ledger=None) -> ExecutionResult:
        if action["action"] == "begin_verification":
            return self._begin_verification()
        if action["action"] == "replace_artifact_section":
            if self.phase != "verification":
                raise ActionRejected(
                    "verification_action_before_phase",
                    "bound section repair is available only in verification",
                )
            return self._replace_artifact_section(action)
        if action["action"] in {"run_check", "submit"} and self.phase != "verification":
            raise ActionRejected(
                "verification_action_before_phase",
                f"{action['action']} is available only in verification",
            )
        return super().execute(action, result_id=result_id, ledger=ledger)
