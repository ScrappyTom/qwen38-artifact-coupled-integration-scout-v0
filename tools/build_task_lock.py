from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import sha256_file, write_json


TASK = ROOT / "task"
DONOR = Path("E:/bounded-context-experimental-program")
DONOR_COMMIT = "0dbfb151ba8f3bb9edef87879076eb1c6fe7cc78"

SOURCE_MAP = {
    "S01": ("FULL_EXPERIMENT_SEQUENCE_WRITEUP.md", "sources/S01_FULL_SEQUENCE.md"),
    "S02": ("PROGRAM_RECONCILIATION.md", "sources/S02_PROGRAM_RECONCILIATION.md"),
    "S03": ("SYSTEMS_INFORMATION_ECONOMICS.md", "sources/S03_INFORMATION_ECONOMICS.md"),
    "S04": ("EVIDENCE_LEDGER.md", "sources/S04_EVIDENCE_LEDGER.md"),
    "S05": ("E36_DECISION_GEOMETRY_AUDIT.md", "sources/S05_DECISION_GEOMETRY_AUDIT.md"),
    "S06": ("E38_INTERACTION_APPARATUS_DISPOSITION.md", "sources/S06_INTERACTION_APPARATUS_DISPOSITION.md"),
    "S07": ("E39_INGRESS_WORK_STAGE0_HANDOFF.md", "sources/S07_INGRESS_WORK_STAGE0.md"),
    "S08": ("E40_INGRESS_WORK_INTERACTION_RESULT.md", "sources/S08_INGRESS_WORK_RESULT.md"),
    "S09": ("MINIMAL_RUNTIME_POLICY_V0.md", "sources/S09_MINIMAL_RUNTIME_POLICY.md"),
    "S10": ("REACTIVE_RUNTIME_POLICY_V1.md", "sources/S10_REACTIVE_RUNTIME_POLICY.md"),
    "S11": ("CAPABILITY_TERRAIN_MAP.md", "sources/S11_CAPABILITY_TERRAIN.md"),
    "S12": ("DISCOVERY_TRANCHE_RESULT.md", "sources/S12_DISCOVERY_TRANCHE_RESULT.md"),
    "S13": ("audits/H05_ARTIFACT_DISPOSITION_RECONCILIATION.md", "sources/S13_H05_CORRECTION.md"),
    "S14": ("audits/NEXT_ROUTE_PRIOR_EVIDENCE_RECONCILIATION.md", "sources/S14_PRIOR_EVIDENCE_RECONCILIATION.md"),
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(DONOR), *args], text=True).strip()


def main() -> int:
    if git("rev-parse", DONOR_COMMIT) != DONOR_COMMIT:
        raise RuntimeError("frozen donor commit is unavailable")
    sources = []
    custody = []
    for source_id, (donor_path, local_path) in SOURCE_MAP.items():
        path = TASK / local_path
        donor_bytes = subprocess.check_output(["git", "-C", str(DONOR), "show", f"{DONOR_COMMIT}:{donor_path}"])
        if donor_bytes != path.read_bytes():
            raise RuntimeError(f"copied source differs from donor Git object: {source_id}")
        lines = path.read_text(encoding="utf-8").splitlines()
        title = next((line.lstrip("# ").strip() for line in lines if line.startswith("#")), path.stem)
        blob = git("rev-parse", f"{DONOR_COMMIT}:{donor_path}")
        row = {
            "source_id": source_id,
            "title": title,
            "path": local_path,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "line_count": len(lines),
        }
        sources.append(row)
        custody.append({**row, "donor_commit": DONOR_COMMIT, "donor_path": donor_path, "donor_blob": blob})
    write_json(TASK / "SOURCE_CATALOG.json", {"schema": "architecture-source-catalog-v0", "sources": sources})
    governed = ["TASK.md", "SYSTEM.md", "ACTIONS.md", "EVALUATOR.json", "evaluator/evaluate.py", "candidate/EVIDENCE_INTEGRATION_LEDGER.md", "candidate/BOUNDED_AGENT_ARCHITECTURE_DECISION.md", *[value[1] for value in SOURCE_MAP.values()]]
    write_json(TASK / "TASK_SOURCE_LOCK.json", {"schema": "architecture-task-source-lock-v0", "source_donor_commit": DONOR_COMMIT, "source_custody": custody, "files": [{"path": path, "sha256": sha256_file(TASK / path), "size_bytes": (TASK / path).stat().st_size} for path in sorted(governed)]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
