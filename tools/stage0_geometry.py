from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import write_json
from reactive_runtime.qualification import build_action_cases, build_cases
from reactive_runtime.trajectory_budget import ConstructionBudget
from reactive_runtime.world import ArchitectureWorld
from tools.offline_tokenizer import OfflineTokenizer


def main() -> int:
    tokenizer = OfflineTokenizer()
    with tempfile.TemporaryDirectory() as temporary:
        world = ArchitectureWorld(ROOT / "task", Path(temporary))
        base_messages = [
            {"role": "system", "content": (ROOT / "task" / "SYSTEM.md").read_text(encoding="utf-8")},
            {"role": "user", "content": (ROOT / "task" / "TASK.md").read_text(encoding="utf-8") + "\n\n" + (ROOT / "task" / "ACTIONS.md").read_text(encoding="utf-8") + "\n\n" + world.source_catalog_for_actor() + "\n\n" + world.candidate_packet()},
        ]
        base_prompt = tokenizer.count_messages(base_messages)
        source_rows = []
        for source_id, source in world.sources.items():
            source_rows.append({"source_id": source_id, "tokens": tokenizer.count_text(source.path.read_text(encoding="utf-8")), "bytes": source.size_bytes, "lines": len(source.lines)})
        cases = [{"case_id": case.case_id, "prompt_tokens": tokenizer.count_messages(case.messages), "headroom_after_max_completion": 25088 - tokenizer.count_messages(case.messages) - 1900} for case in build_cases(ROOT)]
        action_cases = [{"case_id": case.case_id, "prompt_tokens": tokenizer.count_messages(case.messages), "headroom_after_max_completion": 25088 - tokenizer.count_messages(case.messages) - 4096} for case in build_action_cases(ROOT)]
    result = {
        "schema": "northstar-transfer-stage0-geometry-v0",
        "task_id": "northstar-migration-architecture-package-v0",
        "base_actor_prompt_tokens": base_prompt,
        "source_corpus_tokens": sum(row["tokens"] for row in source_rows),
        "source_rows": source_rows,
        "maintenance_qualification_cases": cases,
        "action_qualification_cases": action_cases,
        "task_declared_minimum_distinct_sources": 10,
        "minimum_batch_actions_to_touch_ten_sources": 4,
        "trajectory_budget": {
            **ConstructionBudget().as_dict(),
            "clean_postconstruction_path_calls": 4,
            "clean_path": [
                "receive construction effect and run current-candidate check",
                "receive check and repair exact candidate",
                "receive repair effect and rerun check",
                "receive current recheck and propose closure",
            ],
            "additional_error_or_repair_allowance_calls": 4,
        },
        "activation_qualified": False,
        "activation_blocker": "A live ordinary screening trajectory must demonstrate authentic pressure; accessible-world size is not treated as realized context pressure.",
        "measured_gpu_authorized": False,
    }
    write_json(ROOT / "STAGE0_GEOMETRY.json", result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
