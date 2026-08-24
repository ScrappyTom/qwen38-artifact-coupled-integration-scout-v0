# Northstar topology and migration target

## Authoritative scope

Northstar accepts customer events through regional edge gateways and currently commits them to LegacyQueue. The approved migration target is StreamCore, but the cutover must preserve the externally visible event contract rather than merely keep processes running.
The three production regions are us-east, us-west, and eu-central. EU-tagged payloads must remain inside eu-central. A regional outage may not silently convert an EU event into a US event.
The migration unit is a tenant cohort. A global all-at-once switch is prohibited. Each cohort can be shadowed, dual-written, promoted, held, or rolled back subject to the schema and residency rules in the other sources.

## Data path

The edge gateway validates the envelope and assigns the authoritative producer_id:event_id idempotency key. The validator attaches tenant_policy, residency_tag, and schema_version before any durable write.
LegacyQueue is the current authority. During dual-write, StreamCore is a candidate path and the reconciler compares both paths. After cohort promotion, StreamCore becomes authoritative only after the promotion effect is recorded in the control ledger.
The materializer exposes committed events to downstream readers. An ingest acknowledgement is not evidence that the materializer has made the event visible.

## Topology inventory

| record | region | component | replicas | mode | declared revision |
|---|---|---|---|---|---|
| T00-0 | us-east | edge | 2 | active-active | topology-rev-7 |
| T00-1 | us-west | validator | 3 | active-active | topology-rev-7 |
| T00-2 | eu-central | legacy-queue | 4 | active-passive | topology-rev-7 |
| T01-0 | us-east | validator | 3 | active-active | topology-rev-7 |
| T01-1 | us-west | legacy-queue | 4 | active-passive | topology-rev-7 |
| T01-2 | eu-central | streamcore | 5 | active-active | topology-rev-7 |
| T02-0 | us-east | legacy-queue | 4 | active-passive | topology-rev-7 |
| T02-1 | us-west | streamcore | 5 | active-active | topology-rev-7 |
| T02-2 | eu-central | materializer | 2 | active-active | topology-rev-7 |
| T03-0 | us-east | streamcore | 5 | active-active | topology-rev-7 |
| T03-1 | us-west | materializer | 2 | active-active | topology-rev-7 |
| T03-2 | eu-central | reconciler | 3 | active-active | topology-rev-7 |
| T04-0 | us-east | materializer | 2 | active-active | topology-rev-7 |
| T04-1 | us-west | reconciler | 3 | active-active | topology-rev-7 |
| T04-2 | eu-central | edge | 4 | active-active | topology-rev-7 |
| T05-0 | us-east | reconciler | 3 | active-active | topology-rev-7 |
| T05-1 | us-west | edge | 4 | active-active | topology-rev-7 |
| T05-2 | eu-central | validator | 5 | active-active | topology-rev-7 |
| T06-0 | us-east | edge | 4 | active-active | topology-rev-7 |
| T06-1 | us-west | validator | 5 | active-active | topology-rev-7 |
| T06-2 | eu-central | legacy-queue | 2 | active-passive | topology-rev-7 |
| T07-0 | us-east | validator | 5 | active-active | topology-rev-7 |
| T07-1 | us-west | legacy-queue | 2 | active-passive | topology-rev-7 |
| T07-2 | eu-central | streamcore | 3 | active-active | topology-rev-7 |
| T08-0 | us-east | legacy-queue | 2 | active-passive | topology-rev-8 |
| T08-1 | us-west | streamcore | 3 | active-active | topology-rev-8 |
| T08-2 | eu-central | materializer | 4 | active-active | topology-rev-8 |
| T09-0 | us-east | streamcore | 3 | active-active | topology-rev-8 |
| T09-1 | us-west | materializer | 4 | active-active | topology-rev-8 |
| T09-2 | eu-central | reconciler | 5 | active-active | topology-rev-8 |
| T10-0 | us-east | materializer | 4 | active-active | topology-rev-8 |
| T10-1 | us-west | reconciler | 5 | active-active | topology-rev-8 |
| T10-2 | eu-central | edge | 2 | active-active | topology-rev-8 |
| T11-0 | us-east | reconciler | 5 | active-active | topology-rev-8 |
| T11-1 | us-west | edge | 2 | active-active | topology-rev-8 |
| T11-2 | eu-central | validator | 3 | active-active | topology-rev-8 |
| T12-0 | us-east | edge | 2 | active-active | topology-rev-8 |
| T12-1 | us-west | validator | 3 | active-active | topology-rev-8 |
| T12-2 | eu-central | legacy-queue | 4 | active-passive | topology-rev-8 |
| T13-0 | us-east | validator | 3 | active-active | topology-rev-8 |
| T13-1 | us-west | legacy-queue | 4 | active-passive | topology-rev-8 |
| T13-2 | eu-central | streamcore | 5 | active-active | topology-rev-8 |
| T14-0 | us-east | legacy-queue | 4 | active-passive | topology-rev-8 |
| T14-1 | us-west | streamcore | 5 | active-active | topology-rev-8 |
| T14-2 | eu-central | materializer | 2 | active-active | topology-rev-8 |
| T15-0 | us-east | streamcore | 5 | active-active | topology-rev-8 |
| T15-1 | us-west | materializer | 2 | active-active | topology-rev-8 |
| T15-2 | eu-central | reconciler | 3 | active-active | topology-rev-8 |
| T16-0 | us-east | materializer | 2 | active-active | topology-rev-9 |
| T16-1 | us-west | reconciler | 3 | active-active | topology-rev-9 |
| T16-2 | eu-central | edge | 4 | active-active | topology-rev-9 |
| T17-0 | us-east | reconciler | 3 | active-active | topology-rev-9 |
| T17-1 | us-west | edge | 4 | active-active | topology-rev-9 |
| T17-2 | eu-central | validator | 5 | active-active | topology-rev-9 |
| T18-0 | us-east | edge | 4 | active-active | topology-rev-9 |
| T18-1 | us-west | validator | 5 | active-active | topology-rev-9 |
| T18-2 | eu-central | legacy-queue | 2 | active-passive | topology-rev-9 |
| T19-0 | us-east | validator | 5 | active-active | topology-rev-9 |
| T19-1 | us-west | legacy-queue | 2 | active-passive | topology-rev-9 |
| T19-2 | eu-central | streamcore | 3 | active-active | topology-rev-9 |
| T20-0 | us-east | legacy-queue | 2 | active-passive | topology-rev-9 |
| T20-1 | us-west | streamcore | 3 | active-active | topology-rev-9 |
| T20-2 | eu-central | materializer | 4 | active-active | topology-rev-9 |
| T21-0 | us-east | streamcore | 3 | active-active | topology-rev-9 |
| T21-1 | us-west | materializer | 4 | active-active | topology-rev-9 |
| T21-2 | eu-central | reconciler | 5 | active-active | topology-rev-9 |
| T22-0 | us-east | materializer | 4 | active-active | topology-rev-9 |
| T22-1 | us-west | reconciler | 5 | active-active | topology-rev-9 |
| T22-2 | eu-central | edge | 2 | active-active | topology-rev-9 |
| T23-0 | us-east | reconciler | 5 | active-active | topology-rev-9 |
| T23-1 | us-west | edge | 2 | active-active | topology-rev-9 |
| T23-2 | eu-central | validator | 3 | active-active | topology-rev-9 |

## Known coupling

The validator and materializer deploy independently, but schema v3 requires both to understand tenant_policy and residency_tag. Promoting ingest without current materializer verification can create durable but unreadable events.
The reconciler is an operational control, not the data authority. Its reports are candidate-version-bound observations and become stale after routing, schema, or deduplication changes.
