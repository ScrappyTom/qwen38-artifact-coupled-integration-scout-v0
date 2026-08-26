"""Materialize the deterministic synthetic Aster payment-recovery world."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DESTINATION = ROOT / "task_aster" / "sources"


@dataclass(frozen=True)
class SourceSpec:
    filename: str
    title: str
    domain: str
    prefix: str
    assets: tuple[str, ...]
    base_measure: float
    unit: str
    findings: tuple[str, str, str]
    relationships: tuple[str, str]
    constraints: tuple[str, str]


def row(spec: SourceSpec, index: int) -> tuple[str, str, str, str, str, str]:
    asset = spec.assets[index % len(spec.assets)]
    measure = spec.base_measure + ((index * 11) % 29) / 10
    status = "superseded" if index % 17 == 0 else "current"
    return (
        f"{spec.prefix}-{index:03d}",
        asset,
        f"v{3 + index // 14}",
        f"{measure:.1f}",
        spec.unit,
        status,
    )


def document(spec: SourceSpec) -> str:
    lines = [
        f"# {spec.title}",
        "",
        "## Frozen findings",
        "",
        *spec.findings,
        "",
        "## Governing relationships",
        "",
        *spec.relationships,
        "",
        "## Operational evidence",
        "",
        "| record | object/region | version | measure | unit | status |",
        "|---|---|---|---:|---|---|",
    ]
    lines.extend(
        "| " + " | ".join(values) + " |"
        for values in (row(spec, index) for index in range(42))
    )
    lines.extend(["", "## Decision constraints", "", *spec.constraints, ""])
    return "\n".join(lines)


SPECS = (
    SourceSpec(
        "ANCHOR_AUTHORITY.md",
        "Incident authority, release control, and accountable closure",
        "authority",
        "AUTH",
        ("incident-command", "risk-owner", "settlement-owner", "regulator"),
        1.0,
        "approval",
        (
            "The incident commander may isolate traffic and approve a recovery sequence. Only the payment risk owner may authorize customer-traffic restoration, and only after a current independent verification result; an engineering mutation or green format check is not authorization.",
            "Emergency vendor purchasing does not waive access review, ledger consistency, idempotency, settlement, or regulatory controls. Closure requires accountable-executive acceptance of every declared blocker and residual risk.",
            "A handoff is valid only when the receiving owner acknowledges the same recovery-candidate, ledger-schema, queue-policy, and key-set versions. An unacknowledged version mismatch blocks closure.",
        ),
        (
            "BRIDGE and CIRRUS supply ledger and retry evidence but cannot authorize restoration. PRISM supplies independent readiness findings but does not execute the release.",
            "NOVA owns rollback mechanics; ANCHOR retains authority separation among detection, recommendation, authorization, execution, verification, and closure.",
        ),
        (
            "Name who may isolate, repair, verify, restore, and close, with the exact evidence each decision consumes.",
            "Treat semantic records and candidate mutations as non-authoritative work products.",
        ),
    ),
    SourceSpec(
        "BRIDGE_LEDGER.md",
        "Ledger replication, consistency, and recovery-point evidence",
        "ledger",
        "LEDG",
        ("east-writer", "west-replica", "settlement-log", "balance-view"),
        1800.0,
        "milliseconds-p95",
        (
            "Current cross-region ledger replication lag is 1,800 milliseconds at p95. The traffic-restoration block is 2.5 seconds sustained for three five-minute windows; 1,800 ms must not be converted to 1,800 seconds or treated as zero lag.",
            "The recovery point objective is fifteen seconds and the recovery time objective is forty-five minutes. Those are different controls and neither is the observed replication lag.",
            "A schema or writer-route change makes prior consistency and replay checks stale for the changed candidate. Current verification must bind the candidate, schema, writer, and settlement-log versions.",
        ),
        (
            "CIRRUS retry safety depends on BRIDGE ledger uniqueness and DUSK queue position. FORGE settlement release consumes a BRIDGE-consistent cutoff.",
            "NOVA rollback is permitted only while the old schema remains readable and a current BRIDGE consistency check passes for the rollback candidate.",
        ),
        (
            "Preserve milliseconds, seconds, the three-window rule, RPO, RTO, and candidate currency.",
            "Distinguish replicated bytes, consistent balances, and authority to restore traffic.",
        ),
    ),
    SourceSpec(
        "CIRRUS_IDEMPOTENCY.md",
        "Idempotency keys, retry windows, and duplicate-payment controls",
        "transaction_safety",
        "IDEM",
        ("api-key", "merchant-key", "retry-cache", "dedupe-log"),
        45.0,
        "minutes",
        (
            "The idempotency retention window is forty-five minutes for API retries and two hours for delayed merchant acknowledgments. Neither window is a transaction timeout.",
            "Keys are unique only within merchant and operation scope. Reusing one key across capture and refund is unsafe even when the amount matches.",
            "The current duplicate-payment observation is 0.08 percent of attempted retries, not 0.08 probability and not an eight-percent customer rate.",
        ),
        (
            "CIRRUS retry release requires a BRIDGE-consistent ledger position and a DUSK queue policy that preserves the same idempotency key. GROVE fraud holds remain separate from duplicate suppression.",
            "NOVA rollback must retain the dedupe log for the full CIRRUS window or explicitly suspend retries.",
        ),
        (
            "State the key scope, both retention windows, duplicate observation, and retry retirement evidence.",
            "Do not infer ledger consistency, fraud clearance, or restoration authority from key presence.",
        ),
    ),
    SourceSpec(
        "DUSK_QUEUE.md",
        "Queue backlog, replay order, and drain constraints",
        "queue",
        "QUE",
        ("capture", "refund", "webhook", "settlement"),
        1200.0,
        "messages-per-second",
        (
            "The durable queue contains 3.6 million pending messages. The observed safe drain rate is 1,200 messages per second while live ingress is capped at 400 per second; the rate is not messages per minute.",
            "Refund and reversal events must preserve account order. Webhooks may be delayed, but capture acknowledgments cannot pass an unresolved ledger write.",
            "The restore gate is backlog below 200,000 plus a current fifteen-minute zero-ordering-error observation. Backlog alone is not sufficient.",
        ),
        (
            "CIRRUS supplies retry identity; BRIDGE supplies ledger position; EMBER supplies capacity headroom. All three constrain DUSK replay sequencing.",
            "LATTICE alerts on rate and ordering, while ORBIT documents an earlier exercise that used an obsolete queue-policy version.",
        ),
        (
            "Calculate drain opportunity using both drain and live-ingress rates and preserve event ordering.",
            "Name the current evidence that starts, pauses, resumes, and retires replay controls.",
        ),
    ),
    SourceSpec(
        "EMBER_CAPACITY.md",
        "Service capacity, dependency headroom, and traffic ramps",
        "capacity",
        "CAP",
        ("api", "ledger", "queue", "fraud"),
        24.0,
        "thousand-tps",
        (
            "The API tier is rated for 31,000 transactions per second and the ledger tier for 27,000, but both share a dependency capped at 24,000 TPS. The tier ratings cannot be summed.",
            "The latest inspected run sustained 21,600 TPS after fraud and logging overhead. A higher ramp requires a current candidate-bound load test.",
            "Traffic may increase in 10, 25, 50, and 100 percent stages only after two ten-minute windows meet latency, error, queue, and ledger gates.",
        ),
        (
            "DUSK drain competes with live traffic for EMBER capacity. JUNIPER rail availability and LATTICE telemetry determine whether a ramp observation is usable.",
            "A service limit, dependency allocation, logging policy, or candidate change makes prior load evidence stale.",
        ),
        (
            "Preserve shared capacity, observed sustainable rate, stage sequence, windows, and stale conditions.",
            "Do not convert nominal component ratings into usable system capacity.",
        ),
    ),
    SourceSpec(
        "FORGE_SETTLEMENT.md",
        "Settlement cutoffs, funding, and ledger finality",
        "settlement",
        "SET",
        ("domestic", "cross-border", "card", "bank-transfer"),
        17.0,
        "hour-utc",
        (
            "The domestic settlement cutoff is 17:00 UTC and the cross-border cutoff is 15:30 UTC. Missing a cutoff delays finality; it does not erase customer authorization.",
            "The current prefunding requirement is 6.4 million dollars with a 0.9-million contingency. Amounts are cash obligations, not transaction counts.",
            "Settlement files require a BRIDGE-consistent ledger cutoff and a MICA reconciliation sample before release.",
        ),
        (
            "JUNIPER reports rail availability, KELP governs reportable settlement delay, and HARBOR governs customer-facing pending status.",
            "A BRIDGE schema or cutoff mutation makes FORGE file checks stale until regenerated and reconciled.",
        ),
        (
            "Separate authorization, capture, ledger posting, settlement-file release, and finality.",
            "State funding owner, cutoff decision, delay contingency, and exact release evidence.",
        ),
    ),
    SourceSpec(
        "GROVE_FRAUD.md",
        "Fraud controls, hold thresholds, and manual review capacity",
        "risk",
        "RISK",
        ("card", "bank", "merchant", "account"),
        0.8,
        "percent-review-rate",
        (
            "The current manual-review rate is 0.8 percent of authorized payments. It is not 0.8 probability, 80 percent, or a duplicate-payment measure.",
            "A risk-score alert begins at 720; an automatic hold begins at 860. The alert and hold thresholds must remain distinct.",
            "Manual review capacity is 9,500 cases per hour for two hours, then 6,200 per hour. Backlog above 18,000 blocks a full traffic ramp.",
        ),
        (
            "CIRRUS duplicate suppression is independent of GROVE fraud disposition. LATTICE supplies current score-distribution and false-positive telemetry.",
            "HARBOR communications must not call a pending fraud review a declined or settled payment.",
        ),
        (
            "Preserve percent, score thresholds, time-varying capacity, backlog gate, and separate control purposes.",
            "Name what evidence can retire a hold without weakening fraud controls.",
        ),
    ),
    SourceSpec(
        "HARBOR_CUSTOMER.md",
        "Customer state, merchant notices, and support continuity",
        "customer",
        "CUST",
        ("consumer", "merchant", "support", "status-page"),
        94.0,
        "percent-delivered",
        (
            "Status notices reached 94 percent of enrolled merchants; the missing six percent is a communication uncertainty, not a six-percent reduction in affected merchants.",
            "Customer-visible states must distinguish pending, authorized, captured, reversed, refunded, and settled. A delayed webhook does not by itself change ledger state.",
            "Support can sustain 4,800 contacts per hour for four hours. The surge forecast is 6,100 per hour unless proactive notices reduce contacts.",
        ),
        (
            "FORGE defines settlement status and MICA defines reconciliation exceptions. GROVE defines fraud holds that HARBOR must describe without disclosing risk logic.",
            "KELP supplies mandatory regulatory language; ANCHOR owns public restoration approval.",
        ),
        (
            "Preserve delivery coverage, state vocabulary, contact capacity, forecast, privacy, and escalation.",
            "State owners, channels, timing, acknowledgment, alternate routes, and retirement evidence.",
        ),
    ),
    SourceSpec(
        "IRIS_SECURITY.md",
        "Key rotation, privileged access, and audit evidence",
        "security",
        "SEC",
        ("signing-key", "service-token", "admin-role", "audit-log"),
        12.0,
        "hours",
        (
            "The compromised service token was revoked at 12:20 UTC. The signing key was not compromised and remains current under key-set version K7.",
            "Break-glass administrator access expires after two hours and requires dual approval plus immutable session logging. Emergency access is not continuing authorization.",
            "The audit log retains online events for ninety days and archived events for seven years; these periods serve different obligations.",
        ),
        (
            "ANCHOR governs emergency authority and NOVA binds rollback to the current key set. LATTICE consumes IRIS audit events but does not authorize access.",
            "Any key-set, role-policy, or logging mutation makes prior security verification stale.",
        ),
        (
            "Distinguish token revocation, uncompromised key status, access duration, approvals, and retention periods.",
            "Name the current evidence required before restoring privileged automation.",
        ),
    ),
    SourceSpec(
        "JUNIPER_RAILS.md",
        "External payment rails, observed availability, and fallback",
        "vendors",
        "RAIL",
        ("rail-A", "rail-B", "card-network", "bank-network"),
        99.7,
        "percent-availability",
        (
            "Rail A reports 99.7 percent endpoint availability, but successful authorization is 98.9 percent because issuer declines remain separate. Availability is not payment success.",
            "Rail B's contractual restoration target is four hours; the observed restoration in the last event was six hours and twenty minutes. Target and observation must not be swapped.",
            "Fallback routing adds 220 milliseconds p95 and a 0.12-percent fee increment. Both must be included in capacity and cost decisions.",
        ),
        (
            "EMBER must retain headroom for fallback latency and DUSK replay. FORGE cutoffs constrain whether delayed rail traffic can settle the same day.",
            "KELP reporting may be triggered by customer impact even if contractual rail availability remains above target.",
        ),
        (
            "Preserve availability, success, target, observed duration, latency, and fee units.",
            "State rail-selection owner, fallback gate, rollback, and evidence for normal routing.",
        ),
    ),
    SourceSpec(
        "KELP_REGULATORY.md",
        "Incident reporting, materiality, and evidence retention",
        "compliance",
        "REG",
        ("incident", "settlement", "customer", "audit"),
        72.0,
        "hours",
        (
            "A material payment-availability incident requires initial notice within seventy-two hours of determination, not seventy-two minutes after detection.",
            "Customer financial-loss reports above 250,000 dollars aggregate trigger executive escalation; the amount is not a per-customer threshold.",
            "Evidence for the determination, notices, candidate changes, checks, and closure must be retained for seven years with access provenance.",
        ),
        (
            "FORGE supplies settlement impact and MICA supplies reconciled loss estimates. HARBOR supplies notice delivery and acknowledgment evidence.",
            "ANCHOR owns determination and executive escalation; a semantic source record cannot make the legal determination.",
        ),
        (
            "Preserve the trigger event, seventy-two-hour clock, aggregate loss, retention, and responsible authority.",
            "State unknowns and the evidence that could change materiality.",
        ),
    ),
    SourceSpec(
        "LATTICE_TELEMETRY.md",
        "Telemetry coverage, alert thresholds, and observation quality",
        "observability",
        "OBS",
        ("latency", "errors", "ordering", "fraud-score"),
        97.0,
        "percent-coverage",
        (
            "Telemetry covers 97 percent of production transactions. The missing three percent requires an uncertainty allowance and is not evidence of zero errors.",
            "The latency alert is 900 milliseconds p95 and the traffic hold is 1,400 milliseconds p95 for two consecutive five-minute windows. Alert and hold thresholds differ.",
            "Ordering error above 0.02 percent pauses queue replay. The latest current observation is 0.006 percent over fifteen minutes.",
        ),
        (
            "DUSK supplies queue ordering and GROVE supplies fraud-score distributions. EMBER load tests are usable only when LATTICE coverage and version binding are current.",
            "IRIS governs audit-event integrity; LATTICE dashboards alone do not establish security or readiness.",
        ),
        (
            "Preserve coverage uncertainty, milliseconds, consecutive windows, ordering percentages, and observation horizon.",
            "Name missing telemetry, fallback observation, pause, resume, and falsifier evidence.",
        ),
    ),
    SourceSpec(
        "MICA_RECONCILIATION.md",
        "Reconciliation samples, exception rates, and loss estimates",
        "reconciliation",
        "REC",
        ("capture", "refund", "settlement", "customer-loss"),
        2.4,
        "percent-sample",
        (
            "The current reconciliation sample covers 2.4 percent of affected transactions, stratified by payment rail and operation. It is not a 2.4-percent loss rate.",
            "Observed unmatched ledger events are 0.14 percent of the sample. The release threshold is below 0.05 percent in two independent samples.",
            "The provisional customer-loss estimate is 310,000 dollars with a 90-percent interval from 240,000 to 430,000 dollars. The interval is not a probability of loss.",
        ),
        (
            "FORGE requires a MICA sample before settlement-file release. HARBOR uses reconciled state for customer correction, and KELP uses the loss estimate for escalation.",
            "A BRIDGE schema, DUSK replay, or candidate change makes the prior sample stale for affected transactions.",
        ),
        (
            "Preserve sampling basis, exception rate, two-sample rule, estimate, interval, and candidate currentness.",
            "State who expands the sample and what observation retires reconciliation blockers.",
        ),
    ),
    SourceSpec(
        "NOVA_ROLLBACK.md",
        "Rollback compatibility, candidate lineage, and recovery gates",
        "change_control",
        "ROLL",
        ("candidate-R4", "candidate-R5", "schema-12", "schema-13"),
        35.0,
        "minutes",
        (
            "Candidate R5 changes queue batching and audit fields while retaining schema-12 read compatibility. The rollback estimate is thirty-five minutes if no schema-13-only write has occurred.",
            "After a schema-13-only write, rollback requires a forward repair rather than direct reversion. Candidate identity and write history therefore govern the rollback path.",
            "A check against R4 or pre-mutation R5 remains historical evidence but is stale after any R5 candidate effect until rerun.",
        ),
        (
            "BRIDGE supplies schema and ledger consistency; IRIS supplies key-set and access currency. Both must bind the same NOVA candidate before rollback or restoration.",
            "ORBIT's exercise used R4 and cannot prove R5 readiness. PRISM independently reviews the current candidate and check set.",
        ),
        (
            "Preserve candidate IDs, schema compatibility, write-history condition, duration, and stale-check rule.",
            "State rollback owner, trigger, exact preconditions, effect uptake, recheck, and abandonment condition.",
        ),
    ),
    SourceSpec(
        "ORBIT_EXERCISE.md",
        "Prior recovery exercise, observed defects, and transfer limits",
        "exercise",
        "EX",
        ("queue", "ledger", "security", "communications"),
        61.0,
        "minutes",
        (
            "The prior exercise restored test traffic in sixty-one minutes against a forty-five-minute target. It used candidate R4, queue policy Q8, and synthetic issuer responses.",
            "The exercise missed a refund-ordering defect and did not test cross-border settlement or break-glass access expiry. Those omissions remain open rather than passed.",
            "A later tabletop estimated an 18-percent probability that queue replay would exceed two hours under simultaneous rail degradation. This is a scenario probability, not observed duration or readiness.",
        ),
        (
            "DUSK and NOVA now use newer versions than the exercise. JUNIPER's simultaneous rail condition is the scenario input, not an observed current outage.",
            "PRISM may use ORBIT as historical evidence but must require current candidate-bound verification for closure.",
        ),
        (
            "Preserve target versus observation, exact versions, untested areas, and scenario probability.",
            "Do not promote historical exercise evidence to current readiness.",
        ),
    ),
    SourceSpec(
        "PRISM_READINESS.md",
        "Independent readiness review, blockers, and falsifiers",
        "readiness",
        "READY",
        ("authority", "ledger", "queue", "customer"),
        12.0,
        "criteria",
        (
            "The readiness board evaluates twelve criteria against one exact candidate and evidence manifest. Its recommendation is advisory until the ANCHOR authority records a decision.",
            "Open blockers include stale candidate checks, ledger inconsistency, queue-ordering failure, unbounded customer loss, expired emergency access, and missing regulatory determination.",
            "A submission, candidate mutation, semantic register, or mechanically green format check does not establish readiness. Every blocker requires exact current evidence or an explicit accepted residual risk by the authorized owner.",
        ),
        (
            "PRISM consumes current evidence from ANCHOR, BRIDGE, DUSK, IRIS, KELP, MICA, and NOVA. It does not replace those source authorities.",
            "ORBIT is historical context only. Any post-review candidate effect makes the prior readiness review stale.",
        ),
        (
            "List blockers, falsifiers, residual risks, evidence versions, and independent owners.",
            "Closure requires current candidate-bound review plus ANCHOR authority; do not self-authorize.",
        ),
    ),
)

SOURCE_IDS = (
    "ANCHOR",
    "BRIDGE",
    "CIRRUS",
    "DUSK",
    "EMBER",
    "FORGE",
    "GROVE",
    "HARBOR",
    "IRIS",
    "JUNIPER",
    "KELP",
    "LATTICE",
    "MICA",
    "NOVA",
    "ORBIT",
    "PRISM",
)


def main() -> int:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for spec in SPECS:
        (DESTINATION / spec.filename).write_text(
            document(spec), encoding="utf-8", newline=""
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
