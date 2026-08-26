from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Collection, Mapping, Sequence


SOURCE_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]{1,31}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
CLAIM_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]{2,63}$")
WORK_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]{2,63}$")

SOURCE_REPORTED_FACT = "source_reported_fact"
SOURCE_REPORTED_RELATIONSHIP = "source_reported_relationship"
DERIVED_CROSS_SOURCE = "derived_cross_source"
ASSERTION_MODES = {
    SOURCE_REPORTED_FACT,
    SOURCE_REPORTED_RELATIONSHIP,
    DERIVED_CROSS_SOURCE,
}

SOURCE_SLOT = "source_slot"
DERIVED_WORK_SLOT = "derived_work"
RECORD_KINDS = {SOURCE_SLOT, DERIVED_WORK_SLOT}

OWNER_SOURCE_REPORTED = "owner_source_reported"
MODEL_DERIVED_FROM_SUPPORT_SET = "model_derived_from_support_set"
NON_AUTHORITATIVE_DERIVATIVE = "non_authoritative_derivative"
FORBIDDEN_CONTROL_PHRASES = (
    "ready to submit",
    "submit now",
    "closure approved",
    "candidate is ready",
)


@dataclass(frozen=True)
class ProvenanceClaimValidation:
    valid: bool
    code: str
    issues: tuple[str, ...]
    claim_id: str
    record_kind: str
    assertion_mode: str
    slot_source_id: str | None
    evidence_source_ids: tuple[str, ...]
    referent_source_ids: tuple[str, ...]
    currentness: str
    active: bool
    semantic_review_required: bool


def exact_span_bytes(path: Path, start_line: int, end_line: int) -> bytes:
    raw_lines = path.read_bytes().splitlines(keepends=True)
    if start_line < 1 or end_line < start_line or end_line > len(raw_lines):
        raise ValueError("evidence span is outside the exact source")
    return b"".join(raw_lines[start_line - 1 : end_line])


def exact_span_sha256(path: Path, start_line: int, end_line: int) -> str:
    return sha256(exact_span_bytes(path, start_line, end_line)).hexdigest()


def _source_mentions(text: str, source_ids: Collection[str]) -> set[str]:
    return {
        source_id
        for source_id in source_ids
        if re.search(
            rf"(?<![A-Z0-9_-]){re.escape(source_id)}(?![A-Z0-9_-])",
            text,
        )
    }


def _append_once(issues: list[str], issue: str) -> None:
    if issue not in issues:
        issues.append(issue)


def validate_provenance_claim(
    claim: Mapping[str, object],
    *,
    source_catalog: Mapping[str, Mapping[str, object]],
    source_root: Path,
    admitted_source_versions: Mapping[str, str],
    current_source_versions: Mapping[str, str] | None = None,
) -> ProvenanceClaimValidation:
    """Validate mechanical provenance and currentness, never semantic truth.

    The contract separates mutation scope from evidence support and from named
    relationship objects. A mechanically valid claim still requires semantic
    review of its predicate, modality, units, authority, and qualifications.
    """

    issues: list[str] = []
    claim_id = str(claim.get("claim_id", ""))
    record_kind = str(claim.get("record_kind", ""))
    assertion_mode = str(claim.get("assertion_mode", ""))
    attribution = str(claim.get("attribution", ""))
    authority = str(claim.get("authority", ""))
    statement = str(claim.get("statement", ""))

    if not CLAIM_ID_PATTERN.fullmatch(claim_id):
        _append_once(issues, "claim_id_invalid")
    if record_kind not in RECORD_KINDS:
        _append_once(issues, "record_kind_invalid")
    if assertion_mode not in ASSERTION_MODES:
        _append_once(issues, "assertion_mode_invalid")
    if authority != NON_AUTHORITATIVE_DERIVATIVE:
        _append_once(issues, "authority_scope_invalid")
    if not statement.strip():
        _append_once(issues, "statement_empty")
    if any(phrase in statement.casefold() for phrase in FORBIDDEN_CONTROL_PHRASES):
        _append_once(issues, "closure_authorization_forbidden")

    slot = claim.get("slot")
    slot_map = slot if isinstance(slot, Mapping) else {}
    slot_source_id: str | None = None
    if record_kind == SOURCE_SLOT:
        slot_source_id = str(slot_map.get("source_id", ""))
        slot_source_version = str(slot_map.get("source_version", ""))
        if not SOURCE_ID_PATTERN.fullmatch(slot_source_id):
            _append_once(issues, "slot_source_id_invalid")
        if not SHA256_PATTERN.fullmatch(slot_source_version):
            _append_once(issues, "slot_source_version_invalid")
        if admitted_source_versions.get(slot_source_id) != slot_source_version:
            _append_once(issues, "slot_source_not_admitted")
        if "work_id" in slot_map:
            _append_once(issues, "source_slot_contains_work_id")
    elif record_kind == DERIVED_WORK_SLOT:
        work_id = str(slot_map.get("work_id", ""))
        if not WORK_ID_PATTERN.fullmatch(work_id):
            _append_once(issues, "derived_work_id_invalid")
        if "source_id" in slot_map or "source_version" in slot_map:
            _append_once(issues, "derived_work_claim_mutates_source_slot")

    evidence = claim.get("evidence")
    evidence_rows: Sequence[object] = evidence if isinstance(evidence, list) else ()
    if not evidence_rows:
        _append_once(issues, "evidence_missing")
    evidence_source_ids: list[str] = []
    evidence_text: list[str] = []
    for row in evidence_rows:
        if not isinstance(row, Mapping):
            _append_once(issues, "evidence_record_invalid")
            continue
        source_id = str(row.get("source_id", ""))
        source_version = str(row.get("source_version", ""))
        start_line = row.get("start_line")
        end_line = row.get("end_line")
        span_sha256 = str(row.get("span_sha256", ""))
        evidence_source_ids.append(source_id)
        catalog_row = source_catalog.get(source_id)
        if catalog_row is None:
            _append_once(issues, "evidence_source_unknown")
            continue
        if admitted_source_versions.get(source_id) != source_version:
            _append_once(issues, "evidence_source_not_admitted")
        if str(catalog_row.get("sha256", "")) != source_version:
            _append_once(issues, "evidence_source_version_mismatch")
        if not isinstance(start_line, int) or not isinstance(end_line, int):
            _append_once(issues, "evidence_span_invalid")
            continue
        path = source_root / str(catalog_row.get("path", ""))
        if not path.is_file():
            _append_once(issues, "evidence_source_missing")
            continue
        if sha256(path.read_bytes()).hexdigest() != str(catalog_row.get("sha256", "")):
            _append_once(issues, "evidence_source_custody_mismatch")
            continue
        try:
            span = exact_span_bytes(path, start_line, end_line)
        except ValueError:
            _append_once(issues, "evidence_span_invalid")
            continue
        if sha256(span).hexdigest() != span_sha256:
            _append_once(issues, "evidence_span_hash_mismatch")
        try:
            evidence_text.append(span.decode("utf-8"))
        except UnicodeDecodeError:
            _append_once(issues, "evidence_span_not_utf8")

    evidence_sources = tuple(sorted(set(evidence_source_ids)))
    referents_raw = claim.get("referents")
    referents_seq: Sequence[object] = (
        referents_raw if isinstance(referents_raw, list) else ()
    )
    referents = tuple(sorted({str(value) for value in referents_seq}))
    if len(referents) != len(referents_seq):
        _append_once(issues, "referent_duplicate")
    if any(source_id not in source_catalog for source_id in referents):
        _append_once(issues, "referent_unknown")

    combined_evidence = "\n".join(evidence_text)
    known_source_ids = tuple(source_catalog)
    statement_mentions = _source_mentions(statement, known_source_ids)
    declared_or_supported = set(referents) | set(evidence_sources)
    if statement_mentions - declared_or_supported:
        _append_once(issues, "undeclared_source_reference")
    if set(referents) - statement_mentions:
        _append_once(issues, "referent_not_named_in_statement")

    if assertion_mode in {SOURCE_REPORTED_FACT, SOURCE_REPORTED_RELATIONSHIP}:
        if record_kind != SOURCE_SLOT:
            _append_once(issues, "source_report_requires_source_slot")
        if attribution != OWNER_SOURCE_REPORTED:
            _append_once(issues, "source_report_attribution_invalid")
        if slot_source_id is not None and set(evidence_sources) != {slot_source_id}:
            _append_once(issues, "source_report_evidence_basis_mismatch")
        external_referents = set(referents) - ({slot_source_id} if slot_source_id else set())
        if assertion_mode == SOURCE_REPORTED_FACT and external_referents:
            _append_once(issues, "external_referent_requires_relationship_mode")
        if assertion_mode == SOURCE_REPORTED_RELATIONSHIP:
            if not external_referents:
                _append_once(issues, "relationship_referent_missing")
            grounded = _source_mentions(combined_evidence, known_source_ids)
            if external_referents - grounded:
                _append_once(issues, "relationship_referent_not_in_evidence")
    elif assertion_mode == DERIVED_CROSS_SOURCE:
        if record_kind != DERIVED_WORK_SLOT:
            _append_once(issues, "derived_claim_requires_derived_work_slot")
        if attribution != MODEL_DERIVED_FROM_SUPPORT_SET:
            _append_once(issues, "derived_attribution_invalid")
        if len(evidence_sources) < 2:
            _append_once(issues, "derived_support_set_too_small")
        grounded = _source_mentions(combined_evidence, known_source_ids) | set(
            evidence_sources
        )
        if set(referents) - grounded:
            _append_once(issues, "derived_referent_not_in_support_set")

    current_versions = current_source_versions or admitted_source_versions
    currentness = "current"
    for source_id in evidence_sources:
        evidence_version = next(
            (
                str(row.get("source_version", ""))
                for row in evidence_rows
                if isinstance(row, Mapping) and str(row.get("source_id", "")) == source_id
            ),
            "",
        )
        if current_versions.get(source_id) != evidence_version:
            currentness = "stale"
            break

    return ProvenanceClaimValidation(
        valid=not issues,
        code="accepted" if not issues else issues[0],
        issues=tuple(issues),
        claim_id=claim_id,
        record_kind=record_kind,
        assertion_mode=assertion_mode,
        slot_source_id=slot_source_id,
        evidence_source_ids=evidence_sources,
        referent_source_ids=referents,
        currentness=currentness,
        active=not issues and currentness == "current",
        semantic_review_required=True,
    )
