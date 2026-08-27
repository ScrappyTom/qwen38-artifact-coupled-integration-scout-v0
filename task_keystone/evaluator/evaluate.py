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
    alternatives = "|".join(re.escape(value) for value in CONFIG["source_ids"])
    return set(re.findall(rf"\[({alternatives})\]", text))


def word_count(text: str) -> int:
    alternatives = "|".join(re.escape(value) for value in CONFIG["source_ids"])
    stripped = re.sub(rf"\[(?:{alternatives})\]", "", text)
    return len(re.findall(r"\b[\w’-]+\b", stripped))


def composite_hash(ledger: bytes, decision: bytes) -> str:
    manifest = {
        "BOUNDED_AGENT_ARCHITECTURE_DECISION.md": sha256(decision),
        "EVIDENCE_INTEGRATION_LEDGER.md": sha256(ledger),
    }
    return sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    )


def criterion(
    criterion_id: str,
    passed: bool,
    description: str,
    *,
    expected: str | None = None,
    observed: str | None = None,
) -> dict[str, str]:
    row = {
        "criterion_id": criterion_id,
        "status": "pass" if passed else "fail",
        "description": description,
    }
    if expected is not None:
        row["expected"] = expected
    if observed is not None:
        row["observed"] = observed
    return row


def unnegated_occurrences(text: str, phrase: str) -> list[str]:
    present: list[str] = []
    for match in re.finditer(re.escape(phrase), text, re.IGNORECASE):
        prefix = text[max(0, match.start() - 32) : match.start()].casefold()
        if re.search(r"(?:\bnot\b|\bnever\b|\brather than\b|\bmust not\b)\W*$", prefix):
            continue
        present.append(match.group(0))
    return present


def relation_gate(
    criterion_id: str, spec: dict[str, Any], text: str
) -> dict[str, str]:
    missing = [
        pattern
        for pattern in spec["patterns"]
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL) is None
    ]
    return criterion(
        criterion_id,
        not missing,
        "required relationship supported"
        if not missing
        else f"missing relation patterns: {len(missing)}",
        expected=str(spec["expected"]),
        observed="all required relation patterns found"
        if not missing
        else "missing: " + " | ".join(missing),
    )


def evaluate(candidate_root: Path) -> dict[str, Any]:
    ledger_bytes = (candidate_root / "EVIDENCE_INTEGRATION_LEDGER.md").read_bytes()
    decision_bytes = (
        candidate_root / "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"
    ).read_bytes()
    ledger = ledger_bytes.decode("utf-8")
    decision = decision_bytes.decode("utf-8")
    combined = ledger + "\n" + decision
    rows: list[dict[str, str]] = []

    rows.append(
        criterion(
            "ledger_heading",
            ledger.startswith(CONFIG["ledger_title"] + "\n"),
            "exact task-native ledger heading",
            expected=CONFIG["ledger_title"],
            observed=ledger.splitlines()[0] if ledger.splitlines() else "",
        )
    )
    rows.append(
        criterion(
            "ledger_source_breadth",
            len(citations(ledger)) >= CONFIG["minimum_ledger_sources"],
            f"{len(citations(ledger))} distinct cited sources",
        )
    )
    rows.append(
        criterion(
            "decision_title",
            decision.startswith(CONFIG["decision_title"]),
            "exact decision title",
            expected=CONFIG["decision_title"],
            observed=decision.splitlines()[0] if decision.splitlines() else "",
        )
    )
    headings = re.findall(r"(?m)^## ([^\r\n]+)\s*$", decision)
    rows.append(
        criterion(
            "decision_heading_order",
            headings == CONFIG["decision_headings"],
            "exact ordered level-two headings",
            expected=" | ".join(CONFIG["decision_headings"]),
            observed=" | ".join(headings),
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
    rows.append(
        criterion(
            "decision_source_breadth",
            len(citations(decision)) >= CONFIG["minimum_unique_sources"],
            f"{len(citations(decision))} distinct cited sources",
        )
    )
    for gate, spec in CONFIG["relation_requirements"].items():
        rows.append(relation_gate(gate, spec, decision))

    folded = combined.casefold()
    for gate, patterns in CONFIG["forbidden_relation_patterns"].items():
        present = [pattern for pattern in patterns if pattern.casefold() in folded]
        rows.append(
            criterion(
                gate,
                not present,
                "no prohibited relation conversion"
                if not present
                else "prohibited: " + ", ".join(present),
                expected="none",
                observed=", ".join(present) if present else "none",
            )
        )
    for gate, patterns in CONFIG["negation_aware_forbidden_patterns"].items():
        present = [
            match
            for pattern in patterns
            for match in unnegated_occurrences(combined, pattern)
        ]
        rows.append(
            criterion(
                gate,
                not present,
                "no unnegated prohibited relation conversion"
                if not present
                else "prohibited: " + ", ".join(present),
                expected="none",
                observed=", ".join(present) if present else "none",
            )
        )

    blocking = [
        f"{row['criterion_id']}: {row['description']} | expected={row.get('expected', '')} | observed={row.get('observed', '')}"
        for row in rows
        if row["status"] != "pass"
    ]
    passed = not blocking
    return {
        "schema_version": "keystone-rail-evaluation-result-v0",
        "evaluator_id": CONFIG["evaluator_id"],
        "task_id": CONFIG["task_id"],
        "candidate_sha256": composite_hash(ledger_bytes, decision_bytes),
        "passed": passed,
        "closure_readiness": "not_adjudicated" if passed else "not_ready",
        "blocking_requirements": blocking,
        "criterion_results": rows,
        "mechanical_precheck_passed": passed,
        "independent_adjudication_supplied": False,
        "external_readiness_adjudication_required": True,
        "decision_word_count": count,
        "decision_source_ids": sorted(citations(decision)),
        "ledger_source_ids": sorted(citations(ledger)),
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
