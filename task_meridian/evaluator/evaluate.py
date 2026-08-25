from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


TASK_ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((TASK_ROOT / "EVALUATOR.json").read_text(encoding="utf-8"))
SLOT_BEGIN = "<!-- SOURCE_SLOT_BEGIN -->"
SLOT_END = "<!-- SOURCE_SLOT_END -->"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def citations(text: str) -> set[str]:
    alternatives = "|".join(re.escape(value) for value in CONFIG["source_ids"])
    return set(re.findall(rf"\[({alternatives})\]", text))


def word_count(text: str) -> int:
    alternatives = "|".join(re.escape(value) for value in CONFIG["source_ids"])
    return len(re.findall(r"\b[\w’-]+\b", re.sub(rf"\[(?:{alternatives})\]", "", text)))


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


def parse_slots(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    slots: list[dict[str, Any]] = []
    failures: list[str] = []
    cursor = text.find(SLOT_BEGIN)
    while cursor >= 0:
        metadata_start = cursor + len(SLOT_BEGIN)
        metadata_end = text.find("\n", metadata_start)
        end = text.find(SLOT_END, metadata_end + 1)
        if metadata_end < 0 or end < 0:
            failures.append("malformed source slot markers")
            break
        try:
            metadata = json.loads(text[metadata_start:metadata_end].strip())
        except (ValueError, TypeError) as exc:
            failures.append(f"slot metadata parse: {type(exc).__name__}")
            break
        body = text[metadata_end + 1 : end].strip()
        if metadata.get("schema") != "source-slot-record-v0":
            failures.append("slot schema")
        if metadata.get("source_id") not in CONFIG["source_ids"]:
            failures.append("slot source id")
        if metadata.get("body_sha256") != sha256(body.encode("utf-8")):
            failures.append("slot body hash")
        expected_requirements = sorted(set(re.findall(r"\bQ(?:0[1-9]|1[0-2])\b", body)))
        if metadata.get("requirement_ids") != expected_requirements:
            failures.append("slot requirement binding")
        slots.append({**metadata, "body": body})
        cursor = text.find(SLOT_BEGIN, end + len(SLOT_END))
    if len({row.get("source_id") for row in slots}) != len(slots):
        failures.append("duplicate source slots")
    return slots, failures


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
            "register_heading",
            ledger.startswith("# Source Evidence Register\n"),
            "exact source register heading",
        )
    )
    slots, slot_failures = parse_slots(ledger)
    rows.append(
        criterion(
            "register_slot_integrity",
            not slot_failures,
            "source slots mechanically valid" if not slot_failures else "; ".join(slot_failures),
        )
    )
    rows.append(
        criterion(
            "register_source_breadth",
            len(slots) >= CONFIG["minimum_source_slots"],
            f"source_slots={len(slots)}; minimum={CONFIG['minimum_source_slots']}",
        )
    )
    requirements = set(re.findall(r"\bQ(?:0[1-9]|1[0-2])\b", ledger))
    missing_requirements = sorted(set(CONFIG["required_ledger_requirements"]) - requirements)
    rows.append(
        criterion(
            "register_requirement_coverage",
            not missing_requirements,
            "Q01-Q12 present" if not missing_requirements else "missing: " + ", ".join(missing_requirements),
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

    for gate, terms in CONFIG["semantic_term_gates"].items():
        missing = [term for term in terms if term.casefold() not in lowered]
        rows.append(
            criterion(
                gate,
                not missing,
                "mechanical relation gate passed" if not missing else "missing terms: " + ", ".join(missing),
            )
        )

    combined_folded = combined.casefold()
    for gate, patterns in CONFIG["forbidden_relation_patterns"].items():
        present = [pattern for pattern in patterns if pattern.casefold() in combined_folded]
        rows.append(
            criterion(
                gate,
                not present,
                "no prohibited relation conversion" if not present else "prohibited: " + ", ".join(present),
            )
        )

    blocking = [
        f"{row['criterion_id']}: {row['description']}"
        for row in rows
        if row["status"] != "pass"
    ]
    mechanical_passed = not blocking
    return {
        "schema_version": "meridian-infusion-evaluation-result-v0",
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
        "register_source_ids": sorted(str(row.get("source_id")) for row in slots),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.candidate_root), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
