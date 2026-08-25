from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable, Collection, Mapping, Sequence

from reactive_runtime.canonical import canonical_json_text, sha256_bytes
from reactive_runtime.records import ResultRecord


DELTA_PREFIX = "# Source-local evidence delta"
REGISTER_PREFIX = "# Source Evidence Register"
REGISTER_SCHEMA = "source-slot-register-v0"
DELTA_TOKEN_BUDGET = 1_500
DELTA_PROVIDER_MAX_TOKENS = 1_800
SLOT_TOKEN_BUDGET = 650
MAX_ACTOR_SLOT_BYTES = 6_000
REQUIREMENT_PATTERN = re.compile(r"\bQ(?:0[1-9]|1[0-2])\b")
SOURCE_HEADING = re.compile(
    r"(?m)^## SOURCE ([A-Z][A-Z0-9_-]{2,31})\r?\nVERSION ([0-9a-f]{64})\s*$"
)
SLOT_BEGIN = "<!-- SOURCE_SLOT_BEGIN -->"
SLOT_END = "<!-- SOURCE_SLOT_END -->"
REQUIRED_LOCAL_HEADINGS = (
    "### REQUIREMENTS",
    "### FINDINGS",
    "### QUALIFICATIONS AND CONFLICTS",
    "### UNKNOWNS AND REOPEN CONDITIONS",
)
FORBIDDEN_CONTROL_PHRASES = (
    "ready to submit",
    "submit now",
    "closure approved",
    "candidate is ready",
)


@dataclass(frozen=True)
class SourceDeltaSlot:
    source_id: str
    source_version: str
    body: str
    body_tokens: int
    requirement_ids: tuple[str, ...]


@dataclass(frozen=True)
class SourceDeltaValidation:
    valid: bool
    code: str
    output_tokens: int
    source_ids: tuple[str, ...]
    requirement_ids: tuple[str, ...]
    disallowed_source_ids: tuple[str, ...]
    slots: tuple[SourceDeltaSlot, ...]
    issues: tuple[str, ...]


@dataclass(frozen=True)
class SourceSlotRecord:
    source_id: str
    source_version: str
    body: str
    body_sha256: str
    origin: str
    result_ids: tuple[str, ...]
    requirement_ids: tuple[str, ...]

    @classmethod
    def create(
        cls,
        *,
        source_id: str,
        source_version: str,
        body: str,
        origin: str,
        result_ids: Sequence[str],
    ) -> "SourceSlotRecord":
        normalized = body.strip()
        return cls(
            source_id=source_id,
            source_version=source_version,
            body=normalized,
            body_sha256=sha256_bytes(normalized.encode("utf-8")),
            origin=origin,
            result_ids=tuple(dict.fromkeys(result_ids)),
            requirement_ids=tuple(sorted(set(REQUIREMENT_PATTERN.findall(normalized)))),
        )

    def metadata(self) -> dict[str, object]:
        return {
            "body_sha256": self.body_sha256,
            "origin": self.origin,
            "requirement_ids": list(self.requirement_ids),
            "result_ids": list(self.result_ids),
            "schema": "source-slot-record-v0",
            "source_id": self.source_id,
            "source_version": self.source_version,
        }


def observed_source_ids(records: Sequence[ResultRecord]) -> tuple[str, ...]:
    values: list[str] = []
    for record in records:
        source_ids = record.metadata.get("source_ids")
        if isinstance(source_ids, list):
            values.extend(str(value) for value in source_ids)
        elif isinstance(record.metadata.get("source_id"), str):
            values.append(str(record.metadata["source_id"]))
    return tuple(sorted(set(values)))


def _known_source_mentions(text: str, source_ids: Collection[str]) -> set[str]:
    return {
        source_id
        for source_id in source_ids
        if re.search(rf"(?<![A-Z0-9_-]){re.escape(source_id)}(?![A-Z0-9_-])", text)
    }


def _local_body(block: str) -> tuple[str, list[str]]:
    issues: list[str] = []
    positions = [block.find(heading) for heading in REQUIRED_LOCAL_HEADINGS]
    if any(position < 0 for position in positions):
        issues.append("local_heading_missing")
    elif positions != sorted(positions):
        issues.append("local_heading_order")
    for index, heading in enumerate(REQUIRED_LOCAL_HEADINGS):
        position = block.find(heading)
        if position < 0:
            continue
        start = position + len(heading)
        later = [value for value in positions[index + 1 :] if value >= 0]
        end = min(later) if later else len(block)
        if not block[start:end].strip():
            issues.append("local_heading_empty")
            break
    return block.strip(), issues


def validate_source_delta(
    exact_output: str,
    *,
    count_text: Callable[[str], int],
    allowed_source_versions: Mapping[str, str],
    known_source_ids: Collection[str],
    token_budget: int = DELTA_TOKEN_BUDGET,
    slot_token_budget: int = SLOT_TOKEN_BUDGET,
) -> SourceDeltaValidation:
    output_tokens = count_text(exact_output) if exact_output else 0
    issues: list[str] = []
    if not exact_output.strip():
        issues.append("empty_output")
    if not exact_output.startswith(DELTA_PREFIX + "\n"):
        issues.append("required_prefix_missing")
    if output_tokens > token_budget:
        issues.append("token_budget_exceeded")
    folded = exact_output.casefold()
    if any(phrase in folded for phrase in FORBIDDEN_CONTROL_PHRASES):
        issues.append("closure_authorization_forbidden")
    if REGISTER_PREFIX in exact_output or SLOT_BEGIN in exact_output or SLOT_END in exact_output:
        issues.append("global_register_replacement_forbidden")

    matches = list(SOURCE_HEADING.finditer(exact_output))
    if not matches:
        issues.append("source_block_missing")
    preamble = exact_output[len(DELTA_PREFIX) : matches[0].start()].strip() if matches else ""
    if preamble:
        issues.append("unexpected_global_preamble")

    slots: list[SourceDeltaSlot] = []
    seen: set[str] = set()
    for index, match in enumerate(matches):
        source_id, source_version = match.group(1), match.group(2)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(exact_output)
        body, local_issues = _local_body(exact_output[match.end() : end])
        issues.extend(local_issues)
        if source_id in seen:
            issues.append("duplicate_source_block")
        seen.add(source_id)
        if source_id not in allowed_source_versions:
            issues.append("unobserved_source_block")
        elif allowed_source_versions[source_id] != source_version:
            issues.append("source_version_mismatch")
        body_tokens = count_text(body) if body else 0
        if body_tokens > slot_token_budget:
            issues.append("slot_token_budget_exceeded")
        slots.append(
            SourceDeltaSlot(
                source_id=source_id,
                source_version=source_version,
                body=body,
                body_tokens=body_tokens,
                requirement_ids=tuple(sorted(set(REQUIREMENT_PATTERN.findall(body)))),
            )
        )

    allowed = set(allowed_source_versions)
    output_sources = {slot.source_id for slot in slots}
    if output_sources != allowed:
        issues.append("incomplete_current_batch_coverage")
    mentioned = _known_source_mentions(exact_output, known_source_ids)
    disallowed = tuple(sorted(mentioned - allowed))
    if disallowed:
        issues.append("unobserved_source_reference")
    issues = list(dict.fromkeys(issues))
    return SourceDeltaValidation(
        valid=not issues,
        code="accepted" if not issues else issues[0],
        output_tokens=output_tokens,
        source_ids=tuple(sorted(output_sources)),
        requirement_ids=tuple(
            sorted({value for slot in slots for value in slot.requirement_ids})
        ),
        disallowed_source_ids=disallowed,
        slots=tuple(slots),
        issues=tuple(issues),
    )


class SourceEvidenceRegister:
    def __init__(self, slots: Mapping[str, SourceSlotRecord] | None = None) -> None:
        self._slots = dict(slots or {})

    @classmethod
    def parse(cls, text: str) -> "SourceEvidenceRegister":
        if not text.startswith(REGISTER_PREFIX + "\n"):
            raise ValueError("register prefix mismatch")
        expected_header = "\n".join(
            (
                REGISTER_PREFIX,
                "",
                f"Schema: {REGISTER_SCHEMA}",
                "Readiness authority: none; exact sources and external evaluation govern.",
            )
        )
        slots: dict[str, SourceSlotRecord] = {}
        cursor = text.find(SLOT_BEGIN)
        header_end = cursor if cursor >= 0 else len(text)
        if cursor < 0 and text.strip() != expected_header:
            if text.startswith(expected_header):
                raise ValueError("unexpected trailing register content")
            raise ValueError("register header mismatch")
        if text[:header_end].strip() != expected_header:
            raise ValueError("register header mismatch")
        scan_from = header_end
        while cursor >= 0:
            if text[scan_from:cursor].strip():
                raise ValueError("unexpected content between source slots")
            metadata_start = cursor + len(SLOT_BEGIN)
            metadata_end = text.find("\n", metadata_start)
            if metadata_end < 0:
                raise ValueError("slot metadata line missing")
            metadata = json.loads(text[metadata_start:metadata_end].strip())
            end = text.find(SLOT_END, metadata_end)
            if end < 0:
                raise ValueError("slot end marker missing")
            body = text[metadata_end + 1 : end].strip()
            record = SourceSlotRecord.create(
                source_id=str(metadata["source_id"]),
                source_version=str(metadata["source_version"]),
                body=body,
                origin=str(metadata["origin"]),
                result_ids=tuple(str(value) for value in metadata.get("result_ids", [])),
            )
            if metadata.get("schema") != "source-slot-record-v0":
                raise ValueError("slot schema mismatch")
            if metadata.get("body_sha256") != record.body_sha256:
                raise ValueError("slot body hash mismatch")
            if metadata.get("requirement_ids") != list(record.requirement_ids):
                raise ValueError("slot requirement binding mismatch")
            if not re.fullmatch(r"[0-9a-f]{64}", record.source_version):
                raise ValueError("slot source version mismatch")
            if not record.body:
                raise ValueError("empty source slot")
            if record.source_id in slots:
                raise ValueError("duplicate source slot")
            slots[record.source_id] = record
            scan_from = end + len(SLOT_END)
            cursor = text.find(SLOT_BEGIN, scan_from)
        if text[scan_from:].strip():
            raise ValueError("unexpected trailing register content")
        if SLOT_END in text[:header_end]:
            raise ValueError("orphan source-slot end marker")
        return cls(slots)

    def slots(self) -> dict[str, SourceSlotRecord]:
        return dict(self._slots)

    def get(self, source_id: str) -> SourceSlotRecord | None:
        return self._slots.get(source_id)

    def merge(self, replacements: Sequence[SourceSlotRecord]) -> "SourceEvidenceRegister":
        updated = self.slots()
        for record in replacements:
            updated[record.source_id] = record
        return SourceEvidenceRegister(updated)

    def render(self) -> str:
        rows = [
            REGISTER_PREFIX,
            "",
            f"Schema: {REGISTER_SCHEMA}",
            "Readiness authority: none; exact sources and external evaluation govern.",
        ]
        for source_id in sorted(self._slots):
            record = self._slots[source_id]
            rows.extend(
                [
                    "",
                    SLOT_BEGIN + canonical_json_text(record.metadata()),
                    record.body,
                    SLOT_END,
                ]
            )
        return "\n".join(rows).rstrip() + "\n"


def actor_slot_record(
    *,
    source_id: str,
    source_version: str,
    content: str,
    known_source_versions: Mapping[str, str],
    result_ids: Sequence[str] = (),
    count_text: Callable[[str], int] | None = None,
    slot_token_budget: int = SLOT_TOKEN_BUDGET,
) -> SourceSlotRecord:
    if source_id not in known_source_versions:
        raise ValueError("unknown source slot")
    if known_source_versions[source_id] != source_version:
        raise ValueError("source slot version mismatch")
    raw = content.encode("utf-8")
    if not raw or len(raw) > MAX_ACTOR_SLOT_BYTES:
        raise ValueError(f"source slot must contain 1..{MAX_ACTOR_SLOT_BYTES} bytes")
    if count_text is not None and count_text(content) > slot_token_budget:
        raise ValueError(
            f"source slot exceeds the {slot_token_budget}-token slot budget"
        )
    if SLOT_BEGIN in content or SLOT_END in content or REGISTER_PREFIX in content:
        raise ValueError("source slot may not contain register control markers")
    mentions = _known_source_mentions(content, known_source_versions)
    if mentions - {source_id}:
        raise ValueError("actor source slot may cite only its bound source")
    if any(phrase in content.casefold() for phrase in FORBIDDEN_CONTROL_PHRASES):
        raise ValueError("source slot may not authorize closure")
    return SourceSlotRecord.create(
        source_id=source_id,
        source_version=source_version,
        body=content,
        origin="ordinary_actor",
        result_ids=result_ids,
    )


def records_from_delta(
    validation: SourceDeltaValidation,
    *,
    input_result_ids: Sequence[str],
) -> tuple[SourceSlotRecord, ...]:
    if not validation.valid:
        raise ValueError("cannot materialize rejected source delta")
    return tuple(
        SourceSlotRecord.create(
            source_id=slot.source_id,
            source_version=slot.source_version,
            body=slot.body,
            origin="source_local_maintenance",
            result_ids=input_result_ids,
        )
        for slot in validation.slots
    )


def source_delta_messages(
    *,
    task_text: str,
    register: SourceEvidenceRegister,
    newly_externalized: Sequence[ResultRecord],
    source_versions: Mapping[str, str],
) -> list[dict[str, str]]:
    if not newly_externalized:
        raise ValueError("source-local maintenance requires exact results")
    current_sources = observed_source_ids(newly_externalized)
    if not current_sources:
        raise ValueError("source-local maintenance lacks source observations")
    allowed = {source_id: source_versions[source_id] for source_id in current_sources}
    prior_rows = []
    for source_id in current_sources:
        prior = register.get(source_id)
        prior_rows.append(
            f"## PRIOR SLOT {source_id}\n"
            + ("none" if prior is None else prior.body)
        )
    observations = "\n\n".join(
        f"## EXACT RESULT {record.result_id}\n{record.exact_content}"
        for record in newly_externalized
    )
    system = f"""# SOURCE_LOCAL_EVIDENCE_DELTA maintenance mode

Return only bounded Markdown beginning exactly `{DELTA_PREFIX}`. Emit exactly
one `## SOURCE <ID>` block for every source in the current exact batch and no
other source. The next line must be `VERSION <sha256>`. Each block must contain,
in order: {', '.join(REQUIRED_LOCAL_HEADINGS)}.

Transform only the supplied exact source bytes. Preserve units, probabilities,
versions, qualifications, contradictions, and task requirement links Q01-Q12.
The output is lossy, source-bound task work. It cannot replace the global
register, authorize readiness, recommend submission, or edit absent source
slots. Hard total limit: {DELTA_TOKEN_BUDGET} tokens; hard per-source limit:
{SLOT_TOKEN_BUDGET} tokens. Allowed exact bindings:
{canonical_json_text(allowed)}"""
    user = f"""# Authoritative task

{task_text}

# Prior slots for only the current sources

{chr(10).join(prior_rows)}

# Newly externalized exact source observations

{observations}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
