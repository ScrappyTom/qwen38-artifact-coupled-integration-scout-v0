from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


TASK_ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((TASK_ROOT / "EVALUATOR.json").read_text(encoding="utf-8"))


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def citations(text: str) -> set[str]:
    return set(re.findall(r"\[(S(?:0[1-9]|1[0-4]))\]", text))


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", re.sub(r"\[S\d{2}\]", "", text)))


def composite_hash(ledger: bytes, decision: bytes) -> str:
    manifest = {
        "BOUNDED_AGENT_ARCHITECTURE_DECISION.md": sha256(decision),
        "EVIDENCE_INTEGRATION_LEDGER.md": sha256(ledger),
    }
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded)


def criterion(criterion_id: str, passed: bool, description: str) -> dict[str, str]:
    return {
        "criterion_id": criterion_id,
        "status": "pass" if passed else "fail",
        "description": description,
    }


def evaluate(candidate_root: Path) -> dict[str, Any]:
    ledger_path = candidate_root / "EVIDENCE_INTEGRATION_LEDGER.md"
    decision_path = candidate_root / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
    ledger_bytes = ledger_path.read_bytes()
    decision_bytes = decision_path.read_bytes()
    ledger = ledger_bytes.decode("utf-8")
    decision = decision_bytes.decode("utf-8")
    rows: list[dict[str, str]] = []

    rows.append(criterion("ledger_heading", ledger.startswith("# Evidence Integration Ledger"), "exact ledger heading"))
    ledger_requirements = set(re.findall(r"(?<![A-Za-z0-9])(R(?:0[1-9]|1[0-2]))(?![A-Za-z0-9])", ledger))
    missing_requirements = sorted(set(CONFIG["required_ledger_requirements"]) - ledger_requirements)
    rows.append(criterion("ledger_requirement_coverage", not missing_requirements, "missing: " + ", ".join(missing_requirements) if missing_requirements else "R01-R12 present"))
    ledger_sources = citations(ledger)
    rows.append(criterion("ledger_grounding", len(ledger_sources) >= 8, f"{len(ledger_sources)} distinct cited sources"))

    observed_headings = re.findall(r"(?m)^## ([^\r\n]+)\s*$", decision)
    rows.append(criterion("decision_heading_order", observed_headings == CONFIG["decision_headings"], "exact ordered headings"))
    count = word_count(decision)
    low, high = CONFIG["decision_word_range"]
    rows.append(criterion("decision_word_range", low <= count <= high, f"word_count={count}; required={low}-{high}"))
    decision_sources = citations(decision)
    rows.append(criterion("decision_source_breadth", len(decision_sources) >= CONFIG["minimum_unique_sources"], f"{len(decision_sources)} distinct cited sources"))
    missing_sources = sorted(set(CONFIG["required_source_ids"]) - decision_sources)
    rows.append(criterion("required_sources", not missing_sources, "missing: " + ", ".join(missing_sources) if missing_sources else "all required sources cited"))

    semantic_gates = {
        "boundary_distinctions": ("capacity", "delivery", "effect uptake", "closure"),
        "residency_distinctions": ("recoverability", "residency", "working-set"),
        "economics": ("cache", "decision", "cost"),
        "semantic_risk": ("digest", "false closure", "control"),
        "ownership": ("host", "model", "demand"),
        "interaction_roadmap": ("interaction", "transfer", "stopping"),
        "governance": ("candidate", "readiness", "evaluation"),
        "falsifiers": ("fals", "uncert"),
    }
    lowered = decision.casefold()
    for gate, terms in semantic_gates.items():
        missing = [term for term in terms if term not in lowered]
        rows.append(criterion(gate, not missing, "missing terms: " + ", ".join(missing) if missing else "mechanical term gate passed"))

    blocking = [f"{row['criterion_id']}: {row['description']}" for row in rows if row["status"] != "pass"]
    mechanical_passed = not blocking
    if mechanical_passed:
        blocking.append("independent condition-blinded semantic adjudication required")
    return {
        "schema_version": "bounded-agent-architecture-evaluation-result-v0",
        "evaluator_id": CONFIG["evaluator_id"],
        "task_id": CONFIG["task_id"],
        "candidate_sha256": composite_hash(ledger_bytes, decision_bytes),
        "passed": False,
        "closure_readiness": "not_adjudicated" if mechanical_passed else "not_ready",
        "blocking_requirements": blocking,
        "criterion_results": rows,
        "mechanical_precheck_passed": mechanical_passed,
        "independent_adjudication_supplied": False,
        "decision_word_count": count,
        "decision_source_ids": sorted(decision_sources),
        "ledger_source_ids": sorted(ledger_sources),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.candidate_root), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
