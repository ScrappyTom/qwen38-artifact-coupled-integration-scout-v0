from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json
from tools.materialize_trellis_world import SPECS, document


TASK = ROOT / "task_trellis"
SOURCE_ROOT = TASK / "sources"
TASK_ID = "trellis-heat-continuity-decision-v0"
ACTIVATION_MIN_LINES = 48


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
        custody.append({**row, "origin": "deterministic_synthetic_trellis_heat_world_v0", "generator": "tools/materialize_trellis_world.py"})
    write_json(TASK / "SOURCE_CATALOG.json", {"schema": "trellis-source-catalog-v0", "sources": sources})
    governed = [
        "ACTIONS.md", "VERIFICATION_ACTIONS.md", "EVALUATOR.json", "SOURCE_CATALOG.json",
        "SYSTEM.md", "TASK.md", "WORLD_SPEC.json", "evaluator/evaluate.py",
        "candidate/EVIDENCE_INTEGRATION_LEDGER.md",
        "candidate/BOUNDED_AGENT_ARCHITECTURE_DECISION.md",
        *[f"sources/{spec.filename}" for spec in SPECS],
    ]
    write_json(
        TASK / "TASK_SOURCE_LOCK.json",
        {
            "schema": "trellis-task-source-lock-v0",
            "task_id": TASK_ID,
            "world_origin": "deterministic_synthetic_trellis_heat_world_v0",
            "source_custody": custody,
            "files": [
                {"path": relative, "sha256": sha256_file(TASK / relative), "size_bytes": (TASK / relative).stat().st_size}
                for relative in sorted(governed)
            ],
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
