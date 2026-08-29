from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from reactive_runtime.canonical import sha256_bytes
from reactive_runtime.provenance_claims import (
    NON_AUTHORITATIVE_DERIVATIVE,
    OWNER_SOURCE_REPORTED,
    SOURCE_REPORTED_FACT,
    SOURCE_REPORTED_RELATIONSHIP,
    SOURCE_SLOT,
    ProvenanceClaimValidation,
    exact_span_bytes,
    validate_provenance_claim,
)
from reactive_runtime.records import ResultRecord


DELTA_PREFIX = "# Anchored provenance-local delta"
REGISTER_PREFIX = "# Anchored provenance-local source register"
CLAIM_HEADING = re.compile(r"(?m)^## CLAIM ([A-Z][A-Z0-9_-]{2,63})\s*$")
DELTA_TOKEN_BUDGET = 1_500
SOURCE_SLOT_TOKEN_BUDGET = 650
REGISTER_TOKEN_BUDGET = 8_000
MAX_CLAIMS_PER_DELTA = 8
MAX_CLAIMS_PER_SOURCE = 4


@dataclass(frozen=True)
class MaterializedAnchor:
    source_id: str
    source_version: str
    result_id: str
    anchor_text: str
    anchor_sha256: str
    anchor_start_byte: int
    anchor_end_byte: int
    context_text: str
    context_sha256: str
    context_start_line: int
    context_end_line: int

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "MaterializedAnchor":
        return cls(
            source_id=str(value["source_id"]),
            source_version=str(value["source_version"]),
            result_id=str(value["result_id"]),
            anchor_text=str(value["anchor_text"]),
            anchor_sha256=str(value["anchor_sha256"]),
            anchor_start_byte=int(str(value["anchor_start_byte"])),
            anchor_end_byte=int(str(value["anchor_end_byte"])),
            context_text=str(value["context_text"]),
            context_sha256=str(value["context_sha256"]),
            context_start_line=int(str(value["context_start_line"])),
            context_end_line=int(str(value["context_end_line"])),
        )


@dataclass(frozen=True)
class AnchoredClaim:
    claim_id: str
    source_id: str
    source_version: str
    evidence_result_id: str
    anchor: MaterializedAnchor
    assertion_mode: str
    referents: tuple[str, ...]
    statement: str
    body_tokens: int

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "AnchoredClaim":
        anchor = value.get("anchor")
        if not isinstance(anchor, Mapping):
            raise ValueError("anchored claim lacks anchor object")
        referents = value.get("referents", ())
        if not isinstance(referents, (list, tuple)):
            raise ValueError("anchored claim referents must be a sequence")
        return cls(
            claim_id=str(value["claim_id"]),
            source_id=str(value["source_id"]),
            source_version=str(value["source_version"]),
            evidence_result_id=str(value["evidence_result_id"]),
            anchor=MaterializedAnchor.from_dict(anchor),
            assertion_mode=str(value["assertion_mode"]),
            referents=tuple(str(item) for item in referents),
            statement=str(value["statement"]),
            body_tokens=int(str(value["body_tokens"])),
        )

    @property
    def stable_key(self) -> tuple[str, str, str]:
        return (self.source_id, self.source_version, self.claim_id)

    def render(self) -> str:
        referents = ",".join(self.referents) if self.referents else "NONE"
        return "\n".join(
            (
                f"## CLAIM {self.claim_id}",
                f"SLOT_SOURCE: {self.source_id}",
                f"SOURCE_VERSION: {self.source_version}",
                f"EVIDENCE_RESULT: {self.evidence_result_id}",
                f"EVIDENCE_ANCHOR: {self.anchor.anchor_text}",
                f"ANCHOR_BYTES: {self.anchor.anchor_start_byte}-{self.anchor.anchor_end_byte}",
                f"ANCHOR_SHA256: {self.anchor.anchor_sha256}",
                f"CONTEXT_LINES: {self.anchor.context_start_line}-{self.anchor.context_end_line}",
                f"CONTEXT_SHA256: {self.anchor.context_sha256}",
                f"MODE: {self.assertion_mode}",
                f"ATTRIBUTION: {OWNER_SOURCE_REPORTED}",
                f"REFERENTS: {referents}",
                f"AUTHORITY: {NON_AUTHORITATIVE_DERIVATIVE}",
                f"STATEMENT: {self.statement}",
            )
        )


@dataclass(frozen=True)
class ClaimAdmission:
    claim_id: str
    source_id: str | None
    admitted: bool
    code: str
    issues: tuple[str, ...]
    claim: AnchoredClaim | None
    provenance: ProvenanceClaimValidation | None


@dataclass(frozen=True)
class DeltaAdmission:
    disposition: str
    output_tokens: int
    global_issues: tuple[str, ...]
    records: tuple[ClaimAdmission, ...]

    @property
    def admitted_claims(self) -> tuple[AnchoredClaim, ...]:
        return tuple(
            record.claim
            for record in self.records
            if record.admitted and record.claim is not None
        )

    @property
    def rejected_claims(self) -> tuple[ClaimAdmission, ...]:
        return tuple(record for record in self.records if not record.admitted)


@dataclass(frozen=True)
class RegisterTransition:
    disposition: str
    before_sha256: str
    after_sha256: str
    register: "AnchoredProvenanceRegister"
    admitted_claim_ids: tuple[str, ...]
    rejected_claim_ids: tuple[str, ...]
    issues: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return self.before_sha256 != self.after_sha256


def _append_once(issues: list[str], value: str) -> None:
    if value not in issues:
        issues.append(value)


def _field_map(block: str) -> tuple[dict[str, str], tuple[str, ...]]:
    fields: dict[str, str] = {}
    issues: list[str] = []
    for line in block.splitlines()[1:]:
        if not line.strip():
            continue
        if ": " not in line:
            _append_once(issues, "claim_line_invalid")
            continue
        key, value = line.split(": ", 1)
        if key in fields:
            _append_once(issues, "claim_field_duplicate")
        fields[key] = value.strip()
    required = {
        "SLOT_SOURCE",
        "SOURCE_VERSION",
        "EVIDENCE_RESULT",
        "EVIDENCE_ANCHOR",
        "MODE",
        "ATTRIBUTION",
        "REFERENTS",
        "AUTHORITY",
        "STATEMENT",
    }
    if set(fields) != required:
        _append_once(issues, "claim_fields_invalid")
    return fields, tuple(issues)


def _result_segments(records: Sequence[ResultRecord]) -> dict[str, tuple[dict[str, object], ...]]:
    result: dict[str, tuple[dict[str, object], ...]] = {}
    for record in records:
        raw = record.metadata.get("segments")
        if isinstance(raw, list):
            result[record.result_id] = tuple(row for row in raw if isinstance(row, dict))
            continue
        source_id = record.metadata.get("source_id")
        start_line = record.metadata.get("start_line")
        end_line = record.metadata.get("end_line")
        result[record.result_id] = (
            {
                "source_id": source_id,
                "start_line": start_line,
                "end_line": end_line,
            },
        )
    return result


def _admitted_versions(records: Sequence[ResultRecord]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for record in records:
        raw = record.metadata.get("source_versions")
        if isinstance(raw, dict):
            versions.update((str(key), str(value)) for key, value in raw.items())
            continue
        source_id = record.metadata.get("source_id")
        version = record.metadata.get("source_sha256")
        if isinstance(source_id, str) and isinstance(version, str):
            versions[source_id] = version
    return versions


def materialize_unique_anchor(
    *,
    source_id: str,
    source_version: str,
    result_id: str,
    anchor_text: str,
    source_catalog: Mapping[str, Mapping[str, object]],
    task_root: Path,
    segments_by_result: Mapping[str, Sequence[Mapping[str, object]]],
) -> tuple[MaterializedAnchor | None, tuple[str, ...]]:
    """Resolve a model-selected exact substring and derive host-owned custody fields."""

    issues: list[str] = []
    if not anchor_text or "\n" in anchor_text or "\r" in anchor_text:
        return None, ("evidence_anchor_invalid",)
    catalog_row = source_catalog.get(source_id)
    if catalog_row is None:
        return None, ("source_unknown",)
    if str(catalog_row.get("sha256", "")) != source_version:
        _append_once(issues, "source_version_mismatch")
    source_path = task_root / str(catalog_row.get("path", ""))
    if not source_path.is_file():
        return None, tuple((*issues, "source_missing"))

    source_bytes = source_path.read_bytes()
    if sha256_bytes(source_bytes) != str(catalog_row.get("sha256", "")):
        _append_once(issues, "source_custody_mismatch")
    try:
        source_text = source_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None, tuple((*issues, "source_not_utf8"))

    lines = source_text.splitlines()
    raw_lines = source_bytes.splitlines(keepends=True)
    eligible_lines: set[int] = set()
    for row in segments_by_result.get(result_id, ()):
        if str(row.get("source_id", "")) != source_id:
            continue
        start_line = row.get("start_line")
        end_line = row.get("end_line")
        if isinstance(start_line, int) and isinstance(end_line, int):
            eligible_lines.update(range(start_line, end_line + 1))
    matches: list[tuple[int, int]] = []
    for line_number in sorted(eligible_lines):
        if not 1 <= line_number <= len(lines):
            continue
        start = 0
        while True:
            found = lines[line_number - 1].find(anchor_text, start)
            if found < 0:
                break
            matches.append((line_number, found))
            start = found + 1
    if len(matches) != 1:
        _append_once(issues, "evidence_anchor_not_unique_in_result")
        return None, tuple(issues)

    line_number, character_offset = matches[0]
    anchor_start_byte = sum(len(line) for line in raw_lines[: line_number - 1]) + len(
        lines[line_number - 1][:character_offset].encode("utf-8")
    )
    anchor_bytes = anchor_text.encode("utf-8")
    context_bytes = exact_span_bytes(source_path, line_number, line_number)
    context_text = context_bytes.decode("utf-8").rstrip("\r\n")
    return (
        MaterializedAnchor(
            source_id=source_id,
            source_version=source_version,
            result_id=result_id,
            anchor_text=anchor_text,
            anchor_sha256=sha256_bytes(anchor_bytes),
            anchor_start_byte=anchor_start_byte,
            anchor_end_byte=anchor_start_byte + len(anchor_bytes),
            context_text=context_text,
            context_sha256=sha256_bytes(context_bytes),
            context_start_line=line_number,
            context_end_line=line_number,
        ),
        tuple(issues),
    )


def admit_anchored_delta(
    text: str,
    *,
    count_text: Callable[[str], int],
    source_catalog: Mapping[str, Mapping[str, object]],
    task_root: Path,
    newly_externalized: Sequence[ResultRecord],
    current_source_versions: Mapping[str, str],
) -> DeltaAdmission:
    """Admit independently valid claims; never repair or infer model output."""

    output_tokens = count_text(text)
    global_issues: list[str] = []
    if output_tokens > DELTA_TOKEN_BUDGET:
        _append_once(global_issues, "delta_token_budget_exceeded")
    if not text.startswith(DELTA_PREFIX + "\n"):
        _append_once(global_issues, "delta_prefix_invalid")
    matches = list(CLAIM_HEADING.finditer(text))
    if not 1 <= len(matches) <= MAX_CLAIMS_PER_DELTA:
        _append_once(global_issues, "claim_count_invalid")
    elif text[: matches[0].start()].strip() != DELTA_PREFIX:
        _append_once(global_issues, "delta_preamble_invalid")
    if global_issues:
        return DeltaAdmission(
            disposition="global_reject",
            output_tokens=output_tokens,
            global_issues=tuple(global_issues),
            records=(),
        )

    segments = _result_segments(newly_externalized)
    versions = _admitted_versions(newly_externalized)
    externalized_ids = {record.result_id for record in newly_externalized}
    records: list[ClaimAdmission] = []
    seen_ids: dict[str, int] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start() : end].strip()
        claim_id = match.group(1)
        fields, field_issues = _field_map(block)
        issues = list(field_issues)
        source_id = fields.get("SLOT_SOURCE")
        seen_ids[claim_id] = seen_ids.get(claim_id, 0) + 1
        if field_issues or source_id is None:
            records.append(
                ClaimAdmission(
                    claim_id=claim_id,
                    source_id=source_id,
                    admitted=False,
                    code=issues[0],
                    issues=tuple(issues),
                    claim=None,
                    provenance=None,
                )
            )
            continue

        source_version = fields["SOURCE_VERSION"]
        result_id = fields["EVIDENCE_RESULT"]
        if result_id not in externalized_ids:
            _append_once(issues, "evidence_result_not_newly_externalized")
        anchor, anchor_issues = materialize_unique_anchor(
            source_id=source_id,
            source_version=source_version,
            result_id=result_id,
            anchor_text=fields["EVIDENCE_ANCHOR"],
            source_catalog=source_catalog,
            task_root=task_root,
            segments_by_result=segments,
        )
        for issue in anchor_issues:
            _append_once(issues, issue)
        referents = (
            ()
            if fields["REFERENTS"] == "NONE"
            else tuple(value.strip() for value in fields["REFERENTS"].split(",") if value.strip())
        )
        provenance: ProvenanceClaimValidation | None = None
        claim: AnchoredClaim | None = None
        if anchor is not None:
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
                        "start_line": anchor.context_start_line,
                        "end_line": anchor.context_end_line,
                        "span_sha256": anchor.context_sha256,
                    }
                ],
                "statement": fields["STATEMENT"],
            }
            provenance = validate_provenance_claim(
                claim_map,
                source_catalog=source_catalog,
                source_root=task_root,
                admitted_source_versions=versions,
                current_source_versions=current_source_versions,
            )
            for issue in provenance.issues:
                _append_once(issues, issue)
            claim = AnchoredClaim(
                claim_id=claim_id,
                source_id=source_id,
                source_version=source_version,
                evidence_result_id=result_id,
                anchor=anchor,
                assertion_mode=fields["MODE"],
                referents=referents,
                statement=fields["STATEMENT"],
                body_tokens=count_text(block),
            )
        records.append(
            ClaimAdmission(
                claim_id=claim_id,
                source_id=source_id,
                admitted=not issues and claim is not None,
                code="accepted" if not issues else issues[0],
                issues=tuple(issues),
                claim=claim,
                provenance=provenance,
            )
        )

    duplicate_ids = {claim_id for claim_id, count in seen_ids.items() if count > 1}
    overfull_sources: set[str] = set()
    source_candidates: dict[str, list[ClaimAdmission]] = {}
    for record in records:
        if record.admitted and record.source_id is not None:
            source_candidates.setdefault(record.source_id, []).append(record)
    for source_id, candidates in source_candidates.items():
        claims = [record.claim for record in candidates if record.claim is not None]
        if len(claims) > MAX_CLAIMS_PER_SOURCE or sum(claim.body_tokens for claim in claims) > SOURCE_SLOT_TOKEN_BUDGET:
            overfull_sources.add(source_id)

    normalized: list[ClaimAdmission] = []
    for record in records:
        extra: str | None = None
        if record.claim_id in duplicate_ids:
            extra = "claim_id_duplicate"
        elif record.source_id in overfull_sources:
            extra = f"source_slot_budget_exceeded:{record.source_id}"
        if extra is None:
            normalized.append(record)
            continue
        normalized_issues = tuple(dict.fromkeys((*record.issues, extra)))
        normalized.append(
            ClaimAdmission(
                claim_id=record.claim_id,
                source_id=record.source_id,
                admitted=False,
                code=record.code if record.issues else extra,
                issues=normalized_issues,
                claim=record.claim,
                provenance=record.provenance,
            )
        )

    admitted_count = sum(record.admitted for record in normalized)
    rejected_count = len(normalized) - admitted_count
    disposition = "full_admission" if rejected_count == 0 else "partial_admission" if admitted_count else "zero_valid"
    return DeltaAdmission(
        disposition=disposition,
        output_tokens=output_tokens,
        global_issues=(),
        records=tuple(normalized),
    )


@dataclass(frozen=True)
class AnchoredProvenanceRegister:
    claims: tuple[AnchoredClaim, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "claims": [
                {
                    "anchor": {
                        "anchor_end_byte": claim.anchor.anchor_end_byte,
                        "anchor_sha256": claim.anchor.anchor_sha256,
                        "anchor_start_byte": claim.anchor.anchor_start_byte,
                        "anchor_text": claim.anchor.anchor_text,
                        "context_end_line": claim.anchor.context_end_line,
                        "context_sha256": claim.anchor.context_sha256,
                        "context_start_line": claim.anchor.context_start_line,
                        "context_text": claim.anchor.context_text,
                        "result_id": claim.anchor.result_id,
                        "source_id": claim.anchor.source_id,
                        "source_version": claim.anchor.source_version,
                    },
                    "assertion_mode": claim.assertion_mode,
                    "body_tokens": claim.body_tokens,
                    "claim_id": claim.claim_id,
                    "evidence_result_id": claim.evidence_result_id,
                    "referents": list(claim.referents),
                    "source_id": claim.source_id,
                    "source_version": claim.source_version,
                    "statement": claim.statement,
                }
                for claim in self.claims
            ],
            "register_sha256": self.sha256,
            "schema": "anchored-provenance-register-v0",
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "AnchoredProvenanceRegister":
        if value.get("schema") != "anchored-provenance-register-v0":
            raise ValueError("unsupported anchored provenance register schema")
        rows = value.get("claims")
        if not isinstance(rows, list) or not all(isinstance(row, Mapping) for row in rows):
            raise ValueError("anchored provenance register claims must be objects")
        register = cls(tuple(AnchoredClaim.from_dict(row) for row in rows))
        if value.get("register_sha256") != register.sha256:
            raise ValueError("anchored provenance register hash mismatch")
        return register

    def apply(
        self,
        admission: DeltaAdmission,
        *,
        current_source_versions: Mapping[str, str],
        count_text: Callable[[str], int],
    ) -> RegisterTransition:
        before = self.sha256
        admitted = admission.admitted_claims
        rejected_ids = tuple(record.claim_id for record in admission.rejected_claims)
        if not admitted:
            return RegisterTransition(
                disposition=admission.disposition,
                before_sha256=before,
                after_sha256=before,
                register=self,
                admitted_claim_ids=(),
                rejected_claim_ids=rejected_ids,
                issues=admission.global_issues,
            )

        replaced_sources = {claim.source_id for claim in admitted}
        retained = tuple(
            claim
            for claim in self.claims
            if claim.source_id not in replaced_sources
            and current_source_versions.get(claim.source_id) == claim.source_version
        )
        candidate = AnchoredProvenanceRegister(
            tuple(sorted((*retained, *admitted), key=lambda claim: claim.stable_key))
        )
        if count_text(candidate.render()) > REGISTER_TOKEN_BUDGET:
            return RegisterTransition(
                disposition="register_budget_reject",
                before_sha256=before,
                after_sha256=before,
                register=self,
                admitted_claim_ids=(),
                rejected_claim_ids=tuple(claim.claim_id for claim in admitted) + rejected_ids,
                issues=("register_token_budget_exceeded",),
            )
        return RegisterTransition(
            disposition=admission.disposition,
            before_sha256=before,
            after_sha256=candidate.sha256,
            register=candidate,
            admitted_claim_ids=tuple(claim.claim_id for claim in admitted),
            rejected_claim_ids=rejected_ids,
            issues=(),
        )

    def for_sources(self, source_ids: Iterable[str]) -> "AnchoredProvenanceRegister":
        allowed = set(source_ids)
        return AnchoredProvenanceRegister(tuple(claim for claim in self.claims if claim.source_id in allowed))

    def render(self) -> str:
        if not self.claims:
            return REGISTER_PREFIX + "\n\nEMPTY\n"
        notice = (
            "NON-AUTHORITATIVE, INCOMPLETE SEMANTIC RESIDUE. Omission is not evidence "
            "that a source or requirement was covered. Exact sources remain reopenable."
        )
        return REGISTER_PREFIX + "\n" + notice + "\n\n" + "\n\n".join(claim.render() for claim in self.claims) + "\n"

    @property
    def sha256(self) -> str:
        return sha256_bytes(self.render().encode("utf-8"))


def anchored_delta_messages(
    *,
    task_text: str,
    register: AnchoredProvenanceRegister,
    newly_externalized: Sequence[ResultRecord],
    source_versions: Mapping[str, str],
) -> list[dict[str, str]]:
    source_ids: list[str] = []
    for record in newly_externalized:
        raw = record.metadata.get("source_ids")
        if isinstance(raw, list):
            source_ids.extend(str(value) for value in raw)
        elif isinstance(record.metadata.get("source_id"), str):
            source_ids.append(str(record.metadata["source_id"]))
    source_ids = list(dict.fromkeys(source_ids))
    exact = "\n\n".join(
        f"--- NEWLY EXTERNALIZED {record.result_id} ---\n{record.exact_content}"
        for record in newly_externalized
    )
    versions = "\n".join(f"{source_id}: {source_versions[source_id]}" for source_id in source_ids)
    prior = register.for_sources(source_ids).render()
    instruction = f"""You are in bounded semantic-maintenance mode. Select source-grounded meaning from the newly externalized results. Do not continue the task, judge readiness, or authorize closure.

Use this exact plain-text carrier once:
{DELTA_PREFIX}
## CLAIM <UNIQUE_ID>
SLOT_SOURCE: <one newly externalized source ID>
SOURCE_VERSION: <exact 64-hex version>
EVIDENCE_RESULT: <exact newly externalized RESULT ID>
EVIDENCE_ANCHOR: <one exact unique single-line substring copied from that source inside the delivered result>
MODE: {SOURCE_REPORTED_FACT} or {SOURCE_REPORTED_RELATIONSHIP}
ATTRIBUTION: {OWNER_SOURCE_REPORTED}
REFERENTS: NONE or comma-separated exact source IDs named by both the statement and the anchor's containing source line
AUTHORITY: {NON_AUTHORITATIVE_DERIVATIVE}
STATEMENT: <one complete single-line source-attributed fact or relationship>

The host, not you, resolves the exact anchor, derives its containing complete source line, byte offsets, hashes, source/version binding, and reopen path. Copy only the smallest exact substring that supports the statement. The containing line preserves adjacent context and qualifications. Each claim is admitted independently; rejected claims consume cost and are discarded without repair or retry. A zero-valid update leaves prior state unchanged and ordinary task work continues.

Emit at most {MAX_CLAIMS_PER_SOURCE} claims per source and {MAX_CLAIMS_PER_DELTA} total, <= {DELTA_TOKEN_BUDGET} tokenizer tokens overall and <= {SOURCE_SLOT_TOKEN_BUDGET} per source. A fact cannot name an external source. A relationship may name external objects when the owner-source context names them, but cannot mutate their slots or assert their authoritative current state. Cross-source synthesis belongs in exact task work, not this register.

NEW SOURCE VERSIONS
{versions}

PRIOR CURRENT RECORDS FOR THESE SOURCES
{prior}

AUTHORITATIVE TASK (relevance only; never evidence)
{task_text}

EXACT NEWLY EXTERNALIZED RESULTS
{exact}
"""
    return [
        {
            "role": "system",
            "content": "Return only the bounded anchored provenance delta. No JSON, code fence, commentary, task action, or readiness judgment.",
        },
        {"role": "user", "content": instruction},
    ]
