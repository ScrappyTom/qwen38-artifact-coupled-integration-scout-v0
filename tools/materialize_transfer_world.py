from __future__ import annotations

"""Materialize the frozen synthetic Northstar transfer world.

The prose facts below are the authored source of truth.  The tabular records
are deterministic expansions used to create realistic evidence volume and
cross-source reconciliation work; they do not introduce random values.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "task" / "transfer_sources"


def table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> list[str]:
    output = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    output.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return output


def document(title: str, sections: list[tuple[str, list[str]]]) -> str:
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.extend([f"## {heading}", "", *body, ""])
    return "\n".join(lines).rstrip() + "\n"


def s01() -> str:
    rows: list[tuple[object, ...]] = []
    components = ("edge", "validator", "legacy-queue", "streamcore", "materializer", "reconciler")
    regions = ("us-east", "us-west", "eu-central")
    for hour in range(24):
        for region_index, region in enumerate(regions):
            component = components[(hour + region_index) % len(components)]
            rows.append((f"T{hour:02d}-{region_index}", region, component, 2 + (hour + region_index) % 4, "active-active" if component != "legacy-queue" else "active-passive", f"topology-rev-{7 + hour // 8}"))
    return document("Northstar topology and migration target", [
        ("Authoritative scope", [
            "Northstar accepts customer events through regional edge gateways and currently commits them to LegacyQueue. The approved migration target is StreamCore, but the cutover must preserve the externally visible event contract rather than merely keep processes running.",
            "The three production regions are us-east, us-west, and eu-central. EU-tagged payloads must remain inside eu-central. A regional outage may not silently convert an EU event into a US event.",
            "The migration unit is a tenant cohort. A global all-at-once switch is prohibited. Each cohort can be shadowed, dual-written, promoted, held, or rolled back subject to the schema and residency rules in the other sources.",
        ]),
        ("Data path", [
            "The edge gateway validates the envelope and assigns the authoritative producer_id:event_id idempotency key. The validator attaches tenant_policy, residency_tag, and schema_version before any durable write.",
            "LegacyQueue is the current authority. During dual-write, StreamCore is a candidate path and the reconciler compares both paths. After cohort promotion, StreamCore becomes authoritative only after the promotion effect is recorded in the control ledger.",
            "The materializer exposes committed events to downstream readers. An ingest acknowledgement is not evidence that the materializer has made the event visible.",
        ]),
        ("Topology inventory", table(("record", "region", "component", "replicas", "mode", "declared revision"), rows)),
        ("Known coupling", [
            "The validator and materializer deploy independently, but schema v3 requires both to understand tenant_policy and residency_tag. Promoting ingest without current materializer verification can create durable but unreadable events.",
            "The reconciler is an operational control, not the data authority. Its reports are candidate-version-bound observations and become stale after routing, schema, or deduplication changes.",
        ]),
    ])


def s02() -> str:
    rows: list[tuple[object, ...]] = []
    tiers = ("gold", "silver", "bronze")
    regions = ("us-east", "us-west", "eu-central")
    for hour in range(72):
        region = regions[hour % 3]
        tier = tiers[(hour // 3) % 3]
        ingest = 78_000 + (hour * 1_913) % 44_000
        p99 = 3.1 + ((hour * 7) % 16) / 10
        if tier == "bronze" and hour % 9 in (6, 7, 8):
            p99 = 9.6 + (hour % 5) * 0.8
        duplicate_rate = 0.006 + ((hour * 11) % 9) / 1000
        rows.append((f"H{hour:03d}", region, tier, ingest, f"{p99:.1f}", f"{duplicate_rate:.3f}%", "pass" if p99 <= 8.0 else "tail-breach"))
    return document("Northstar service objectives and traffic evidence", [
        ("Frozen service objectives", [
            "Successful migration requires all of the following simultaneously: monthly ingest availability at least 99.95%; event-loss probability no greater than one per million accepted events; duplicate delivery no greater than 0.02%; and commit-to-visible latency of at most four seconds at the 99.9th percentile.",
            "A second latency guard is tenant-local: every tenant tier must remain at or below eight seconds at p99. Fleet averages and region averages are not acceptable substitutes because they can hide a low-volume cohort regression.",
            "The readiness gate uses the worse of regional and tenant-cohort measurements. A rollout that improves the fleet aggregate while breaching bronze tenants is a failed rollout.",
        ]),
        ("Observed load", table(("window", "region", "tier", "events/s", "commit-visible p99 s", "duplicates", "classification"), rows)),
        ("Interpretation constraints", [
            "The sample includes repeated bronze tail breaches even while the blended fleet statistic remains below four seconds. Promotion gates must query per-tenant distributions, not only the dashboard headline.",
            "Traffic grows by cohort and time of day. Capacity claims must be bound to the candidate routing revision and tested at the planned dual-write percentage.",
        ]),
    ])


def s03() -> str:
    rows: list[tuple[object, ...]] = []
    outcomes = ("accepted", "retry-before-ack", "retry-after-ack", "late-replay", "producer-reset")
    for index in range(180):
        delay = (index * 17) % 46
        outcome = outcomes[index % len(outcomes)]
        dedup = "hit" if delay <= 24 and outcome != "producer-reset" else "miss"
        rows.append((f"P{index:03d}", f"producer-{index % 12:02d}", f"event-{index:05d}", outcome, f"{delay}h", dedup))
    return document("Delivery, acknowledgement, and idempotency contract", [
        ("Identity and acknowledgement", [
            "The only authoritative idempotency key is producer_id:event_id. A transport batch ID identifies a shipment and may be reused after a producer restart; it is not an event identity and must never drive deduplication.",
            "The gateway may acknowledge an event only after the authoritative path has committed it to two availability zones and persisted the idempotency key. A socket write, broker receipt, or batch acceptance is not a commit acknowledgement.",
            "StreamCore consumers are at-least-once. Exactly-once delivery is not promised. The system objective is idempotent observable effects with auditable duplicate bounds.",
        ]),
        ("Retention conflict", [
            "The original StreamCore proposal set the deduplication horizon to 24 hours. Producer incident evidence contains legitimate retries 31 hours after acknowledgement. The migration decision must raise the minimum deduplication horizon to 48 hours or supply an equally explicit mechanism that covers those retries.",
            "A producer epoch can change only through the authenticated reset workflow. An unannounced producer restart does not authorize erasing prior idempotency state.",
        ]),
        ("Replay examples", table(("record", "producer", "event", "condition", "delay", "24h cache result"), rows)),
        ("Required tests", [
            "Tests must cover retries before and after acknowledgement, a 31-hour replay, producer restart with reused batch ID, duplicate delivery across a regional handoff, and expiry at the selected horizon.",
        ]),
    ])


def s04() -> str:
    rows: list[tuple[object, ...]] = []
    for producer in range(24):
        for version in (1, 2, 3):
            readable = "yes" if version < 3 or producer % 4 != 0 else "requires-new-materializer"
            legacy_roundtrip = "lossless" if version < 3 else "drops-tenant_policy-and-residency_tag"
            rows.append((f"producer-{producer:02d}", f"v{version}", readable, legacy_roundtrip, "block" if version == 3 and readable != "yes" else "allow"))
    return document("Schema compatibility and rollback boundaries", [
        ("Schema rules", [
            "Schema v1 is the legacy envelope. Schema v2 adds optional trace metadata and can round-trip through LegacyQueue. Schema v3 makes tenant_policy and residency_tag mandatory and is the first format used to enforce tenant-local policy at ingest.",
            "LegacyQueue cannot preserve the two v3 fields. Sending an accepted v3 event back through the legacy path silently drops them. Therefore an ordinary failback after v3 promotion is unsafe unless an explicit lossless down-conversion or retained dual representation has been proven.",
            "The current migration proposal contains no lossless v3-to-v1 conversion. Once a cohort accepts v3-only events, rollback means stop new promotion and forward-fix StreamCore; it does not mean route those events through LegacyQueue.",
        ]),
        ("Compatibility matrix", table(("producer", "schema", "current reader", "legacy round-trip", "promotion disposition"), rows)),
        ("Version gates", [
            "Before v3 promotion, the validator, StreamCore decoder, materializer, reconciler, replay tooling, and audit exporter must all pass the same candidate-bound compatibility suite.",
            "A check run against the prior schema bundle becomes stale after any component or routing mutation. Readiness must name the exact bundle hash that was tested.",
        ]),
    ])


def s05() -> str:
    rows: list[tuple[object, ...]] = []
    stages = (("shadow", 0), ("canary", 5), ("cohort-1", 25), ("cohort-2", 50), ("cohort-3", 75), ("complete", 100))
    for region in ("us-east", "us-west", "eu-central"):
        for name, percent in stages:
            dwell = 2 if percent <= 5 else 6 if percent <= 50 else 12
            rows.append((region, name, f"{percent}%", f"{dwell}h", "candidate-bound check + reconciliation", "automatic hold on any hard gate"))
    return document("Rollout, hold, and rollback policy", [
        ("Default sequence", [
            "The standard cohort sequence is shadow, 5%, 25%, 50%, 75%, and 100%. Advancement is never time-only: the minimum dwell and every service, reconciliation, residency, security, and capacity gate must pass for the exact candidate.",
            "Any event loss, unauthorized cross-region payload movement, schema corruption, or current check failure is a hard hold. Duplicate or latency breaches are also holds when they exceed the frozen objectives.",
            "The generic disaster-recovery appendix says traffic may fail to any healthy region. That generic rule is overridden for EU-tagged payloads by the compliance source: EU payloads may fail only to an approved EU-resident target, otherwise ingest must fail closed while metadata-only status remains available.",
        ]),
        ("Rollback semantics", [
            "Before v3-only acceptance, rollback may restore LegacyQueue authority after reconciliation confirms no unrepresented events. After v3-only acceptance, the safe response is halt advancement, retain StreamCore authority for accepted v3 events, and forward-fix or replay from the EU/region-local spool.",
            "Every mutation to routing, schema, deduplication, or materializer code invalidates the prior check. A new check and at least one clean dwell window are required before advancement.",
        ]),
        ("Stage matrix", table(("region", "stage", "traffic", "minimum dwell", "advance evidence", "failure action"), rows)),
        ("Authority", [
            "The release commander can hold or roll back within the safe envelope. Compliance owns residency exceptions. The data-integrity lead owns reconciliation acceptance. No single actor may waive a hard gate and declare readiness.",
        ]),
    ])


def incident_rows(prefix: str, count: int, delay_multiplier: int, region: str, classification: str) -> list[tuple[object, ...]]:
    rows = []
    for index in range(count):
        minute = index * 7
        delay = (index * delay_multiplier) % 1_980
        rows.append((f"{prefix}-{index:03d}", f"+{minute:04d}m", region, f"tenant-{index % 17:02d}", f"{delay}m", classification if index % 11 == 0 else "observed", f"candidate-r{3 + index // 70}"))
    return rows


def s06() -> str:
    return document("Incident E-17: delayed replay and duplicate storm", [
        ("Disposition", [
            "E-17 followed a producer restart. The producer reused a transport batch ID and replayed accepted events 31 hours after the original acknowledgement. The 24-hour deduplication cache had expired.",
            "The candidate implementation keyed deduplication by batch ID instead of producer_id:event_id. It emitted 1.7 million duplicate downstream effects before the cohort was held. No source event was lost, but customer-visible balances were temporarily double-counted.",
            "The corrective action requires event-level keys, a minimum 48-hour deduplication horizon, and a test whose replay occurs after hour 31. Increasing a cache without correcting identity is insufficient.",
        ]),
        ("Event log", table(("event", "time", "region", "tenant", "replay delay", "classification", "candidate"), incident_rows("E17", 210, 19, "us-east", "duplicate-confirmed"))),
        ("Closure evidence", [
            "The incident is not closed by a passing fleet-average duplicate rate. The affected cohort must reconcile to the authoritative event cardinality and downstream effects must be compensated exactly once.",
        ]),
    ])


def s07() -> str:
    return document("Incident E-23: EU residency failover violation", [
        ("Disposition", [
            "During an eu-central broker impairment, the generic global failover rule routed EU-tagged payloads to us-east for 23 minutes. Payload confidentiality was preserved in transit, but location policy was violated because encryption does not change residency.",
            "The incident review requires an EU-resident secondary or fail-closed ingest for EU payloads. Metadata-only health and backpressure signals may leave the region; raw payloads, replay spools, and dead-letter bodies may not.",
            "A future plan must explicitly override the generic disaster-recovery appendix and separately test routing for EU payloads, EU metadata, and non-EU traffic.",
        ]),
        ("Routing log", table(("event", "time", "region", "tenant", "queue delay", "classification", "candidate"), incident_rows("E23", 210, 5, "eu-central", "residency-breach"))),
        ("Open control", [
            "The approved near-term control is a twelve-hour encrypted spool inside eu-central plus fail-closed behavior when both EU paths are unavailable. Cross-region metadata must contain no payload fragments.",
        ]),
    ])


def s08() -> str:
    return document("Incident E-31: dependency outage beyond SLA", [
        ("Disposition", [
            "StreamCore's managed control plane was unavailable for 11 hours and 8 minutes. The vendor target said four hours, but the event fell under a regional dependency exclusion and service was not restored within that target.",
            "The local spool held six hours of peak traffic. After it filled, us-west rejected new events and two producers discarded retries. The postmortem therefore requires twelve hours of region-local spool capacity at projected peak, with backpressure before exhaustion.",
            "The release plan may use the vendor SLA for escalation timing but may not use it as the sole continuity control. Recovery exercises must assume at least a twelve-hour control-plane loss.",
        ]),
        ("Outage timeline", table(("event", "time", "region", "tenant", "queue delay", "classification", "candidate"), incident_rows("E31", 210, 13, "us-west", "dependency-unavailable"))),
        ("Required follow-up", [
            "Capacity, spool encryption, replay order, and producer backpressure must be tested together. A larger spool without replay and deduplication tests can convert an outage into a delayed duplicate storm.",
        ]),
    ])


def s09() -> str:
    rows = []
    for tenant in range(60):
        tier = ("gold", "silver", "bronze")[tenant % 3]
        base = 2.2 + (tenant % 7) * 0.35
        p99 = base + (8.2 if tier == "bronze" and tenant % 4 == 2 else 0)
        p999 = p99 + 1.1 + (tenant % 5) * 0.4
        rows.append((f"tenant-{tenant:02d}", tier, 900 + tenant * 113, f"{p99:.2f}", f"{p999:.2f}", "hold" if p99 > 8 else "pass"))
    return document("Tail-latency and cohort telemetry review", [
        ("Finding", [
            "The fleet dashboard reported commit-to-visible p99 of 3.8 seconds during the 25% candidate run. Tenant-level analysis found bronze cohorts between 10.4 and 13.7 seconds. Low bronze volume hid the breach in the aggregate.",
            "Promotion requires per-tenant p99, regional p99.9, duplicate rate, loss, reconciliation lag, spool fill, and backpressure. Every metric must be tagged with candidate hash, cohort, region, and schema version.",
            "A dashboard without candidate binding cannot establish current readiness after a deployment or routing change.",
        ]),
        ("Tenant slice", table(("tenant", "tier", "events/s", "p99 s", "p99.9 s", "gate"), rows)),
        ("Decision rule", [
            "Any tenant above eight seconds p99 holds that cohort even if the fleet aggregate passes. The remedy must be checked against the same tenant slice before release resumes.",
        ]),
    ])


def s10() -> str:
    rows = []
    for index in range(240):
        region = ("us-east", "us-west", "eu-central")[index % 3]
        tenant = f"tenant-{index % 41:02d}"
        expected = 90_000 + (index * 8_137) % 60_000
        delta = 0 if index % 17 else 3 + index % 9
        hash_match = "yes" if delta == 0 and index % 29 else "no"
        rows.append((f"W{index:03d}", region, tenant, expected, expected - delta, hash_match, "hold" if delta or hash_match == "no" else "pass"))
    return document("Shadow reconciliation and data-integrity audit", [
        ("Required comparison", [
            "Shadow validation must compare LegacyQueue and StreamCore for every tenant-hour using accepted-event cardinality, ordered event identity, payload hash, schema version, residency tag, and materialized effect count. A one-percent sample is insufficient for promotion.",
            "Zero unexplained loss and zero residency mismatch are hard gates. Duplicate effects must remain within 0.02% and every explained exclusion must have an exact reason code and owner.",
            "Reconciliation output is current only for the candidate routing, decoder, materializer, and deduplication bundle it evaluated.",
        ]),
        ("Audit rows", table(("window", "region", "tenant", "legacy count", "stream count", "hash match", "gate"), rows)),
        ("Repair rule", [
            "A mismatch produces a hold, a candidate-bound defect, and a repair/recheck cycle. Re-running the old report after code changes does not make it current.",
        ]),
    ])


def s11() -> str:
    rows = []
    controls = ("residency", "encryption", "access", "retention", "audit", "deletion")
    for index in range(144):
        control = controls[index % len(controls)]
        rows.append((f"C{index:03d}", control, ("EU", "US", "global-metadata")[index % 3], "required", f"owner-{index % 8}", f"review-{1 + index // 24}"))
    return document("Security, privacy, retention, and audit controls", [
        ("Non-negotiable controls", [
            "EU-tagged raw payloads, replay spools, and dead-letter bodies must remain in approved EU storage and processing locations. Encryption in transit or at rest does not permit a residency exception.",
            "Raw payload retention is 30 days. Idempotency keys and non-payload audit metadata are retained for 400 days. Deletion requests must remove payloads while retaining the minimum non-payload proof required for compliance.",
            "Spools use envelope encryption with region-local keys. Break-glass access requires two-person approval, a ticket binding, and a complete audit event. Service accounts are least-privilege and cohort-scoped.",
        ]),
        ("Control inventory", table(("control", "class", "scope", "status", "owner", "evidence set"), rows)),
        ("Release consequence", [
            "Residency, retention, encryption, and access checks are blocking release criteria. The generic fail-anywhere disaster-recovery statement is not authoritative for EU payloads.",
        ]),
    ])


def s12() -> str:
    rows = []
    for percent in range(0, 101, 5):
        for region, base in (("us-east", 54), ("us-west", 63), ("eu-central", 58)):
            cpu = base + round(percent * (0.31 if region == "us-west" else 0.24), 1)
            spool = 4.5 + percent * (0.075 if region == "us-west" else 0.055)
            rows.append((region, f"{percent}%", f"{cpu:.1f}%", f"{spool:.1f}h", "expand-before-advance" if region == "us-west" and percent > 60 else "within-plan"))
    return document("Capacity, spool, and migration cost model", [
        ("Capacity conclusion", [
            "us-east and eu-central can sustain the planned dual-write path through 75% under forecast load. us-west crosses the 80% CPU safety ceiling above 60% unless two StreamCore shards are added first.",
            "Current encrypted spool capacity is six hours in us-west and eight hours elsewhere. The E-31 continuity target is twelve hours at projected peak in every region; storage and replay throughput must be expanded before promotion beyond 25%.",
            "The two-shard us-west expansion and twelve-hour spools fit the approved quarterly budget. Permanent full dual-write does not; dual-write is a bounded migration control, not the steady-state design.",
        ]),
        ("Forecast", table(("region", "candidate traffic", "projected CPU", "spool hours", "disposition"), rows)),
        ("Economic gate", [
            "Cost is subordinate to integrity and residency hard gates, but the plan must name when migration-only capacity can be retired and what evidence authorizes that effect.",
        ]),
    ])


def s13() -> str:
    rows = []
    durations = (2.1, 3.7, 4.4, 6.8, 11.1, 1.9, 8.3, 3.2, 5.6, 10.4)
    for index in range(120):
        duration = durations[index % len(durations)]
        excluded = "yes" if duration > 4 and index % 2 == 0 else "no"
        rows.append((f"V{index:03d}", ("control-plane", "storage", "network")[index % 3], f"{duration:.1f}h", excluded, "met" if duration <= 4 else "missed-or-excluded", f"ticket-{7000 + index}"))
    return document("Vendor service objective and support history", [
        ("Contract", [
            "The managed StreamCore support target is restoration within four hours for covered severity-one events. Regional dependency failures, customer networking, and force-majeure events can be excluded from the service credit calculation.",
            "The target determines escalation, communication, and credits. It is not a technical continuity guarantee and does not replace region-local buffering or tested recovery.",
        ]),
        ("Observed history", table(("incident", "class", "duration", "contract exclusion", "SLA disposition", "ticket"), rows)),
        ("Planning implication", [
            "The longest recent loss of control-plane service was 11.1 hours. Recovery exercises and spool sizing must cover at least twelve hours, and operations must be able to hold rollout without vendor control-plane access.",
        ]),
    ])


def s14() -> str:
    rows = []
    blockers = (
        "event-key dedup not proven beyond 31h",
        "EU secondary routing not independently tested",
        "us-west shards not installed",
        "twelve-hour spool replay not load-tested",
        "schema-v3 materializer bundle lacks current check",
        "per-tenant latency gate absent from release automation",
    )
    for index in range(144):
        blocker = blockers[index % len(blockers)]
        rows.append((f"A{index:03d}", blocker, ("open", "open", "evidence-requested")[index % 3], f"candidate-r{4 + index // 48}", f"owner-{index % 6}", "blocks-promotion"))
    return document("Independent migration readiness review", [
        ("Current disposition", [
            "The migration is not ready for production promotion. Shadowing may continue, but no tenant cohort may advance beyond 5% until the six blocking evidence groups below are current for the exact candidate.",
            "The review rejects three attractive shortcuts: a 24-hour dedup cache, global failover for EU payloads, and reliance on the four-hour vendor target. It also rejects fleet-average latency as the only performance gate.",
            "Readiness requires a current candidate-bound check after the last routing, schema, deduplication, materializer, capacity, or policy mutation. Submission of a plan is not itself release authorization.",
        ]),
        ("Open evidence", table(("item", "blocking evidence", "status", "candidate binding", "owner", "effect"), rows)),
        ("Expected decision", [
            "A credible ninety-day plan should sequence prerequisites before traffic, preserve a safe pre-v3 rollback envelope, define the post-v3 forward-fix boundary, assign owners, and state falsifiers that would stop or reverse the chosen route.",
        ]),
    ])


SOURCES = {
    "S01_TOPOLOGY.md": s01,
    "S02_SERVICE_OBJECTIVES.md": s02,
    "S03_DELIVERY_SEMANTICS.md": s03,
    "S04_SCHEMA_COMPATIBILITY.md": s04,
    "S05_ROLLOUT_POLICY.md": s05,
    "S06_INCIDENT_E17.md": s06,
    "S07_INCIDENT_E23.md": s07,
    "S08_INCIDENT_E31.md": s08,
    "S09_TAIL_TELEMETRY.md": s09,
    "S10_RECONCILIATION_AUDIT.md": s10,
    "S11_COMPLIANCE_CONTROLS.md": s11,
    "S12_CAPACITY_COST.md": s12,
    "S13_VENDOR_HISTORY.md": s13,
    "S14_READINESS_REVIEW.md": s14,
}


def main() -> int:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    expected = set(SOURCES)
    unexpected = {path.name for path in DESTINATION.glob("*.md")} - expected
    if unexpected:
        raise RuntimeError(f"unexpected transfer source files: {sorted(unexpected)}")
    for name, factory in SOURCES.items():
        (DESTINATION / name).write_text(factory(), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
