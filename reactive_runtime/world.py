from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from reactive_runtime.actions import (
    DECISION_HEADINGS,
    MAX_BATCH_RANGES,
    MAX_BATCH_SOURCE_BYTES,
    MAX_BATCH_TOTAL_LINES,
    MAX_READ_LINES,
)
from reactive_runtime.canonical import canonical_json_text, sha256_bytes, sha256_file, write_bytes, write_json
from reactive_runtime.configuration import configuration
from reactive_runtime.diagnostics import (
    RawToolCustody,
    bind_observation_currency,
    parse_evaluator_stdout,
    project_check,
    render_check_projection,
)
from reactive_runtime.integration import IntegrationArtifact
from reactive_runtime.records import ResultLedger, ResultRecord, wrap_action_result


class ActionRejected(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class SourceObject:
    source_id: str
    title: str
    evidence_domain: str
    activation_min_lines: int
    path: Path
    sha256: str
    size_bytes: int
    lines: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionResult:
    result_kind: str
    object_id: str
    object_version: str
    body: str
    candidate_sha256_after: str
    evaluated_candidate_sha256: str | None = None
    raw_tool_custody: RawToolCustody | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ArchitectureWorld:
    candidate_files = (
        "EVIDENCE_INTEGRATION_LEDGER.md",
        "BOUNDED_AGENT_ARCHITECTURE_DECISION.md",
    )

    def __init__(self, task_root: Path, cell_root: Path) -> None:
        self.task_root = task_root.resolve()
        self.cell_root = cell_root.resolve()
        self.world_root = self.cell_root / "world"
        self.candidate_root = self.world_root / "candidate"
        self.candidate_root.mkdir(parents=True, exist_ok=True)
        for name in self.candidate_files:
            shutil.copyfile(self.task_root / "candidate" / name, self.candidate_root / name)
        self.sources = self._load_sources()
        self.version_index = 0
        self.submitted = False
        self.last_check_projection: dict[str, Any] | None = None
        self.detached_integration: IntegrationArtifact | None = None
        self._snapshot("initial")

    def _load_sources(self) -> dict[str, SourceObject]:
        catalog = json.loads((self.task_root / "SOURCE_CATALOG.json").read_text(encoding="utf-8"))
        result: dict[str, SourceObject] = {}
        for row in catalog["sources"]:
            path = (self.task_root / row["path"]).resolve()
            raw = path.read_bytes()
            if sha256_bytes(raw) != row["sha256"]:
                raise ValueError(f"source hash mismatch: {row['source_id']}")
            text = raw.decode("utf-8")
            result[row["source_id"]] = SourceObject(
                row["source_id"],
                row["title"],
                row["evidence_domain"],
                int(row["activation_min_lines"]),
                path,
                row["sha256"],
                len(raw),
                tuple(text.splitlines()),
            )
        return result

    @property
    def candidate_manifest(self) -> dict[str, str]:
        return {name: sha256_file(self.candidate_root / name) for name in sorted(self.candidate_files)}

    @property
    def candidate_sha256(self) -> str:
        return sha256_bytes(canonical_json_text(self.candidate_manifest).encode("utf-8"))

    @property
    def candidate_version(self) -> str:
        return f"candidate-v{self.version_index:03d}:{self.candidate_sha256}"

    def candidate_packet(self) -> str:
        chunks = [canonical_json_text({"candidate_sha256": self.candidate_sha256, "candidate_version": self.candidate_version, "files": self.candidate_manifest, "schema": "architecture-current-candidate-v0"})]
        for name in self.candidate_files:
            chunks.append(f"--- exact candidate file: {name} ---\n" + (self.candidate_root / name).read_text(encoding="utf-8"))
        return "\n".join(chunks)

    def construction_milestone(self) -> dict[str, Any]:
        """Return the frozen mechanical construction milestone for budgeting.

        This grants post-construction decisions; it does not assert semantic
        quality, readiness, or closure.
        """
        config = json.loads(
            (self.task_root / "EVALUATOR.json").read_text(encoding="utf-8")
        )
        decision = (
            self.candidate_root / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
        ).read_text(encoding="utf-8")
        headings = re.findall(r"(?m)^## ([^\r\n]+)\s*$", decision)
        without_citations = re.sub(r"\[S\d{2}\]", "", decision)
        words = len(re.findall(r"\b[\w’'-]+\b", without_citations))
        sources = sorted(set(re.findall(r"\[(S(?:0[1-9]|1[0-6]))\]", decision)))
        passed = (
            decision.startswith(config["decision_title"])
            and headings == config["decision_headings"]
            and words >= config["construction_milestone_minimum_words"]
            and len(sources) >= config["construction_milestone_minimum_sources"]
        )
        return {
            "passed": passed,
            "word_count": words,
            "source_ids": sources,
            "heading_order_passed": headings == config["decision_headings"],
            "minimum_words": config["construction_milestone_minimum_words"],
            "minimum_sources": config["construction_milestone_minimum_sources"],
            "semantic_readiness": "not_adjudicated",
        }

    def _snapshot(self, cause: str) -> None:
        destination = self.cell_root / "candidate_versions" / f"version-{self.version_index:03d}"
        destination.mkdir(parents=True, exist_ok=False)
        for name in self.candidate_files:
            shutil.copyfile(self.candidate_root / name, destination / name)
        write_json(destination / "CANDIDATE_MANIFEST.json", {"cause": cause, "candidate_sha256": self.candidate_sha256, "candidate_version": self.candidate_version, "files": self.candidate_manifest})

    def source_catalog_for_actor(self) -> str:
        rows = [
            {
                "source_id": source.source_id,
                "title": source.title,
                "line_count": len(source.lines),
                "size_bytes": source.size_bytes,
                "sha256": source.sha256,
            }
            for source in self.sources.values()
        ]
        return canonical_json_text({"schema": "architecture-source-catalog-v0", "sources": rows})

    def _read_source(self, source_id: str, start: int, end: int) -> ExecutionResult:
        source = self.sources.get(source_id)
        if source is None:
            raise ActionRejected("unknown_source", f"unknown source: {source_id}")
        if start < 1 or end < start:
            raise ActionRejected("invalid_range", "range must satisfy 1 <= start <= end")
        if end > len(source.lines):
            raise ActionRejected("range_out_of_bounds", f"{source_id} has {len(source.lines)} lines")
        if end - start + 1 > MAX_READ_LINES:
            raise ActionRejected("range_too_large", f"maximum is {MAX_READ_LINES} lines")
        body_text = "\n".join(source.lines[start - 1 : end])
        binding = canonical_json_text({"end_line": end, "source_id": source_id, "source_path": str(source.path.relative_to(self.task_root)).replace("\\", "/"), "source_sha256": source.sha256, "source_size_bytes": source.size_bytes, "start_line": start})
        return ExecutionResult("source_observation", f"source:{source_id}:{start}-{end}", source.sha256, binding + "\n--- exact source range ---\n" + body_text, self.candidate_sha256, metadata={"source_id": source_id, "source_ids": [source_id], "source_path": str(source.path.relative_to(self.task_root)).replace("\\", "/"), "source_sha256": source.sha256, "source_size_bytes": source.size_bytes, "start_line": start, "end_line": end, "segments": [{"source_id": source_id, "start_line": start, "end_line": end}]})

    def _read_batch(self, requests: list[dict[str, Any]]) -> ExecutionResult:
        if not 1 <= len(requests) <= MAX_BATCH_RANGES:
            raise ActionRejected("invalid_batch_size", f"batch must contain 1..{MAX_BATCH_RANGES} ranges")
        total_lines = sum(int(row["end_line"]) - int(row["start_line"]) + 1 for row in requests)
        if total_lines > MAX_BATCH_TOTAL_LINES:
            raise ActionRejected("batch_lines_exceeded", f"batch may contain at most {MAX_BATCH_TOTAL_LINES} lines")
        for index, left in enumerate(requests):
            for right in requests[index + 1 :]:
                if left["source_id"] == right["source_id"] and not (
                    left["end_line"] < right["start_line"] or right["end_line"] < left["start_line"]
                ):
                    raise ActionRejected("batch_overlap", "same-source batch ranges may not overlap")
        singles = [self._read_source(row["source_id"], row["start_line"], row["end_line"]) for row in requests]
        total = sum(len(item.body.encode("utf-8")) for item in singles)
        if total > MAX_BATCH_SOURCE_BYTES:
            raise ActionRejected("batch_source_bytes_exceeded", f"batch exact bytes {total} exceed {MAX_BATCH_SOURCE_BYTES}")
        segments = [item.metadata["segments"][0] for item in singles]
        binding = canonical_json_text({"schema": "architecture-batch-observation-v0", "segments": segments, "total_source_bytes": total})
        chunks = [binding] + [f"--- exact batch segment {i} ---\n{item.body}" for i, item in enumerate(singles, 1)]
        return ExecutionResult("source_observation", "batch:" + "+".join(f"{r['source_id']}:{r['start_line']}-{r['end_line']}" for r in requests), sha256_bytes(binding.encode("utf-8")), "\n".join(chunks), self.candidate_sha256, metadata={"batch": True, "segments": segments, "source_ids": list(dict.fromkeys(row["source_id"] for row in requests)), "total_source_bytes": total})

    def _candidate_effect(self, *, before: str, changed_file: str, cause: str) -> ExecutionResult:
        after = self.candidate_sha256
        prior = self.current_check_binding()
        body = canonical_json_text({"after_sha256": after, "before_sha256": before, "candidate_version": self.candidate_version, "changed_file": changed_file, "cause": cause, "current_candidate_verification_status": "not_run_after_candidate_effect", "prior_check_binding": prior, "schema": "architecture-candidate-effect-v0"})
        return ExecutionResult("candidate_effect", f"candidate:{changed_file}", self.candidate_version, body, after, metadata={"before_sha256": before, "changed_file": changed_file, "cause": cause})

    def _replace_file(self, name: str, content: str, cause: str) -> ExecutionResult:
        raw = content.encode("utf-8")
        if not raw or len(raw) > 250_000:
            raise ActionRejected("candidate_size", "candidate replacement must contain 1..250000 bytes")
        path = self.candidate_root / name
        if raw == path.read_bytes():
            raise ActionRejected("no_effect", "replacement is byte-identical")
        before = self.candidate_sha256
        write_bytes(path, raw)
        self.version_index += 1
        self._snapshot(cause)
        return self._candidate_effect(before=before, changed_file=name, cause=cause)

    def apply_integration(self, configuration_id: str, artifact: IntegrationArtifact) -> ExecutionResult:
        config = configuration(configuration_id)
        if config.artifact_coupled:
            path = self.candidate_root / "EVIDENCE_INTEGRATION_LEDGER.md"
            if path.read_bytes() == artifact.body.encode("utf-8"):
                body = canonical_json_text(
                    {
                        "artifact_coupled": True,
                        "candidate_changed": False,
                        "candidate_sha256": self.candidate_sha256,
                        "candidate_version": self.candidate_version,
                        "integration_body_sha256": artifact.body_sha256,
                        "integration_version": artifact.version,
                        "schema": "architecture-coupled-integration-confirmation-v0",
                    }
                )
                return ExecutionResult(
                    "candidate_state_confirmation",
                    "candidate:EVIDENCE_INTEGRATION_LEDGER.md",
                    self.candidate_version,
                    body,
                    self.candidate_sha256,
                    metadata={"artifact_coupled": True, "candidate_changed": False},
                )
            return self._replace_file("EVIDENCE_INTEGRATION_LEDGER.md", artifact.body, "maintenance_integration_coupled")
        self.detached_integration = artifact
        body = canonical_json_text({"artifact_coupled": False, "body_sha256": artifact.body_sha256, "body_tokens": artifact.body_tokens, "candidate_sha256_unchanged": self.candidate_sha256, "integration_version": artifact.version, "schema": "architecture-detached-integration-effect-v0"})
        return ExecutionResult("semantic_state_effect", "sidecar:integration-ledger", artifact.body_sha256, body, self.candidate_sha256, metadata={"artifact_coupled": False})

    def _upsert_section(self, heading: str, body: str) -> ExecutionResult:
        if heading not in DECISION_HEADINGS:
            raise ActionRejected("unknown_heading", heading)
        path = self.candidate_root / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
        text = path.read_text(encoding="utf-8")
        matches = list(re.finditer(r"(?m)^## ([^\r\n]+)\s*$", text))
        preamble = text[: matches[0].start()].rstrip() if matches else text.rstrip()
        sections: dict[str, str] = {}
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections[match.group(1).strip()] = text[match.end() : end].strip()
        sections[heading] = body.strip()
        rendered = [preamble]
        for declared in DECISION_HEADINGS:
            if declared in sections:
                rendered.append(f"## {declared}\n\n{sections[declared]}")
        return self._replace_file(path.name, "\n\n".join(rendered).rstrip() + "\n", "actor_upsert_decision_section")

    def _run_check(self, result_id: str) -> ExecutionResult:
        evaluated = self.candidate_sha256
        evaluator_id = json.loads(
            (self.task_root / "EVALUATOR.json").read_text(encoding="utf-8")
        )["evaluator_id"]
        raw_handle = f"raw-tool://{result_id}/evaluator"
        command = (sys.executable, str(self.task_root / "evaluator" / "evaluate.py"), str(self.candidate_root))
        process = subprocess.run(command, cwd=self.task_root, capture_output=True, check=False, timeout=180)
        raw = RawToolCustody(command, process.returncode, "completed", process.stdout, process.stderr, evaluated, raw_handle)
        raw_root = self.cell_root / "raw_tool_results" / result_id
        write_bytes(raw_root / "stdout.bin", process.stdout)
        write_bytes(raw_root / "stderr.bin", process.stderr)
        write_json(raw_root / "RAW_TOOL_RECEIPT.json", raw.receipt())
        try:
            evaluation = parse_evaluator_stdout(process.stdout)
            if evaluation.get("candidate_sha256") != evaluated:
                raise ValueError("evaluator candidate hash mismatch")
            projection = project_check(evaluation, evaluated_candidate_sha256=evaluated, raw_result_handle=raw_handle, returncode=process.returncode)
        except ValueError as exc:
            projection = {"blocking_requirements": ["evaluator_protocol_error"], "closure_readiness": "not_ready", "criterion_results": [], "evaluated_candidate_sha256": evaluated, "evaluator_id": evaluator_id, "passed": False, "protocol_error_class": type(exc).__name__, "raw_result_handle": raw_handle, "raw_result_preserved_exactly": True, "returncode_class": "zero" if process.returncode == 0 else "nonzero", "schema": "cedar-stable-check-projection-v0", "volatile_fields_excluded": True}
        self.last_check_projection = projection
        return ExecutionResult("check_observation", f"evaluator:{evaluator_id}", evaluated, render_check_projection(projection), self.candidate_sha256, evaluated_candidate_sha256=evaluated, raw_tool_custody=raw, metadata={"check_projection": projection})

    def current_check_binding(self) -> dict[str, Any] | None:
        if self.last_check_projection is None:
            return None
        return bind_observation_currency(self.last_check_projection, current_candidate_sha256=self.candidate_sha256)

    def _reopen(self, result_id: str, ledger: ResultLedger | None) -> ExecutionResult:
        if ledger is None:
            raise ActionRejected("ledger_required", "exact reopen requires custody ledger")
        try:
            original = ledger.exact_reopen(result_id)
        except (KeyError, ValueError) as exc:
            raise ActionRejected("result_not_reopenable", str(exc)) from exc
        body = canonical_json_text({"original_result_id": result_id, "original_sha256": original.content_sha256, "schema": "architecture-exact-reopen-v0"}) + "\n--- exact original model-visible result ---\n" + original.exact_content
        return ExecutionResult("exact_reopen_observation", f"result:{result_id}", original.content_sha256, body, self.candidate_sha256, metadata={**original.metadata, "reopened_result_id": result_id})

    def _submit(self) -> ExecutionResult:
        if self.submitted:
            raise ActionRejected("already_submitted", "candidate already submitted")
        destination = self.cell_root / "submissions" / self.candidate_sha256
        destination.mkdir(parents=True, exist_ok=False)
        for name in self.candidate_files:
            shutil.copyfile(self.candidate_root / name, destination / name)
        write_json(destination / "SUBMISSION_MANIFEST.json", {"candidate_sha256": self.candidate_sha256, "candidate_version": self.candidate_version, "files": self.candidate_manifest, "readiness": "requires_external_adjudication"})
        self.submitted = True
        return ExecutionResult("submission_effect", "submission:evacuation-package", self.candidate_version, canonical_json_text({"candidate_sha256": self.candidate_sha256, "effect": "submission_proposal_recorded", "readiness": "requires_external_candidate_bound_adjudication"}), self.candidate_sha256)

    def execute(self, action: dict[str, Any], *, result_id: str, ledger: ResultLedger | None = None) -> ExecutionResult:
        name = action["action"]
        if name == "read_source":
            return self._read_source(action["source_id"], action["start_line"], action["end_line"])
        if name == "read_batch":
            return self._read_batch(action["requests"])
        if name == "reopen_exact":
            return self._reopen(action["result_id"], ledger)
        if name == "replace_evidence_ledger":
            return self._replace_file("EVIDENCE_INTEGRATION_LEDGER.md", action["content"], "actor_replace_evidence_ledger")
        if name == "replace_decision":
            return self._replace_file("BOUNDED_AGENT_ARCHITECTURE_DECISION.md", action["content"], "actor_replace_decision")
        if name == "upsert_decision_section":
            return self._upsert_section(action["heading"], action["body"])
        if name == "run_check":
            return self._run_check(result_id)
        if name == "submit":
            return self._submit()
        raise ActionRejected("unknown_action", str(name))

    def make_result_record(self, execution: ExecutionResult, *, result_id: str, acquired_call: int) -> ResultRecord:
        exact = wrap_action_result(result_id=result_id, result_kind=execution.result_kind, object_id=execution.object_id, object_version=execution.object_version, body=execution.body)
        return ResultRecord(result_id=result_id, result_kind=execution.result_kind, object_id=execution.object_id, object_version=execution.object_version, exact_content=exact, acquired_call=acquired_call, candidate_sha256_after=execution.candidate_sha256_after, relief_eligible=execution.result_kind in {"source_observation", "exact_reopen_observation"}, evaluated_candidate_sha256=execution.evaluated_candidate_sha256, raw_result_handle=None if execution.raw_tool_custody is None else execution.raw_tool_custody.raw_result_handle, metadata=execution.metadata)
