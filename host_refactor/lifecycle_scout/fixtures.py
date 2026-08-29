from __future__ import annotations

from typing import Any, Callable, Mapping

from host_refactor.lifecycle_scout.adapter import LifecycleScoutAdapter
from interaction_scout.fixtures import decision
from reactive_runtime.canonical import canonical_json_text, sha256_bytes
from reactive_runtime.verification_causal_frame import section_spans


FINAL_HEADING = "Execution, rollback, verification, and closure"


def milestone_section() -> str:
    return (
        "Execution proceeds through named owners, recorded prerequisites, reversible "
        "controls, candidate-bound checks, and an independent closure decision. The "
        "current decision remains incomplete until a check exposes every blocking "
        "requirement and the changed candidate is checked again. Evidence remains "
        "available from [COUNCIL] [CLIMATE] [GRID] [WATER] [CLINIC] [SHELTER] "
        "[TRANSIT] [COMMS] [SUPPLY] [LABOR] [LINEAGE] [REVIEW]. "
        "The exact candidate remains the durable work state. [LINEAGE] [REVIEW]"
    )


def repaired_section() -> str:
    return " ".join(
        (
            "The emergency manager activates limited operations; the health commissioner "
            "authorizes the citywide heat-health emergency; and the continuity director "
            "closes only after current evidence. A successful mechanical check is not "
            "authority and does not authorize closure. [COUNCIL] [REVIEW]",
            "The 31.4 degrees observation is evaluated against the 30.0 degrees limited "
            "gate for two consecutive windows; expanded operation uses 32.0 degrees. "
            "The 0.62 forecast probability is distinct from 84 percent station coverage. "
            "[CLIMATE] [LINEAGE]",
            "Power distinguishes 31.0 megawatts installed from 24.5 megawatts usable. "
            "The observed 12.6 kilovolts must remain within 12.2 to 12.9 at every node "
            "for three consecutive 15-minute windows. Backup is 8.4 megawatts for 16 "
            "hours emergency load versus 9 hours full load. [GRID]",
            "Water records 38 psi observed and at least 35 psi at every node for three "
            "consecutive 10-minute windows. Reserve is 1.6 million liters versus 0.19 "
            "million liters per hour. [WATER]",
            "Clinical occupancy is 71 percent against 82 percent for two consecutive "
            "windows, with twelve staffed cooling beds. Shelter distinguishes 2,400 "
            "seats installed from 1,760 seats staffed and accessible. [CLINIC] [SHELTER]",
            "Transit has twenty-two of twenty-six shuttles plus four accessible vehicles; "
            "the median is 26 minutes and p95 is 44 minutes. Communications delivery is "
            "89 percent, leaving 11 percent uncertainty; latency is 680 ms p95 and 1,140 "
            "ms p99. [TRANSIT] [COMMS]",
            "Fuel supports 16 hours emergency load versus 9 hours full load. Inventory "
            "distinguishes 2.8 operating days from 3.6 clinic-days. Labor requires twelve "
            "hours off after ten consecutive hours, with twenty-six drivers and ten "
            "interpreters. [SUPPLY] [LABOR]",
            "Candidate T9 binds F6, G4, R8, L11, and C7. T8 remains historical unless "
            "transferred and rechecked. Independent acceptance by an authorized owner is "
            "required before closure. [LINEAGE] [REVIEW]",
        )
    )


def bound_section_repair(
    adapter: LifecycleScoutAdapter, heading: str
) -> dict[str, Any]:
    path = adapter.world.candidate_root / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
    current = path.read_text(encoding="utf-8")
    section = next(row for row in section_spans(current) if row["heading"] == heading)
    if heading == FINAL_HEADING:
        replacement = (
            f"## {FINAL_HEADING}\n\n"
            "Candidate T9 binds F6, G4, R8, L11, and C7. T8 remains historical "
            "unless transferred and rechecked. Independent acceptance by an authorized "
            "owner is required before closure. [LINEAGE] [REVIEW]\n"
        )
    else:
        target = decision(water_defect=False)
        target_section = next(
            row for row in section_spans(target) if row["heading"] == heading
        )
        replacement = target_section["text"]
    return {
        "action": "replace_artifact_section",
        "artifact_sha256": sha256_bytes(current.encode("utf-8")),
        "candidate_sha256": adapter.world.candidate_sha256,
        "expected_section_sha256": section["sha256"],
        "replacement_section": replacement,
        "section_heading": heading,
    }


class DonorLifecycleActorFixture:
    """Provider-free expression fixture for the migrated donor lifecycle."""

    def __init__(
        self,
        adapter: LifecycleScoutAdapter,
        count_messages: Callable[[list[dict[str, str]]], int],
        count_text: Callable[[str], int],
    ) -> None:
        self.adapter = adapter
        self.count_messages = count_messages
        self.count_text = count_text
        self.calls = 0

    def _action(self) -> dict[str, Any]:
        headings = tuple(self.adapter.world.decision_headings)
        actions: tuple[Callable[[], dict[str, Any]], ...] = (
            lambda: {
                "action": "upsert_decision_section",
                "heading": FINAL_HEADING,
                "body": milestone_section(),
            },
            lambda: {"action": "begin_verification"},
            lambda: {"action": "run_check"},
            *(lambda heading=heading: bound_section_repair(self.adapter, heading) for heading in headings),
            lambda: {"action": "run_check"},
            lambda: {"action": "submit"},
        )
        if self.calls >= len(actions):
            raise RuntimeError("donor lifecycle actor fixture exhausted")
        return actions[self.calls]()

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


class NoOpMaintenanceFixture:
    """A bound fallback that fails if unplanned maintenance is requested."""

    def __call__(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        del payload
        raise RuntimeError("unexpected_maintenance_call_in_provider_free_lifecycle")
