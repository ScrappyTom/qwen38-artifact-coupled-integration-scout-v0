"""Mechanical activation semantics aligned to the actor's ingress contract.

Eligibility is expressed in delivered source-line coverage, never in result
object count.  This makes one full-source read and a two-source batch comparable
without asking the host to infer what the evidence means.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from reactive_runtime.records import ResultLedger, ResultRecord
from reactive_runtime.world import ArchitectureWorld


MINIMUM_QUALIFYING_SOURCES = 4
MINIMUM_EVIDENCE_DOMAINS = 3


def _segments(record: ResultRecord) -> tuple[dict[str, Any], ...]:
    value = record.metadata.get("segments")
    if not isinstance(value, list):
        return ()
    rows: list[dict[str, Any]] = []
    for row in value:
        if not isinstance(row, dict):
            continue
        source_id = row.get("source_id")
        start = row.get("start_line")
        end = row.get("end_line")
        if (
            isinstance(source_id, str)
            and type(start) is int
            and type(end) is int
            and 1 <= start <= end
        ):
            rows.append({"source_id": source_id, "start_line": start, "end_line": end})
    return tuple(rows)


def _covered_lines(ranges: Iterable[tuple[int, int]]) -> int:
    ordered = sorted(ranges)
    if not ordered:
        return 0
    total = 0
    start, end = ordered[0]
    for next_start, next_end in ordered[1:]:
        if next_start <= end + 1:
            end = max(end, next_end)
        else:
            total += end - start + 1
            start, end = next_start, next_end
    return total + end - start + 1


def delivered_coverage(ledger: ResultLedger) -> dict[str, int]:
    ranges: dict[str, list[tuple[int, int]]] = {}
    for record in ledger.records():
        if record.result_kind != "source_observation" or not record.previously_visible:
            continue
        for row in _segments(record):
            ranges.setdefault(str(row["source_id"]), []).append(
                (int(row["start_line"]), int(row["end_line"]))
            )
    return {
        source_id: _covered_lines(rows) for source_id, rows in sorted(ranges.items())
    }


def pending_novel_lines(pending: ResultRecord, ledger: ResultLedger) -> int:
    # Use exact interval arithmetic rather than subtracting aggregate counts.
    prior: dict[str, set[int]] = {}
    for record in ledger.records():
        if record.result_kind != "source_observation" or not record.previously_visible:
            continue
        for row in _segments(record):
            prior.setdefault(str(row["source_id"]), set()).update(
                range(int(row["start_line"]), int(row["end_line"]) + 1)
            )
    novel = 0
    for row in _segments(pending):
        seen = prior.get(str(row["source_id"]), set())
        novel += sum(
            line not in seen
            for line in range(int(row["start_line"]), int(row["end_line"]) + 1)
        )
    return novel


@dataclass(frozen=True)
class ActivationSnapshot:
    coverage_lines: dict[str, int]
    qualifying_sources: tuple[str, ...]
    qualifying_domains: tuple[str, ...]
    pending_novel_lines: int
    minimum_qualifying_sources: int = MINIMUM_QUALIFYING_SOURCES
    minimum_evidence_domains: int = MINIMUM_EVIDENCE_DOMAINS

    def as_dict(self) -> dict[str, Any]:
        return {
            "coverage_lines": self.coverage_lines,
            "minimum_evidence_domains": self.minimum_evidence_domains,
            "minimum_qualifying_sources": self.minimum_qualifying_sources,
            "pending_novel_lines": self.pending_novel_lines,
            "qualifying_domains": list(self.qualifying_domains),
            "qualifying_sources": list(self.qualifying_sources),
            "schema": "cedar-ingress-aligned-activation-snapshot-v0",
        }


def activation_snapshot(
    *,
    pending: ResultRecord,
    ledger: ResultLedger,
    world: ArchitectureWorld,
    minimum_qualifying_sources: int = MINIMUM_QUALIFYING_SOURCES,
    minimum_evidence_domains: int = MINIMUM_EVIDENCE_DOMAINS,
) -> ActivationSnapshot:
    coverage = delivered_coverage(ledger)
    qualifying = tuple(
        sorted(
            source_id
            for source_id, lines in coverage.items()
            if source_id in world.sources
            and lines >= world.sources[source_id].activation_min_lines
        )
    )
    domains = tuple(
        sorted({world.sources[source_id].evidence_domain for source_id in qualifying})
    )
    return ActivationSnapshot(
        coverage_lines=coverage,
        qualifying_sources=qualifying,
        qualifying_domains=domains,
        pending_novel_lines=pending_novel_lines(pending, ledger),
        minimum_qualifying_sources=minimum_qualifying_sources,
        minimum_evidence_domains=minimum_evidence_domains,
    )


def boundary_eligibility_failures(
    *,
    pending: ResultRecord,
    ledger: ResultLedger,
    world: ArchitectureWorld,
    initial_candidate_sha256: str,
    minimum_qualifying_sources: int = MINIMUM_QUALIFYING_SOURCES,
    minimum_evidence_domains: int = MINIMUM_EVIDENCE_DOMAINS,
) -> tuple[list[str], ActivationSnapshot]:
    """Classify a realized overflow without semantic host judgment."""
    snapshot = activation_snapshot(
        pending=pending,
        ledger=ledger,
        world=world,
        minimum_qualifying_sources=minimum_qualifying_sources,
        minimum_evidence_domains=minimum_evidence_domains,
    )
    failures: list[str] = []
    if pending.result_kind != "source_observation":
        failures.append("pending_result_is_not_source_observation")
    if len(snapshot.qualifying_sources) < minimum_qualifying_sources:
        failures.append("insufficient_delivered_source_coverage")
    if len(snapshot.qualifying_domains) < minimum_evidence_domains:
        failures.append("insufficient_delivered_evidence_domains")
    if snapshot.pending_novel_lines < 1:
        failures.append("pending_observation_has_no_novel_source_lines")
    if world.candidate_sha256 != initial_candidate_sha256:
        failures.append("candidate_changed_before_pressure")
    if world.submitted:
        failures.append("candidate_submitted_before_pressure")
    if any(record.result_kind == "check_observation" for record in ledger.records()):
        failures.append("check_ran_before_pressure")
    return failures, snapshot
