from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json
from tools.materialize_transfer_world import SOURCES


TASK = ROOT / "task"
SOURCE_ROOT = TASK / "transfer_sources"
SOURCE_TITLES = {
    "S01": "Northstar topology and migration target",
    "S02": "Northstar service objectives and traffic evidence",
    "S03": "Delivery, acknowledgement, and idempotency contract",
    "S04": "Schema compatibility and rollback boundaries",
    "S05": "Rollout, hold, and rollback policy",
    "S06": "Incident E-17: delayed replay and duplicate storm",
    "S07": "Incident E-23: EU residency failover violation",
    "S08": "Incident E-31: dependency outage beyond SLA",
    "S09": "Tail-latency and cohort telemetry review",
    "S10": "Shadow reconciliation and data-integrity audit",
    "S11": "Security, privacy, retention, and audit controls",
    "S12": "Capacity, spool, and migration cost model",
    "S13": "Vendor service objective and support history",
    "S14": "Independent migration readiness review",
}


def main() -> int:
    expected_names = list(SOURCES)
    sources = []
    custody = []
    for ordinal, name in enumerate(expected_names, start=1):
        source_id = f"S{ordinal:02d}"
        path = SOURCE_ROOT / name
        if not path.is_file():
            raise RuntimeError(f"missing materialized source: {name}")
        expected = SOURCES[name]()
        if path.read_text(encoding="utf-8") != expected:
            raise RuntimeError(f"materialized source differs from generator: {source_id}")
        relative = str(path.relative_to(TASK)).replace("\\", "/")
        row = {
            "source_id": source_id,
            "title": SOURCE_TITLES[source_id],
            "path": relative,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "line_count": len(path.read_text(encoding="utf-8").splitlines()),
        }
        sources.append(row)
        custody.append(
            {
                **row,
                "origin": "deterministic_synthetic_northstar_world_v0",
                "generator": "tools/materialize_transfer_world.py",
                "generator_function": SOURCES[name].__name__,
            }
        )

    write_json(
        TASK / "SOURCE_CATALOG.json",
        {"schema": "northstar-source-catalog-v0", "sources": sources},
    )
    governed = [
        "ACTIONS.md",
        "EVALUATOR.json",
        "SYSTEM.md",
        "TASK.md",
        "WORLD_SPEC.json",
        "evaluator/evaluate.py",
        "candidate/EVIDENCE_INTEGRATION_LEDGER.md",
        "candidate/BOUNDED_AGENT_ARCHITECTURE_DECISION.md",
        *[f"transfer_sources/{name}" for name in expected_names],
    ]
    write_json(
        TASK / "TASK_SOURCE_LOCK.json",
        {
            "schema": "northstar-task-source-lock-v0",
            "task_id": "northstar-migration-architecture-package-v0",
            "world_origin": "deterministic_synthetic_northstar_world_v0",
            "source_custody": custody,
            "files": [
                {
                    "path": path,
                    "sha256": sha256_file(TASK / path),
                    "size_bytes": (TASK / path).stat().st_size,
                }
                for path in sorted(governed)
            ],
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
