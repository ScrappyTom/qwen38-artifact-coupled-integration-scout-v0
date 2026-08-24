# Rollout, hold, and rollback policy

## Default sequence

The standard cohort sequence is shadow, 5%, 25%, 50%, 75%, and 100%. Advancement is never time-only: the minimum dwell and every service, reconciliation, residency, security, and capacity gate must pass for the exact candidate.
Any event loss, unauthorized cross-region payload movement, schema corruption, or current check failure is a hard hold. Duplicate or latency breaches are also holds when they exceed the frozen objectives.
The generic disaster-recovery appendix says traffic may fail to any healthy region. That generic rule is overridden for EU-tagged payloads by the compliance source: EU payloads may fail only to an approved EU-resident target, otherwise ingest must fail closed while metadata-only status remains available.

## Rollback semantics

Before v3-only acceptance, rollback may restore LegacyQueue authority after reconciliation confirms no unrepresented events. After v3-only acceptance, the safe response is halt advancement, retain StreamCore authority for accepted v3 events, and forward-fix or replay from the EU/region-local spool.
Every mutation to routing, schema, deduplication, or materializer code invalidates the prior check. A new check and at least one clean dwell window are required before advancement.

## Stage matrix

| region | stage | traffic | minimum dwell | advance evidence | failure action |
|---|---|---|---|---|---|
| us-east | shadow | 0% | 2h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| us-east | canary | 5% | 2h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| us-east | cohort-1 | 25% | 6h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| us-east | cohort-2 | 50% | 6h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| us-east | cohort-3 | 75% | 12h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| us-east | complete | 100% | 12h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| us-west | shadow | 0% | 2h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| us-west | canary | 5% | 2h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| us-west | cohort-1 | 25% | 6h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| us-west | cohort-2 | 50% | 6h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| us-west | cohort-3 | 75% | 12h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| us-west | complete | 100% | 12h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| eu-central | shadow | 0% | 2h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| eu-central | canary | 5% | 2h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| eu-central | cohort-1 | 25% | 6h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| eu-central | cohort-2 | 50% | 6h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| eu-central | cohort-3 | 75% | 12h | candidate-bound check + reconciliation | automatic hold on any hard gate |
| eu-central | complete | 100% | 12h | candidate-bound check + reconciliation | automatic hold on any hard gate |

## Authority

The release commander can hold or roll back within the safe envelope. Compliance owns residency exceptions. The data-integrity lead owns reconciliation acceptance. No single actor may waive a hard gate and declare readiness.
