from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from reactive_runtime.world import ArchitectureWorld, ExecutionResult


class SolaceWorld(ArchitectureWorld):
    """Fresh regional-water recovery world for system interaction scouting."""

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
            candidate_seed_root=candidate_seed_root,
            candidate_seed_version_index=candidate_seed_version_index,
            evaluator_config_path=evaluator_config_path,
            evaluator_script_path=evaluator_script_path,
        )
        self._count_text = count_text

    def _read_batch(self, requests: list[dict[str, object]]) -> ExecutionResult:
        result = super()._read_batch(requests)
        metadata = dict(result.metadata)
        metadata["source_versions"] = {
            source_id: self.sources[source_id].sha256
            for source_id in metadata.get("source_ids", [])
        }
        return ExecutionResult(
            result.result_kind,
            result.object_id,
            result.object_version,
            result.body,
            result.candidate_sha256_after,
            evaluated_candidate_sha256=result.evaluated_candidate_sha256,
            raw_tool_custody=result.raw_tool_custody,
            metadata=metadata,
        )

    @property
    def source_versions(self) -> dict[str, str]:
        return {source_id: source.sha256 for source_id, source in self.sources.items()}

    def construction_milestone(self) -> dict[str, object]:
        config = self.evaluator_config
        decision = (
            self.candidate_root / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
        ).read_text(encoding="utf-8")
        headings = re.findall(r"(?m)^## ([^\r\n]+)\s*$", decision)
        citation = "|".join(re.escape(source_id) for source_id in self.sources)
        citations = sorted(set(re.findall(rf"\[({citation})\]", decision)))
        without_citations = re.sub(rf"\[(?:{citation})\]", "", decision)
        words = len(re.findall(r"\b[\w’'-]+\b", without_citations))
        passed = (
            decision.startswith(config["decision_title"])
            and headings == config["decision_headings"]
            and words >= config["construction_milestone_minimum_words"]
            and len(citations) >= config["construction_milestone_minimum_sources"]
        )
        return {
            "passed": passed,
            "word_count": words,
            "source_ids": citations,
            "heading_order_passed": headings == config["decision_headings"],
            "minimum_words": config["construction_milestone_minimum_words"],
            "minimum_sources": config["construction_milestone_minimum_sources"],
            "semantic_readiness": "not_adjudicated",
        }
