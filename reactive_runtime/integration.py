from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Collection, Sequence

from reactive_runtime.canonical import sha256_bytes
from reactive_runtime.records import ResultRecord


INTEGRATION_PREFIX = "# Evidence Integration Ledger"
INTEGRATION_TOKEN_BUDGET = 1600
INTEGRATION_PROVIDER_MAX_TOKENS = 1900
BATCHED_INTEGRATION_TOKEN_BUDGET = 2400
BATCHED_INTEGRATION_PROVIDER_MAX_TOKENS = 2700
SOURCE_PATTERN = re.compile(r"(?<![A-Za-z0-9])S(?:0[1-9]|1[0-6])(?![A-Za-z0-9])")
REQUIREMENT_PATTERN = re.compile(r"(?<![A-Za-z0-9])R(?:0[1-9]|1[0-2])(?![A-Za-z0-9])")


@dataclass(frozen=True)
class IntegrationArtifact:
    version: int
    body: str
    body_tokens: int
    input_result_ids: tuple[str, ...]
    observed_source_ids: tuple[str, ...]

    @property
    def body_sha256(self) -> str:
        return sha256_bytes(self.body.encode("utf-8"))


@dataclass(frozen=True)
class IntegrationValidation:
    valid: bool
    code: str
    output_tokens: int
    source_ids: tuple[str, ...]
    disallowed_source_ids: tuple[str, ...]
    requirement_ids: tuple[str, ...]
    issues: tuple[str, ...]


def observed_source_ids(record: ResultRecord) -> tuple[str, ...]:
    values = record.metadata.get("source_ids")
    if isinstance(values, list):
        return tuple(sorted(set(str(value) for value in values)))
    value = record.metadata.get("source_id")
    return () if value is None else (str(value),)


def validate_integration(
    exact_output: str,
    *,
    count_text: Callable[[str], int],
    allowed_source_ids: Collection[str],
    token_budget: int = INTEGRATION_TOKEN_BUDGET,
) -> IntegrationValidation:
    tokens = count_text(exact_output) if exact_output else 0
    sources = tuple(sorted(set(SOURCE_PATTERN.findall(exact_output))))
    requirements = tuple(sorted(set(REQUIREMENT_PATTERN.findall(exact_output))))
    disallowed = tuple(sorted(set(sources) - set(allowed_source_ids)))
    issues: list[str] = []
    if not exact_output.strip():
        issues.append("empty_output")
    if not exact_output.lstrip().startswith(INTEGRATION_PREFIX):
        issues.append("required_prefix_missing")
    if tokens > token_budget:
        issues.append("token_budget_exceeded")
    if disallowed:
        issues.append("unobserved_source_reference")
    if "ready to submit" in exact_output.casefold() or "submit now" in exact_output.casefold():
        issues.append("closure_authorization_forbidden")
    return IntegrationValidation(
        valid=not issues,
        code="accepted" if not issues else issues[0],
        output_tokens=tokens,
        source_ids=sources,
        disallowed_source_ids=disallowed,
        requirement_ids=requirements,
        issues=tuple(issues),
    )


def integration_messages(
    *,
    task_text: str,
    prior: IntegrationArtifact | None,
    newly_externalized: ResultRecord,
    allowed_source_ids: Collection[str],
) -> list[dict[str, str]]:
    prior_body = (
        f"{INTEGRATION_PREFIX}\n\nNo accepted evidence has been integrated yet."
        if prior is None
        else prior.body
    )
    allowed = ", ".join(sorted(set(allowed_source_ids))) or "none"
    system = f"""# EVIDENCE_INTEGRATION maintenance mode

Return only a complete replacement Markdown evidence-integration ledger whose
first line is exactly `{INTEGRATION_PREFIX}`. Do not take an ordinary task
action. Integrate source-grounded findings, qualifications, cross-source
relationships, requirement bindings R01-R12, contradictions, and unresolved
evidence useful for the authoritative task decision.

The output is model-authored and lossy. It cannot authorize readiness or
submission. Replace prior material rather than appending indefinitely. Keep it
under the hard {INTEGRATION_TOKEN_BUDGET}-token limit. The only evidence source
IDs you may cite are: {allowed}. Source identities elsewhere in the task are
not evidence unless they are in that allowlist."""
    user = f"""# Authoritative task

{task_text}

# Prior accepted integration ledger

{prior_body}

# Exact newly externalized observation

{newly_externalized.exact_content}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def batched_integration_messages(
    *,
    task_text: str,
    prior: IntegrationArtifact | None,
    newly_externalized: Sequence[ResultRecord],
    allowed_source_ids: Collection[str],
) -> list[dict[str, str]]:
    if not newly_externalized:
        raise ValueError("batched maintenance requires at least one exact result")
    prior_body = (
        f"{INTEGRATION_PREFIX}\n\nNo accepted evidence has been integrated yet."
        if prior is None
        else prior.body
    )
    allowed = ", ".join(sorted(set(allowed_source_ids))) or "none"
    system = f"""# BATCHED_EVIDENCE_INTEGRATION maintenance mode

Return only a complete replacement Markdown evidence-integration ledger whose
first line is exactly `{INTEGRATION_PREFIX}`. Do not take an ordinary task
action. Integrate the exact batch with the prior task work, preserving units,
probabilities, revisions, qualifications, contradictions, cross-source
relationships, R01-R12 bindings, and unresolved blockers.

The output is model-authored and lossy. It cannot authorize readiness or
submission. Replace prior material rather than appending indefinitely. Keep it
under the hard {BATCHED_INTEGRATION_TOKEN_BUDGET}-token limit. The only source IDs you
may cite are: {allowed}."""
    observations = "\n\n".join(
        f"## Externalized exact result {record.result_id}\n\n{record.exact_content}"
        for record in newly_externalized
    )
    user = f"""# Authoritative task

{task_text}

# Prior accepted integration ledger

{prior_body}

# Mechanically batched exact externalized observations

{observations}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def next_artifact(
    *,
    prior: IntegrationArtifact | None,
    body: str,
    body_tokens: int,
    result: ResultRecord,
) -> IntegrationArtifact:
    result_ids = list(prior.input_result_ids if prior else ())
    if result.result_id not in result_ids:
        result_ids.append(result.result_id)
    sources = set(prior.observed_source_ids if prior else ())
    sources.update(observed_source_ids(result))
    return IntegrationArtifact(
        version=1 if prior is None else prior.version + 1,
        body=body,
        body_tokens=body_tokens,
        input_result_ids=tuple(result_ids),
        observed_source_ids=tuple(sorted(sources)),
    )


def next_artifact_batch(
    *,
    prior: IntegrationArtifact | None,
    body: str,
    body_tokens: int,
    results: Sequence[ResultRecord],
) -> IntegrationArtifact:
    if not results:
        raise ValueError("batched artifact requires at least one result")
    result_ids = list(prior.input_result_ids if prior else ())
    sources = set(prior.observed_source_ids if prior else ())
    for result in results:
        if result.result_id not in result_ids:
            result_ids.append(result.result_id)
        sources.update(observed_source_ids(result))
    return IntegrationArtifact(
        version=1 if prior is None else prior.version + 1,
        body=body,
        body_tokens=body_tokens,
        input_result_ids=tuple(result_ids),
        observed_source_ids=tuple(sorted(sources)),
    )
