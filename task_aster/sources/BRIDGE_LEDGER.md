# Ledger replication, consistency, and recovery-point evidence

## Frozen findings

Current cross-region ledger replication lag is 1,800 milliseconds at p95. The traffic-restoration block is 2.5 seconds sustained for three five-minute windows; 1,800 ms must not be converted to 1,800 seconds or treated as zero lag.
The recovery point objective is fifteen seconds and the recovery time objective is forty-five minutes. Those are different controls and neither is the observed replication lag.
A schema or writer-route change makes prior consistency and replay checks stale for the changed candidate. Current verification must bind the candidate, schema, writer, and settlement-log versions.

## Governing relationships

CIRRUS retry safety depends on BRIDGE ledger uniqueness and DUSK queue position. FORGE settlement release consumes a BRIDGE-consistent cutoff.
NOVA rollback is permitted only while the old schema remains readable and a current BRIDGE consistency check passes for the rollback candidate.

## Operational evidence

| record | object/region | version | measure | unit | status |
|---|---|---|---:|---|---|
| LEDG-000 | east-writer | v3 | 1800.0 | milliseconds-p95 | superseded |
| LEDG-001 | west-replica | v3 | 1801.1 | milliseconds-p95 | current |
| LEDG-002 | settlement-log | v3 | 1802.2 | milliseconds-p95 | current |
| LEDG-003 | balance-view | v3 | 1800.4 | milliseconds-p95 | current |
| LEDG-004 | east-writer | v3 | 1801.5 | milliseconds-p95 | current |
| LEDG-005 | west-replica | v3 | 1802.6 | milliseconds-p95 | current |
| LEDG-006 | settlement-log | v3 | 1800.8 | milliseconds-p95 | current |
| LEDG-007 | balance-view | v3 | 1801.9 | milliseconds-p95 | current |
| LEDG-008 | east-writer | v3 | 1800.1 | milliseconds-p95 | current |
| LEDG-009 | west-replica | v3 | 1801.2 | milliseconds-p95 | current |
| LEDG-010 | settlement-log | v3 | 1802.3 | milliseconds-p95 | current |
| LEDG-011 | balance-view | v3 | 1800.5 | milliseconds-p95 | current |
| LEDG-012 | east-writer | v3 | 1801.6 | milliseconds-p95 | current |
| LEDG-013 | west-replica | v3 | 1802.7 | milliseconds-p95 | current |
| LEDG-014 | settlement-log | v4 | 1800.9 | milliseconds-p95 | current |
| LEDG-015 | balance-view | v4 | 1802.0 | milliseconds-p95 | current |
| LEDG-016 | east-writer | v4 | 1800.2 | milliseconds-p95 | current |
| LEDG-017 | west-replica | v4 | 1801.3 | milliseconds-p95 | superseded |
| LEDG-018 | settlement-log | v4 | 1802.4 | milliseconds-p95 | current |
| LEDG-019 | balance-view | v4 | 1800.6 | milliseconds-p95 | current |
| LEDG-020 | east-writer | v4 | 1801.7 | milliseconds-p95 | current |
| LEDG-021 | west-replica | v4 | 1802.8 | milliseconds-p95 | current |
| LEDG-022 | settlement-log | v4 | 1801.0 | milliseconds-p95 | current |
| LEDG-023 | balance-view | v4 | 1802.1 | milliseconds-p95 | current |
| LEDG-024 | east-writer | v4 | 1800.3 | milliseconds-p95 | current |
| LEDG-025 | west-replica | v4 | 1801.4 | milliseconds-p95 | current |
| LEDG-026 | settlement-log | v4 | 1802.5 | milliseconds-p95 | current |
| LEDG-027 | balance-view | v4 | 1800.7 | milliseconds-p95 | current |
| LEDG-028 | east-writer | v5 | 1801.8 | milliseconds-p95 | current |
| LEDG-029 | west-replica | v5 | 1800.0 | milliseconds-p95 | current |
| LEDG-030 | settlement-log | v5 | 1801.1 | milliseconds-p95 | current |
| LEDG-031 | balance-view | v5 | 1802.2 | milliseconds-p95 | current |
| LEDG-032 | east-writer | v5 | 1800.4 | milliseconds-p95 | current |
| LEDG-033 | west-replica | v5 | 1801.5 | milliseconds-p95 | current |
| LEDG-034 | settlement-log | v5 | 1802.6 | milliseconds-p95 | superseded |
| LEDG-035 | balance-view | v5 | 1800.8 | milliseconds-p95 | current |
| LEDG-036 | east-writer | v5 | 1801.9 | milliseconds-p95 | current |
| LEDG-037 | west-replica | v5 | 1800.1 | milliseconds-p95 | current |
| LEDG-038 | settlement-log | v5 | 1801.2 | milliseconds-p95 | current |
| LEDG-039 | balance-view | v5 | 1802.3 | milliseconds-p95 | current |
| LEDG-040 | east-writer | v5 | 1800.5 | milliseconds-p95 | current |
| LEDG-041 | west-replica | v5 | 1801.6 | milliseconds-p95 | current |

## Decision constraints

Preserve milliseconds, seconds, the three-window rule, RPO, RTO, and candidate currency.
Distinguish replicated bytes, consistent balances, and authority to restore traffic.
