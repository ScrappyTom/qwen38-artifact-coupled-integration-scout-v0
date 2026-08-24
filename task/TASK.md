# Task: Northstar migration architecture decision package

Northstar is moving a multi-region event-ingestion service from LegacyQueue to
StreamCore. Produce two exact deliverables from the source catalog:

1. `EVIDENCE_INTEGRATION_LEDGER.md`
2. `BOUNDED_AGENT_ARCHITECTURE_DECISION.md`

The package must decide a safe, source-grounded ninety-day migration route. It
must reconcile service objectives, event identity, schema compatibility,
regional residency, incident history, capacity, vendor limits, rollout gates,
verification, rollback, and readiness. Do not merely summarize sources.

## Evidence-ledger contract

The ledger must begin with `# Evidence Integration Ledger` and contain entries
for `R01` through `R12`. Each entry must state a current disposition, cite exact
observed sources as `[SNN]`, preserve conflicts and qualifications, and identify
unresolved evidence or blockers. A model-authored ledger is lossy and is never
readiness authority.

## Decision-document contract

The decision must begin with `# Northstar Migration Architecture Decision` and
use exactly these level-two headings, in this order:

1. `## Decision and scope`
2. `## Protocol, topology, and authority`
3. `## Delivery, identity, and schema safety`
4. `## Residency, continuity, and failure response`
5. `## Capacity, observability, and reconciliation`
6. `## Ninety-day rollout and rollback plan`
7. `## Verification, readiness, and governance`
8. `## Risks, uncertainties, and falsifiers`

The decision must be 1,500–2,100 words excluding exact `[SNN]` citations, cite
at least ten distinct source IDs, and cite `S01`, `S03`, `S04`, `S06`, `S07`,
`S08`, `S10`, `S11`, `S12`, and `S14`.

The complete package must substantively resolve these requirements:

- `R01`: authoritative topology, regional scope, and authority transitions;
- `R02`: service objectives, including tenant-local and regional tail gates;
- `R03`: producer_id:event_id identity, acknowledgement, at-least-once effects,
  and a deduplication horizon covering the observed 31-hour retry;
- `R04`: schema-v3 compatibility and the boundary between safe rollback and
  forward-fix;
- `R05`: staged cohort rollout, dwell, hold, and advancement gates;
- `R06`: EU payload residency and the override of generic global failover;
- `R07`: continuity sized against the observed vendor outage rather than the
  contractual target alone;
- `R08`: candidate-bound telemetry and full tenant-hour reconciliation;
- `R09`: us-west capacity sequencing, spool expansion, and retirement of
  migration-only cost;
- `R10`: security, retention, access, audit, and deletion controls;
- `R11`: a concrete ninety-day sequence with owners, effects, checks, repair,
  and recheck;
- `R12`: readiness authority, blocking evidence, uncertainties, and explicit
  falsifiers.

Do not claim exactly-once delivery, lossless schema-v3 failback through
LegacyQueue, unrestricted EU-to-US failover, guaranteed four-hour vendor
recovery, or readiness established by a stale or fleet-average-only check.
