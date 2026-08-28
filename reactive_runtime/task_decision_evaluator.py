"""Config-driven evaluator for two-file evidence/decision tasks."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _citations(text: str, source_ids: list[str]) -> set[str]:
    alternatives = "|".join(re.escape(value) for value in source_ids)
    return set(re.findall(rf"\[({alternatives})\]", text))


def _word_count(text: str, source_ids: list[str]) -> int:
    alternatives = "|".join(re.escape(value) for value in source_ids)
    stripped = re.sub(rf"\[(?:{alternatives})\]", "", text)
    return len(re.findall(r"\b[\w’-]+\b", stripped))


def _criterion(
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


def _unnegated_occurrences(text: str, phrase: str) -> list[str]:
    present: list[str] = []
    for match in re.finditer(re.escape(phrase), text, re.IGNORECASE):
        prefix = text[max(0, match.start() - 32) : match.start()].casefold()
        if re.search(r"(?:\bnot\b|\bnever\b|\brather than\b|\bmust not\b)\W*$", prefix):
            continue
        present.append(match.group(0))
    return present


def _relation_gate(
    criterion_id: str, spec: dict[str, Any], text: str
) -> dict[str, str]:
    missing = [
        pattern
        for pattern in spec["patterns"]
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL) is None
    ]
    return _criterion(
        criterion_id,
        not missing,
        "required relationship supported" if not missing else f"missing relation patterns: {len(missing)}",
        expected=str(spec["expected"]),
        observed="all required relation patterns found" if not missing else "missing: " + " | ".join(missing),
    )


def evaluate(task_root: Path, candidate_root: Path) -> dict[str, Any]:
    config = json.loads((task_root / "EVALUATOR.json").read_text(encoding="utf-8"))
    ledger_name = str(config.get("ledger_file", "EVIDENCE_INTEGRATION_LEDGER.md"))
    decision_name = str(config.get("decision_file", "BOUNDED_AGENT_ARCHITECTURE_DECISION.md"))
    ledger_bytes = (candidate_root / ledger_name).read_bytes()
    decision_bytes = (candidate_root / decision_name).read_bytes()
    ledger = ledger_bytes.decode("utf-8")
    decision = decision_bytes.decode("utf-8")
    combined = ledger + "\n" + decision
    source_ids = list(config["source_ids"])
    rows: list[dict[str, str]] = []

    rows.append(_criterion("ledger_heading", ledger.startswith(config["ledger_title"] + "\n"), "exact task-native ledger heading", expected=config["ledger_title"], observed=ledger.splitlines()[0] if ledger.splitlines() else ""))
    rows.append(_criterion("ledger_source_breadth", len(_citations(ledger, source_ids)) >= config["minimum_ledger_sources"], f"{len(_citations(ledger, source_ids))} distinct cited sources"))
    rows.append(_criterion("decision_title", decision.startswith(config["decision_title"]), "exact decision title", expected=config["decision_title"], observed=decision.splitlines()[0] if decision.splitlines() else ""))
    headings = re.findall(r"(?m)^## ([^\r\n]+)\s*$", decision)
    rows.append(_criterion("decision_heading_order", headings == config["decision_headings"], "exact ordered level-two headings", expected=" | ".join(config["decision_headings"]), observed=" | ".join(headings)))
    count = _word_count(decision, source_ids)
    low, high = config["decision_word_range"]
    rows.append(_criterion("decision_word_range", low <= count <= high, f"word_count={count}; required={low}-{high}"))
    rows.append(_criterion("decision_source_breadth", len(_citations(decision, source_ids)) >= config["minimum_unique_sources"], f"{len(_citations(decision, source_ids))} distinct cited sources"))
    for gate, spec in config["relation_requirements"].items():
        rows.append(_relation_gate(gate, spec, decision))

    folded = combined.casefold()
    for gate, patterns in config.get("forbidden_relation_patterns", {}).items():
        present = [pattern for pattern in patterns if pattern.casefold() in folded]
        rows.append(_criterion(gate, not present, "no prohibited relation conversion" if not present else "prohibited: " + ", ".join(present), expected="none", observed=", ".join(present) if present else "none"))
    for gate, patterns in config.get("negation_aware_forbidden_patterns", {}).items():
        present = [match for pattern in patterns for match in _unnegated_occurrences(combined, pattern)]
        rows.append(_criterion(gate, not present, "no unnegated prohibited relation conversion" if not present else "prohibited: " + ", ".join(present), expected="none", observed=", ".join(present) if present else "none"))

    blocking = [
        f"{row['criterion_id']}: {row['description']} | expected={row.get('expected', '')} | observed={row.get('observed', '')}"
        for row in rows if row["status"] != "pass"
    ]
    manifest = {decision_name: _sha256(decision_bytes), ledger_name: _sha256(ledger_bytes)}
    candidate_sha256 = _sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())
    passed = not blocking
    return {
        "schema_version": str(config["schema_version"]) + "-result",
        "evaluator_id": config["evaluator_id"],
        "task_id": config["task_id"],
        "candidate_sha256": candidate_sha256,
        "passed": passed,
        "closure_readiness": "not_adjudicated" if passed else "not_ready",
        "blocking_requirements": blocking,
        "criterion_results": rows,
        "mechanical_precheck_passed": passed,
        "independent_adjudication_supplied": False,
        "external_readiness_adjudication_required": True,
        "decision_word_count": count,
        "decision_source_ids": sorted(_citations(decision, source_ids)),
        "ledger_source_ids": sorted(_citations(ledger, source_ids)),
    }
