from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence

from reactive_runtime.canonical import sha256_bytes
from reactive_runtime.provenance_claims import (
    NON_AUTHORITATIVE_DERIVATIVE,
    OWNER_SOURCE_REPORTED,
    SOURCE_REPORTED_FACT,
    SOURCE_REPORTED_RELATIONSHIP,
    SOURCE_SLOT,
    ProvenanceClaimValidation,
    exact_span_sha256,
    validate_provenance_claim,
)
from reactive_runtime.records import ResultRecord


DELTA_PREFIX = "# Provenance-local relational delta"
REGISTER_PREFIX = "# Provenance-local source register"
CLAIM_HEADING = re.compile(r"(?m)^## CLAIM ([A-Z][A-Z0-9_-]{2,63})\s*$")
SOURCE_DELTA_TOKEN_BUDGET = 1_500
SOURCE_DELTA_PROVIDER_MAX_TOKENS = 1_800
SOURCE_SLOT_TOKEN_BUDGET = 650
REGISTER_TOKEN_BUDGET = 8_000
MAX_CLAIMS_PER_DELTA = 8
MAX_CLAIMS_PER_SOURCE = 4


@dataclass(frozen=True)
class RelationalClaim:
    claim_id: str
    source_id: str
    source_version: str
    evidence_result_id: str
    evidence_quote: str
    start_line: int
    end_line: int
    span_sha256: str
    assertion_mode: str
    referents: tuple[str, ...]
    statement: str
    body_tokens: int

    @property
    def stable_key(self) -> tuple[str, str, str]:
        return (self.source_id, self.source_version, self.claim_id)

    def render(self, *, include_derived_span_hash: bool = True) -> str:
        referents = ",".join(self.referents) if self.referents else "NONE"
        rows = [
            f"## CLAIM {self.claim_id}",
            f"SLOT_SOURCE: {self.source_id}",
            f"SOURCE_VERSION: {self.source_version}",
            f"EVIDENCE_RESULT: {self.evidence_result_id}",
            f"EVIDENCE_QUOTE: {self.evidence_quote}",
        ]
        if include_derived_span_hash:
            rows.extend(
                [
                    f"EVIDENCE_LINES: {self.start_line}-{self.end_line}",
                    f"EVIDENCE_SHA256: {self.span_sha256}",
                ]
            )
        rows.extend(
            [
                f"MODE: {self.assertion_mode}",
                f"ATTRIBUTION: {OWNER_SOURCE_REPORTED}",
                f"REFERENTS: {referents}",
                f"AUTHORITY: {NON_AUTHORITATIVE_DERIVATIVE}",
                f"STATEMENT: {self.statement}",
            ]
        )
        return "\n".join(rows)


@dataclass(frozen=True)
class RelationalDeltaValidation:
    valid: bool
    code: str
    output_tokens: int
    claims: tuple[RelationalClaim, ...]
    source_ids: tuple[str, ...]
    issues: tuple[str, ...]
    provenance: tuple[ProvenanceClaimValidation, ...]


def _field_map(block: str) -> tuple[dict[str, str], list[str]]:
    fields: dict[str, str] = {}
    issues: list[str] = []
    for line in block.splitlines()[1:]:
        if not line.strip():
            continue
        if ": " not in line:
            issues.append("claim_line_invalid")
            continue
        key, value = line.split(": ", 1)
        if key in fields:
            issues.append("claim_field_duplicate")
        fields[key] = value.strip()
    required = {
        "SLOT_SOURCE",
        "SOURCE_VERSION",
        "EVIDENCE_RESULT",
        "EVIDENCE_QUOTE",
        "MODE",
        "ATTRIBUTION",
        "REFERENTS",
        "AUTHORITY",
        "STATEMENT",
    }
    if set(fields) != required:
        issues.append("claim_fields_invalid")
    return fields, issues


def _segments_by_result(
    records: Sequence[ResultRecord],
) -> dict[str, tuple[dict[str, object], ...]]:
    result: dict[str, tuple[dict[str, object], ...]] = {}
    for record in records:
        raw = record.metadata.get("segments")
        rows = tuple(row for row in raw if isinstance(row, dict)) if isinstance(raw, list) else ()
        result[record.result_id] = rows
    return result


def validate_relational_delta(
    text: str,
    *,
    count_text: Callable[[str], int],
    source_catalog: Mapping[str, Mapping[str, object]],
    task_root: object,
    newly_externalized: Sequence[ResultRecord],
    current_source_versions: Mapping[str, str],
) -> RelationalDeltaValidation:
    """Validate carrier shape and mechanical provenance, never claim truth."""

    from pathlib import Path

    issues: list[str] = []
    tokens = count_text(text)
    if tokens > SOURCE_DELTA_TOKEN_BUDGET:
        issues.append("delta_token_budget_exceeded")
    if not text.startswith(DELTA_PREFIX + "\n"):
        issues.append("delta_prefix_invalid")
    matches = list(CLAIM_HEADING.finditer(text))
    if not 1 <= len(matches) <= MAX_CLAIMS_PER_DELTA:
        issues.append("claim_count_invalid")
    elif text[: matches[0].start()].strip() != DELTA_PREFIX:
        issues.append("delta_preamble_invalid")

    externalized_ids = {record.result_id for record in newly_externalized}
    segments = _segments_by_result(newly_externalized)
    admitted_versions: dict[str, str] = {}
    for record in newly_externalized:
        versions = record.metadata.get("source_versions")
        if isinstance(versions, dict):
            admitted_versions.update(
                (str(source_id), str(version))
                for source_id, version in versions.items()
            )
        else:
            source_id = record.metadata.get("source_id")
            version = record.metadata.get("source_sha256")
            if isinstance(source_id, str) and isinstance(version, str):
                admitted_versions[source_id] = version

    claims: list[RelationalClaim] = []
    provenance: list[ProvenanceClaimValidation] = []
    seen_ids: set[str] = set()
    per_source_counts: dict[str, int] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start() : end].strip()
        claim_id = match.group(1)
        fields, block_issues = _field_map(block)
        issues.extend(block_issues)
        if block_issues:
            continue
        if claim_id in seen_ids:
            issues.append("claim_id_duplicate")
        seen_ids.add(claim_id)
        source_id = fields["SLOT_SOURCE"]
        source_version = fields["SOURCE_VERSION"]
        evidence_result = fields["EVIDENCE_RESULT"]
        evidence_quote = fields["EVIDENCE_QUOTE"]
        catalog_row = source_catalog.get(source_id)
        matching_lines: list[int] = []
        if catalog_row is not None:
            source_path = Path(task_root) / str(catalog_row.get("path", ""))
            if source_path.is_file():
                matching_lines = [
                    line_number
                    for line_number, line in enumerate(
                        source_path.read_text(encoding="utf-8").splitlines(), start=1
                    )
                    if line == evidence_quote
                ]
        if len(matching_lines) != 1:
            issues.append("evidence_quote_not_unique_exact_line")
            continue
        start_line = end_line = matching_lines[0]
        referents = (
            ()
            if fields["REFERENTS"] == "NONE"
            else tuple(value.strip() for value in fields["REFERENTS"].split(",") if value.strip())
        )
        if evidence_result not in externalized_ids:
            issues.append("evidence_result_not_newly_externalized")
        segment_match = any(
            row.get("source_id") == source_id
            and isinstance(row.get("start_line"), int)
            and isinstance(row.get("end_line"), int)
            and int(row["start_line"]) <= start_line <= end_line <= int(row["end_line"])
            for row in segments.get(evidence_result, ())
        )
        if not segment_match:
            issues.append("evidence_span_not_in_result")
        span_sha256 = ""
        if catalog_row is not None:
            try:
                span_sha256 = exact_span_sha256(
                    Path(task_root) / str(catalog_row.get("path", "")),
                    start_line,
                    end_line,
                )
            except ValueError:
                issues.append("evidence_span_invalid")
        claim_map: dict[str, object] = {
            "claim_id": claim_id,
            "record_kind": SOURCE_SLOT,
            "slot": {"source_id": source_id, "source_version": source_version},
            "assertion_mode": fields["MODE"],
            "attribution": fields["ATTRIBUTION"],
            "authority": fields["AUTHORITY"],
            "referents": list(referents),
            "evidence": [
                {
                    "source_id": source_id,
                    "source_version": source_version,
                    "start_line": start_line,
                    "end_line": end_line,
                    "span_sha256": span_sha256,
                }
            ],
            "statement": fields["STATEMENT"],
        }
        check = validate_provenance_claim(
            claim_map,
            source_catalog=source_catalog,
            source_root=Path(task_root),
            admitted_source_versions=admitted_versions,
            current_source_versions=current_source_versions,
        )
        provenance.append(check)
        issues.extend(check.issues)
        claim = RelationalClaim(
            claim_id=claim_id,
            source_id=source_id,
            source_version=source_version,
            evidence_result_id=evidence_result,
            evidence_quote=evidence_quote,
            start_line=start_line,
            end_line=end_line,
            span_sha256=span_sha256,
            assertion_mode=fields["MODE"],
            referents=referents,
            statement=fields["STATEMENT"],
            body_tokens=count_text(block),
        )
        claims.append(claim)
        per_source_counts[source_id] = per_source_counts.get(source_id, 0) + 1

    for source_id, count in per_source_counts.items():
        if count > MAX_CLAIMS_PER_SOURCE:
            issues.append(f"source_claim_count_exceeded:{source_id}")
    for source_id in admitted_versions:
        if source_id not in per_source_counts:
            issues.append(f"externalized_source_unrepresented:{source_id}")
    for source_id in per_source_counts:
        source_tokens = sum(claim.body_tokens for claim in claims if claim.source_id == source_id)
        if source_tokens > SOURCE_SLOT_TOKEN_BUDGET:
            issues.append(f"source_slot_token_budget_exceeded:{source_id}")

    unique_issues = tuple(dict.fromkeys(issues))
    return RelationalDeltaValidation(
        valid=not unique_issues,
        code="accepted" if not unique_issues else unique_issues[0],
        output_tokens=tokens,
        claims=tuple(claims),
        source_ids=tuple(sorted(per_source_counts)),
        issues=unique_issues,
        provenance=tuple(provenance),
    )


@dataclass(frozen=True)
class ProvenanceRegister:
    """Current source/version records; exact historical deltas remain external."""

    claims: tuple[RelationalClaim, ...] = ()

    def merge(
        self,
        validation: RelationalDeltaValidation,
        *,
        current_source_versions: Mapping[str, str],
        count_text: Callable[[str], int],
    ) -> "ProvenanceRegister":
        if not validation.valid:
            raise ValueError(f"cannot merge invalid delta: {validation.issues}")
        replaced_sources = set(validation.source_ids)
        retained = tuple(
            claim
            for claim in self.claims
            if claim.source_id not in replaced_sources
            and current_source_versions.get(claim.source_id) == claim.source_version
        )
        merged = ProvenanceRegister(tuple(sorted((*retained, *validation.claims), key=lambda row: row.stable_key)))
        if count_text(merged.render()) > REGISTER_TOKEN_BUDGET:
            raise ValueError("register_token_budget_exceeded")
        return merged

    def for_sources(self, source_ids: Iterable[str]) -> "ProvenanceRegister":
        allowed = set(source_ids)
        return ProvenanceRegister(tuple(claim for claim in self.claims if claim.source_id in allowed))

    def render(self) -> str:
        if not self.claims:
            return REGISTER_PREFIX + "\n\nEMPTY\n"
        return REGISTER_PREFIX + "\n\n" + "\n\n".join(claim.render() for claim in self.claims) + "\n"

    def render_for_maintenance(self, source_ids: Iterable[str]) -> str:
        allowed = set(source_ids)
        claims = tuple(claim for claim in self.claims if claim.source_id in allowed)
        if not claims:
            return DELTA_PREFIX + "\n\nEMPTY\n"
        return DELTA_PREFIX + "\n" + "\n".join(
            claim.render(include_derived_span_hash=False) for claim in claims
        ) + "\n"

    @property
    def sha256(self) -> str:
        return sha256_bytes(self.render().encode("utf-8"))


def relational_delta_messages(
    *,
    task_text: str,
    register: ProvenanceRegister,
    newly_externalized: Sequence[ResultRecord],
    source_versions: Mapping[str, str],
) -> list[dict[str, str]]:
    source_ids: list[str] = []
    for record in newly_externalized:
        raw = record.metadata.get("source_ids")
        if isinstance(raw, list):
            source_ids.extend(str(value) for value in raw)
    source_ids = list(dict.fromkeys(source_ids))
    prior = register.render_for_maintenance(source_ids)
    exact = "\n\n".join(
        f"--- NEWLY EXTERNALIZED {record.result_id} ---\n{record.exact_content}"
        for record in newly_externalized
    )
    versions = "\n".join(f"{source_id}: {source_versions[source_id]}" for source_id in source_ids)
    instruction = f"""You are in a bounded semantic-maintenance mode. Produce only a replacement provenance-local delta for the newly externalized exact sources. Do not continue the task, judge readiness, or authorize closure.

Use this exact plain-text carrier once:
{DELTA_PREFIX}
## CLAIM <UNIQUE_ID>
SLOT_SOURCE: <one newly externalized source ID>
SOURCE_VERSION: <exact 64-hex version>
EVIDENCE_RESULT: <exact newly externalized RESULT ID>
EVIDENCE_QUOTE: <one exact complete single line copied from that source inside the result>
MODE: {SOURCE_REPORTED_FACT} or {SOURCE_REPORTED_RELATIONSHIP}
ATTRIBUTION: {OWNER_SOURCE_REPORTED}
REFERENTS: NONE or comma-separated exact source IDs literally present in the evidence span and statement
AUTHORITY: {NON_AUTHORITATIVE_DERIVATIVE}
STATEMENT: <one complete single-line source-attributed fact or relationship>

Emit 1..{MAX_CLAIMS_PER_SOURCE} claims per newly externalized source and at most {MAX_CLAIMS_PER_DELTA} total. Total output must be <= {SOURCE_DELTA_TOKEN_BUDGET} tokenizer tokens and each source's claim blocks <= {SOURCE_SLOT_TOKEN_BUDGET}. Copy EVIDENCE_QUOTE exactly; the host uniquely resolves it inside the delivered range and derives line numbers and SHA-256. Do not emit derived line or hash fields. A source-reported fact cannot name another source. A source-reported relationship may name other source objects when the exact owner-source line names them, but it does not assert their authoritative current state or mutate their slots. Do not emit a cross-source derived claim; the ordinary actor must place synthesis in exact task work with all supporting citations.

NEW SOURCE VERSIONS
{versions}

PRIOR CURRENT RECORDS FOR THESE SOURCES
{prior}

AUTHORITATIVE TASK (for relevance only; never use it as evidence)
{task_text}

EXACT NEWLY EXTERNALIZED RESULTS
{exact}
"""
    return [
        {"role": "system", "content": "Return only the bounded provenance-local relational delta. No JSON, code fence, commentary, task action, or readiness judgment."},
        {"role": "user", "content": instruction},
    ]
