from __future__ import annotations

# ruff: noqa: E402

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json
from tools.materialize_solace_world import SPECS, document


TASK = ROOT / "task_solace"
SOURCE_ROOT = TASK / "sources"
TASK_ID = "solace-water-recovery-decision-v0"
ACTIVATION_MIN_LINES = 50


def main() -> int:
    sources = []
    custody = []
    for spec in SPECS:
        path = SOURCE_ROOT / spec.filename
        if not path.is_file() or path.read_text(encoding="utf-8") != document(spec):
            raise RuntimeError(f"materialized source differs from generator: {spec.source_id}")
        relative = str(path.relative_to(TASK)).replace("\\", "/")
        row = {
            "source_id": spec.source_id,
            "title": spec.title,
            "evidence_domain": spec.domain,
            "activation_min_lines": ACTIVATION_MIN_LINES,
            "path": relative,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "line_count": len(path.read_text(encoding="utf-8").splitlines()),
        }
        sources.append(row)
        custody.append(
            {
                **row,
                "origin": "deterministic_synthetic_solace_water_world_v0",
                "generator": "tools/materialize_solace_world.py",
                "generator_spec": spec.filename,
            }
        )
    write_json(TASK / "SOURCE_CATALOG.json", {"schema": "solace-source-catalog-v0", "sources": sources})
    governed = [
        "ACTIONS.md",
        "EVALUATOR.json",
        "SOURCE_CATALOG.json",
        "SYSTEM.md",
        "TASK.md",
        "WORLD_SPEC.json",
        "evaluator/evaluate.py",
        "candidate/EVIDENCE_INTEGRATION_LEDGER.md",
        "candidate/BOUNDED_AGENT_ARCHITECTURE_DECISION.md",
        *[f"sources/{spec.filename}" for spec in SPECS],
    ]
    write_json(
        TASK / "TASK_SOURCE_LOCK.json",
        {
            "schema": "solace-task-source-lock-v0",
            "task_id": TASK_ID,
            "world_origin": "deterministic_synthetic_solace_water_world_v0",
            "source_custody": custody,
            "files": [
                {
                    "path": relative,
                    "sha256": sha256_file(TASK / relative),
                    "size_bytes": (TASK / relative).stat().st_size,
                }
                for relative in sorted(governed)
            ],
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
