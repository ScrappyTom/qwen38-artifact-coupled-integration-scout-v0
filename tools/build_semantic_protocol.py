from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json


CRITERIA = (
    ("R01", "Does the package distinguish recommendation, legal order, execution, checking, and closure authority, including acknowledged command transfer?"),
    ("R02", "Does it use the conservative fire/weather envelope, bind one forecast revision, state expiry, and define explicit advance, hold, and expansion triggers?"),
    ("R03", "Does it use a time-bound population basis, preserve overlap and survey uncertainty, account for tourists, and derive clearance demand without double counting?"),
    ("R04", "Does it model Mill Junction as the shared bottleneck, use observed exercise throughput, preserve inbound access, and specify contraflow and route-loss effects?"),
    ("R05", "Does it match people and accommodations to staffed vehicles, duty limits, cycle times, accessible capacity, route constraints, and relief capacity?"),
    ("R06", "Does it use smoke-safe staffed shelter capacity and exact medical/accessibility placement, power, filtration, handoff, and relocation rules?"),
    ("R07", "Does it provide redundant multilingual warning, door-knock timing, delivery/understanding evidence, radio interoperability, and one consistent zone revision?"),
    ("R08", "Does it use the observed fuel delay, stage at least twenty-four hours locally or provide an equivalent diversified control, and carry coupled power/fuel effects?"),
    ("R09", "Does it distinguish pets, livestock, and service animals and run a parallel plan that does not delay humans or double-count shared routes/capacity?"),
    ("R10", "Does it define private accountability, aggregate public reporting, verified self-evacuation, restricted medical data, reconciliation, retention, and deletion proof?"),
    ("R11", "Is the forty-eight-hour plan ordered, owned, effect-aware, resource- and cost-bound, checked, repairable, rechecked, and contingently executable?"),
    ("R12", "Does it preserve every material exercise/readiness blocker, bind evidence to the current candidate, distinguish readiness states, and give concrete falsifiers?"),
)


def main() -> int:
    write_json(
        ROOT / "SEMANTIC_ADJUDICATION_PROTOCOL_TRANSFER.json",
        {
            "schema_version": "cedar-semantic-adjudication-protocol-v0",
            "task_id": "cedar-valley-evacuation-decision-package-v0",
            "evaluator_id": "cedar-evacuation-semantic-adjudicator-v0",
            "task_source_lock_sha256": sha256_file(ROOT / "task" / "TASK_SOURCE_LOCK.json"),
            "mechanical_evaluator_sha256": sha256_file(ROOT / "task" / "evaluator" / "evaluate.py"),
            "world_spec_sha256": sha256_file(ROOT / "task" / "WORLD_SPEC.json"),
            "candidate_binding": "Exact composite SHA-256 and task-source-lock SHA-256 are required before adjudication.",
            "condition_masking": "Candidates receive hash-derived neutral labels; arm mapping is applied only after criterion dispositions are frozen.",
            "evidence_rule": "Adjudication uses only the frozen task sources and task contract. Unsupported but plausible emergency-management claims count as defects.",
            "criteria": [{"id": key, "question": question} for key, question in CRITERIA],
            "criterion_statuses": ["met", "partial", "not_met"],
            "quality_classes": ["complete", "strong_partial", "weak_partial", "failed"],
            "readiness_values": ["ready", "not_ready"],
            "readiness_rule": "ready requires the mechanical precheck, all R01-R12 met, no unsupported source claim, no forbidden shortcut, no unresolved blocking requirement, and a current candidate-bound final check. Submission behavior never changes this rule.",
            "useful_completion_rule": "artifact quality complete AND readiness ready AND closure appropriate AND the final relevant effect is delivered or independently reconciled",
            "supersession_rule": "Any prior disposition for the same candidate/task/evidence/rubric binding remains append-only and must be explicitly superseded if corrected.",
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
