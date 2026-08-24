# Schema compatibility and rollback boundaries

## Schema rules

Schema v1 is the legacy envelope. Schema v2 adds optional trace metadata and can round-trip through LegacyQueue. Schema v3 makes tenant_policy and residency_tag mandatory and is the first format used to enforce tenant-local policy at ingest.
LegacyQueue cannot preserve the two v3 fields. Sending an accepted v3 event back through the legacy path silently drops them. Therefore an ordinary failback after v3 promotion is unsafe unless an explicit lossless down-conversion or retained dual representation has been proven.
The current migration proposal contains no lossless v3-to-v1 conversion. Once a cohort accepts v3-only events, rollback means stop new promotion and forward-fix StreamCore; it does not mean route those events through LegacyQueue.

## Compatibility matrix

| producer | schema | current reader | legacy round-trip | promotion disposition |
|---|---|---|---|---|
| producer-00 | v1 | yes | lossless | allow |
| producer-00 | v2 | yes | lossless | allow |
| producer-00 | v3 | requires-new-materializer | drops-tenant_policy-and-residency_tag | block |
| producer-01 | v1 | yes | lossless | allow |
| producer-01 | v2 | yes | lossless | allow |
| producer-01 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-02 | v1 | yes | lossless | allow |
| producer-02 | v2 | yes | lossless | allow |
| producer-02 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-03 | v1 | yes | lossless | allow |
| producer-03 | v2 | yes | lossless | allow |
| producer-03 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-04 | v1 | yes | lossless | allow |
| producer-04 | v2 | yes | lossless | allow |
| producer-04 | v3 | requires-new-materializer | drops-tenant_policy-and-residency_tag | block |
| producer-05 | v1 | yes | lossless | allow |
| producer-05 | v2 | yes | lossless | allow |
| producer-05 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-06 | v1 | yes | lossless | allow |
| producer-06 | v2 | yes | lossless | allow |
| producer-06 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-07 | v1 | yes | lossless | allow |
| producer-07 | v2 | yes | lossless | allow |
| producer-07 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-08 | v1 | yes | lossless | allow |
| producer-08 | v2 | yes | lossless | allow |
| producer-08 | v3 | requires-new-materializer | drops-tenant_policy-and-residency_tag | block |
| producer-09 | v1 | yes | lossless | allow |
| producer-09 | v2 | yes | lossless | allow |
| producer-09 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-10 | v1 | yes | lossless | allow |
| producer-10 | v2 | yes | lossless | allow |
| producer-10 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-11 | v1 | yes | lossless | allow |
| producer-11 | v2 | yes | lossless | allow |
| producer-11 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-12 | v1 | yes | lossless | allow |
| producer-12 | v2 | yes | lossless | allow |
| producer-12 | v3 | requires-new-materializer | drops-tenant_policy-and-residency_tag | block |
| producer-13 | v1 | yes | lossless | allow |
| producer-13 | v2 | yes | lossless | allow |
| producer-13 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-14 | v1 | yes | lossless | allow |
| producer-14 | v2 | yes | lossless | allow |
| producer-14 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-15 | v1 | yes | lossless | allow |
| producer-15 | v2 | yes | lossless | allow |
| producer-15 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-16 | v1 | yes | lossless | allow |
| producer-16 | v2 | yes | lossless | allow |
| producer-16 | v3 | requires-new-materializer | drops-tenant_policy-and-residency_tag | block |
| producer-17 | v1 | yes | lossless | allow |
| producer-17 | v2 | yes | lossless | allow |
| producer-17 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-18 | v1 | yes | lossless | allow |
| producer-18 | v2 | yes | lossless | allow |
| producer-18 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-19 | v1 | yes | lossless | allow |
| producer-19 | v2 | yes | lossless | allow |
| producer-19 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-20 | v1 | yes | lossless | allow |
| producer-20 | v2 | yes | lossless | allow |
| producer-20 | v3 | requires-new-materializer | drops-tenant_policy-and-residency_tag | block |
| producer-21 | v1 | yes | lossless | allow |
| producer-21 | v2 | yes | lossless | allow |
| producer-21 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-22 | v1 | yes | lossless | allow |
| producer-22 | v2 | yes | lossless | allow |
| producer-22 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |
| producer-23 | v1 | yes | lossless | allow |
| producer-23 | v2 | yes | lossless | allow |
| producer-23 | v3 | yes | drops-tenant_policy-and-residency_tag | allow |

## Version gates

Before v3 promotion, the validator, StreamCore decoder, materializer, reconciler, replay tooling, and audit exporter must all pass the same candidate-bound compatibility suite.
A check run against the prior schema bundle becomes stale after any component or routing mutation. Readiness must name the exact bundle hash that was tested.
