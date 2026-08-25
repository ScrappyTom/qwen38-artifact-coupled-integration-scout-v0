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
    return set(re.findall(r"\[(S(?:0[1-9]|1[0-6]))\]", text))


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’-]+\b", re.sub(r"\[S\d{2}\]", "", text)))


def composite_hash(ledger: bytes, decision: bytes) -> str:
    manifest = {
        "BOUNDED_AGENT_ARCHITECTURE_DECISION.md": sha256(decision),
        "EVIDENCE_INTEGRATION_LEDGER.md": sha256(ledger),
    }
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded)


def criterion(criterion_id: str, passed: bool, description: str) -> dict[str, str]:
    return {
        "criterion_id": criterion_id,
        "status": "pass" if passed else "fail",
        "description": description,
    }


def evaluate(candidate_root: Path) -> dict[str, Any]:
    ledger_bytes = (candidate_root / "EVIDENCE_INTEGRATION_LEDGER.md").read_bytes()
    decision_bytes = (
        candidate_root / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
    ).read_bytes()
    ledger = ledger_bytes.decode("utf-8")
    decision = decision_bytes.decode("utf-8")
    combined = ledger + "\n" + decision
    lowered = decision.casefold()
    rows: list[dict[str, str]] = []

    rows.append(
        criterion(
            "ledger_heading",
            ledger.startswith("# Evidence Integration Ledger"),
            "exact ledger heading",
        )
    )
    requirements = set(
        re.findall(r"(?<![A-Za-z0-9])(R(?:0[1-9]|1[0-2]))(?![A-Za-z0-9])", ledger)
    )
    missing_requirements = sorted(
        set(CONFIG["required_ledger_requirements"]) - requirements
    )
    rows.append(
        criterion(
            "ledger_requirement_coverage",
            not missing_requirements,
            "R01-R12 present"
            if not missing_requirements
            else "missing: " + ", ".join(missing_requirements),
        )
    )
    ledger_sources = citations(ledger)
    rows.append(
        criterion(
            "ledger_grounding",
            len(ledger_sources) >= 9,
            f"{len(ledger_sources)} distinct cited sources",
        )
    )

    rows.append(
        criterion(
            "decision_title",
            decision.startswith(CONFIG["decision_title"]),
            "exact decision title",
        )
    )
    headings = re.findall(r"(?m)^## ([^\r\n]+)\s*$", decision)
    rows.append(
        criterion(
            "decision_heading_order",
            headings == CONFIG["decision_headings"],
            "exact ordered headings",
        )
    )
    count = word_count(decision)
    low, high = CONFIG["decision_word_range"]
    rows.append(
        criterion(
            "decision_word_range",
            low <= count <= high,
            f"word_count={count}; required={low}-{high}",
        )
    )
    decision_sources = citations(decision)
    rows.append(
        criterion(
            "decision_source_breadth",
            len(decision_sources) >= CONFIG["minimum_unique_sources"],
            f"{len(decision_sources)} distinct cited sources",
        )
    )
    missing_sources = sorted(set(CONFIG["required_source_ids"]) - decision_sources)
    rows.append(
        criterion(
            "required_sources",
            not missing_sources,
            "all required sources cited"
            if not missing_sources
            else "missing: " + ", ".join(missing_sources),
        )
    )

    for gate, terms in CONFIG["semantic_term_gates"].items():
        missing = [term for term in terms if term.casefold() not in lowered]
        rows.append(
            criterion(
                gate,
                not missing,
                "mechanical relation gate passed"
                if not missing
                else "missing terms: " + ", ".join(missing),
            )
        )

    combined_folded = combined.casefold()
    for gate, patterns in CONFIG["forbidden_relation_patterns"].items():
        present = [pattern for pattern in patterns if pattern.casefold() in combined_folded]
        rows.append(
            criterion(
                gate,
                not present,
                "no prohibited relation conversion"
                if not present
                else "prohibited: " + ", ".join(present),
            )
        )

    blocking = [
        f"{row['criterion_id']}: {row['description']}"
        for row in rows
        if row["status"] != "pass"
    ]
    mechanical_passed = not blocking
    return {
        "schema_version": "bluehaven-water-evaluation-result-v0",
        "evaluator_id": CONFIG["evaluator_id"],
        "task_id": CONFIG["task_id"],
        "candidate_sha256": composite_hash(ledger_bytes, decision_bytes),
        "passed": mechanical_passed,
        "closure_readiness": "not_adjudicated" if mechanical_passed else "not_ready",
        "blocking_requirements": blocking,
        "criterion_results": rows,
        "mechanical_precheck_passed": mechanical_passed,
        "independent_adjudication_supplied": False,
        "external_readiness_adjudication_required": True,
        "decision_word_count": count,
        "decision_source_ids": sorted(decision_sources),
        "ledger_source_ids": sorted(ledger_sources),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_root", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            evaluate(args.candidate_root),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
