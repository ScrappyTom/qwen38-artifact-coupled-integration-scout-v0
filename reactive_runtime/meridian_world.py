from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Sequence

from reactive_runtime.canonical import canonical_json_text
from reactive_runtime.records import ResultLedger
from reactive_runtime.source_delta import (
    SourceDeltaValidation,
    SourceEvidenceRegister,
    actor_slot_record,
    records_from_delta,
)
from reactive_runtime.world import ActionRejected, ArchitectureWorld, ExecutionResult


class MeridianWorld(ArchitectureWorld):
    """Fresh task world with source/version-local exact evidence slots."""

    def __init__(
        self,
        task_root: Path,
        cell_root: Path,
        *,
        count_text: Callable[[str], int] | None = None,
    ) -> None:
        super().__init__(task_root, cell_root)
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

    def evidence_register(self) -> SourceEvidenceRegister:
        return SourceEvidenceRegister.parse(
            (self.candidate_root / "EVIDENCE_INTEGRATION_LEDGER.md").read_text(
                encoding="utf-8"
            )
        )

    @property
    def source_versions(self) -> dict[str, str]:
        return {
            source_id: source.sha256 for source_id, source in self.sources.items()
        }

    def _replace_register(
        self, register: SourceEvidenceRegister, *, cause: str
    ) -> ExecutionResult:
        rendered = register.render()
        path = self.candidate_root / "EVIDENCE_INTEGRATION_LEDGER.md"
        if path.read_text(encoding="utf-8") == rendered:
            body = canonical_json_text(
                {
                    "candidate_changed": False,
                    "candidate_sha256": self.candidate_sha256,
                    "candidate_version": self.candidate_version,
                    "cause": cause,
                    "schema": "source-slot-state-confirmation-v0",
                }
            )
            return ExecutionResult(
                "candidate_state_confirmation",
                "candidate:EVIDENCE_INTEGRATION_LEDGER.md",
                self.candidate_version,
                body,
                self.candidate_sha256,
                metadata={"candidate_changed": False, "cause": cause},
            )
        return self._replace_file(path.name, rendered, cause)

    def apply_source_delta(
        self,
        validation: SourceDeltaValidation,
        *,
        input_result_ids: Sequence[str],
    ) -> ExecutionResult:
        replacements = records_from_delta(
            validation, input_result_ids=input_result_ids
        )
        register = self.evidence_register().merge(replacements)
        return self._replace_register(register, cause="source_local_maintenance_delta")

    @staticmethod
    def _matching_visible_results(
        ledger: ResultLedger | None, *, source_id: str, source_version: str
    ) -> tuple[str, ...]:
        if ledger is None:
            return ()
        matches: list[str] = []
        for record in ledger.records():
            if not record.previously_visible:
                continue
            source_ids = record.metadata.get("source_ids")
            if not isinstance(source_ids, list) or source_id not in source_ids:
                continue
            versions = record.metadata.get("source_versions")
            observed_version = (
                versions.get(source_id)
                if isinstance(versions, dict)
                else record.metadata.get("source_sha256")
            )
            if observed_version == source_version:
                matches.append(record.result_id)
        return tuple(matches)

    def _upsert_actor_slot(
        self,
        source_id: str,
        source_version: str,
        content: str,
        ledger: ResultLedger | None,
    ) -> ExecutionResult:
        result_ids = self._matching_visible_results(
            ledger, source_id=source_id, source_version=source_version
        )
        if not result_ids:
            raise ActionRejected(
                "source_not_observed",
                "evidence slots require an exact source/version observation that crossed a model boundary",
            )
        try:
            record = actor_slot_record(
                source_id=source_id,
                source_version=source_version,
                content=content,
                known_source_versions=self.source_versions,
                result_ids=result_ids,
                count_text=self._count_text,
            )
        except ValueError as exc:
            raise ActionRejected("invalid_evidence_slot", str(exc)) from exc
        register = self.evidence_register().merge((record,))
        return self._replace_register(register, cause="actor_upsert_evidence_slot")

    def execute(
        self,
        action: dict[str, object],
        *,
        result_id: str,
        ledger: ResultLedger | None = None,
    ) -> ExecutionResult:
        if action.get("action") == "upsert_evidence_slot":
            return self._upsert_actor_slot(
                str(action["source_id"]),
                str(action["source_version"]),
                str(action["content"]),
                ledger,
            )
        return super().execute(action, result_id=result_id, ledger=ledger)
