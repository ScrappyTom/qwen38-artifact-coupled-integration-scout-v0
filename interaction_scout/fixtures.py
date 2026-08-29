from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping

from reactive_runtime.canonical import canonical_json_text, sha256_bytes
from reactive_runtime.provenance_claims import (
    NON_AUTHORITATIVE_DERIVATIVE,
    OWNER_SOURCE_REPORTED,
    SOURCE_REPORTED_FACT,
)
from reactive_runtime.verification_causal_frame import section_spans

from host_refactor.trellis_adapter import TrellisDomainAdapter


READ_ACTIONS: tuple[dict[str, Any], ...] = (
    {"action": "read_batch", "requests": [{"source_id": "COUNCIL", "start_line": 1, "end_line": 60}, {"source_id": "CLIMATE", "start_line": 1, "end_line": 60}]},
    {"action": "read_batch", "requests": [{"source_id": "COUNCIL", "start_line": 61, "end_line": 94}, {"source_id": "CLIMATE", "start_line": 61, "end_line": 94}]},
    {"action": "read_batch", "requests": [{"source_id": "GRID", "start_line": 1, "end_line": 60}, {"source_id": "WATER", "start_line": 1, "end_line": 60}]},
    {"action": "read_batch", "requests": [{"source_id": "GRID", "start_line": 61, "end_line": 94}, {"source_id": "WATER", "start_line": 61, "end_line": 94}]},
    {"action": "read_batch", "requests": [{"source_id": "CLINIC", "start_line": 1, "end_line": 60}, {"source_id": "SHELTER", "start_line": 1, "end_line": 60}]},
    {"action": "read_batch", "requests": [{"source_id": "CLINIC", "start_line": 61, "end_line": 94}, {"source_id": "SHELTER", "start_line": 61, "end_line": 94}]},
    {"action": "read_batch", "requests": [{"source_id": "TRANSIT", "start_line": 1, "end_line": 60}, {"source_id": "COMMS", "start_line": 1, "end_line": 60}]},
    {"action": "read_batch", "requests": [{"source_id": "TRANSIT", "start_line": 61, "end_line": 94}, {"source_id": "COMMS", "start_line": 61, "end_line": 94}]},
    {"action": "read_batch", "requests": [{"source_id": "SUPPLY", "start_line": 1, "end_line": 60}, {"source_id": "LABOR", "start_line": 1, "end_line": 60}]},
    {"action": "read_batch", "requests": [{"source_id": "SUPPLY", "start_line": 61, "end_line": 94}, {"source_id": "LABOR", "start_line": 61, "end_line": 94}]},
    {"action": "read_batch", "requests": [{"source_id": "LINEAGE", "start_line": 1, "end_line": 60}, {"source_id": "REVIEW", "start_line": 1, "end_line": 60}]},
    {"action": "read_batch", "requests": [{"source_id": "LINEAGE", "start_line": 61, "end_line": 94}, {"source_id": "REVIEW", "start_line": 61, "end_line": 94}]},
)


def evidence_ledger() -> str:
    sources = (
        "COUNCIL CLIMATE GRID WATER CLINIC SHELTER TRANSIT COMMS SUPPLY LABOR "
        "LINEAGE REVIEW"
    ).split()
    rows = ["# Trellis Evidence-to-Requirement Matrix", ""]
    rows.extend(f"- [{source}] exact evidence observed and remains reopenable." for source in sources)
    return "\n".join(rows) + "\n"


def _section_bodies(*, water_defect: bool) -> dict[str, str]:
    water_gate = (
        "The water gate requires 38 psi observed and at least 35 psi at every node."
        if water_defect
        else "The water gate requires 38 psi observed and at least 35 psi at every node for three consecutive ten-minute windows."
    )
    return {
        "Authority, scope, and operating states": (
            "The emergency manager activates limited cooling operations. The health commissioner authorizes the citywide heat-health emergency, while the continuity director closes the incident only after current evidence is reconciled. A mechanical check is not authority and does not authorize closure. These powers remain distinct, version bound, and reviewable. [COUNCIL] [REVIEW]"
        ),
        "Heat triggers and geographic staging": (
            "The current 31.4 degrees Celsius observation is above the 30.0 degrees limited gate only when sustained for two consecutive windows. Expanded operation uses 32.0 degrees, not the single current observation. The 0.62 forecast probability is different from 84 percent station coverage, so neither figure may substitute for the other. [CLIMATE] [LINEAGE]"
        ),
        "Power, water, and cooling continuity": (
            "Power records distinguish 31.0 megawatts installed from 24.5 megawatts usable. The 12.6 kilovolts observation must remain within 12.2 to 12.9 kilovolts at every node for three consecutive fifteen-minute windows. Backup provides 8.4 megawatts for sixteen hours under emergency load versus nine hours at full load. "
            + water_gate
            + " Reserve is 1.6 million liters, while flow is 0.19 million liters per hour. [GRID] [WATER]"
        ),
        "Clinical, shelter, and accessibility operations": (
            "Clinical occupancy is 71 percent against an 82 percent gate for two consecutive windows, with twelve staffed cooling beds separately confirmed. Shelter planning distinguishes 2,400 seats installed from 1,760 seats staffed and accessible. These observations remain prerequisites rather than declarations of readiness. [CLINIC] [SHELTER]"
        ),
        "Transit, communications, logistics, and staffing": (
            "Transit has twenty-two of twenty-six shuttles plus four accessible vehicles. Route median is 26 minutes while p95 is 44 minutes. Communication delivery is 89 percent and leaves 11 percent uncertainty; latency is 680 ms p95 and 1,140 ms p99. Fuel supports sixteen hours of emergency load versus nine hours full load. Inventory distinguishes 2.8 operating days from 3.6 clinic-days. Labor requires twelve hours off after ten consecutive hours, with twenty-six drivers and ten interpreters. [TRANSIT] [COMMS] [SUPPLY] [LABOR]"
        ),
        "Execution, rollback, verification, and closure": (
            "Candidate T9 binds F6, G4, R8, L11, and C7. T8 is historical unless transferred and rechecked. Independent authorized acceptance remains required before closure. Each operating change records its owner, prerequisite, observation, falsifier, rollback, current candidate, and evidence that retires the temporary control. [LINEAGE] [REVIEW]"
        ),
    }


def decision(*, water_defect: bool) -> str:
    bodies = _section_bodies(water_defect=water_defect)
    filler = (
        " Operators record the governing source, current observation, responsible owner, "
        "falsifier, rollback trigger, and next verification event without converting an "
        "observation into authority or treating an old candidate result as current."
    )
    rendered = ["# Trellis Urban Heat Continuity Decision"]
    for heading, body in bodies.items():
        rendered.append(f"## {heading}\n\n{body}{filler * 7}")
    return "\n\n".join(rendered).rstrip() + "\n"


def repair_action(adapter: TrellisDomainAdapter) -> dict[str, Any]:
    path = adapter.world.candidate_root / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
    current = path.read_text(encoding="utf-8")
    corrected = decision(water_defect=False)
    heading = "Power, water, and cooling continuity"
    old_section = next(row for row in section_spans(current) if row["heading"] == heading)
    new_section = next(row for row in section_spans(corrected) if row["heading"] == heading)
    return {
        "action": "replace_artifact_section",
        "artifact_sha256": sha256_bytes(current.encode("utf-8")),
        "candidate_sha256": adapter.world.candidate_sha256,
        "expected_section_sha256": old_section["sha256"],
        "replacement_section": new_section["text"],
        "section_heading": heading,
    }


class ScriptedActorProvider:
    def __init__(
        self,
        adapter: TrellisDomainAdapter,
        count_messages: Callable[[list[dict[str, str]]], int],
        count_text: Callable[[str], int],
    ) -> None:
        self.adapter = adapter
        self.count_messages = count_messages
        self.count_text = count_text
        self.calls = 0

    def _action(self) -> dict[str, Any]:
        index = self.calls
        if index < len(READ_ACTIONS):
            return READ_ACTIONS[index]
        tail: tuple[Callable[[], dict[str, Any]], ...] = (
            lambda: {"action": "replace_evidence_ledger", "content": evidence_ledger()},
            lambda: {"action": "replace_decision", "content": decision(water_defect=True)},
            lambda: {"action": "begin_verification"},
            lambda: {"action": "run_check"},
            lambda: repair_action(self.adapter),
            lambda: {"action": "run_check"},
            lambda: {"action": "submit"},
        )
        tail_index = index - len(READ_ACTIONS)
        if tail_index >= len(tail):
            raise RuntimeError("scripted actor exhausted")
        return tail[tail_index]()

    def __call__(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        action = self._action()
        self.calls += 1
        content = canonical_json_text(action)
        messages = payload.get("messages")
        if not isinstance(messages, list):
            raise ValueError("actor payload lacks messages")
        prompt = self.count_messages(messages)
        completion = self.count_text(content)
        return {
            "content": content,
            "finish_reason": "stop",
            "usage": {
                "completion_tokens": completion,
                "prompt_tokens": prompt,
                "total_tokens": prompt + completion,
            },
        }


class GroundedMaintenanceFixture:
    """Provider-free transport fixture; it makes no utility claim."""

    def __init__(
        self,
        task_root: Path,
        count_messages: Callable[[list[dict[str, str]]], int],
        count_text: Callable[[str], int],
    ) -> None:
        self.task_root = task_root
        self.count_messages = count_messages
        self.count_text = count_text
        self.calls = 0
        catalog = json.loads((task_root / "SOURCE_CATALOG.json").read_text(encoding="utf-8"))
        self.catalog = {str(row["source_id"]): row for row in catalog["sources"]}

    def __call__(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        messages = payload.get("messages")
        if not isinstance(messages, list):
            raise ValueError("maintenance payload lacks messages")
        text = "\n".join(str(row.get("content", "")) for row in messages if isinstance(row, Mapping))
        versions = re.search(r"NEW SOURCE VERSIONS\n([\s\S]+?)\n\nPRIOR", text)
        result = re.search(r"--- NEWLY EXTERNALIZED (RESULT-[0-9]+) ---", text)
        if versions is None or result is None:
            raise ValueError("maintenance fixture cannot bind input")
        first_version = next(line for line in versions.group(1).splitlines() if ": " in line)
        source_id, source_version = first_version.split(": ", 1)
        source_path = self.task_root / str(self.catalog[source_id]["path"])
        candidates = [
            line.strip()
            for line in source_path.read_text(encoding="utf-8").splitlines()
            if len(line.strip()) >= 24
            and not line.startswith("#")
            and not line.startswith("|")
            and not any(
                other in line
                for other in self.catalog
                if other != source_id
            )
        ]
        anchor = candidates[0]
        content = "\n".join(
            (
                "# Anchored provenance-local delta",
                f"## CLAIM FIXTURE_{self.calls + 1:03d}",
                f"SLOT_SOURCE: {source_id}",
                f"SOURCE_VERSION: {source_version}",
                f"EVIDENCE_RESULT: {result.group(1)}",
                f"EVIDENCE_ANCHOR: {anchor}",
                f"MODE: {SOURCE_REPORTED_FACT}",
                f"ATTRIBUTION: {OWNER_SOURCE_REPORTED}",
                "REFERENTS: NONE",
                f"AUTHORITY: {NON_AUTHORITATIVE_DERIVATIVE}",
                f"STATEMENT: {source_id} reports: {anchor}",
            )
        )
        self.calls += 1
        prompt = self.count_messages(messages)
        completion = self.count_text(content)
        return {
            "content": content,
            "finish_reason": "stop",
            "usage": {
                "completion_tokens": completion,
                "prompt_tokens": prompt,
                "total_tokens": prompt + completion,
            },
        }
