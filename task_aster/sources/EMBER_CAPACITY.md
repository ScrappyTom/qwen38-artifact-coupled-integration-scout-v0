# Service capacity, dependency headroom, and traffic ramps

## Frozen findings

The API tier is rated for 31,000 transactions per second and the ledger tier for 27,000, but both share a dependency capped at 24,000 TPS. The tier ratings cannot be summed.
The latest inspected run sustained 21,600 TPS after fraud and logging overhead. A higher ramp requires a current candidate-bound load test.
Traffic may increase in 10, 25, 50, and 100 percent stages only after two ten-minute windows meet latency, error, queue, and ledger gates.

## Governing relationships

DUSK drain competes with live traffic for EMBER capacity. JUNIPER rail availability and LATTICE telemetry determine whether a ramp observation is usable.
A service limit, dependency allocation, logging policy, or candidate change makes prior load evidence stale.

## Operational evidence

| record | object/region | version | measure | unit | status |
|---|---|---|---:|---|---|
| CAP-000 | api | v3 | 24.0 | thousand-tps | superseded |
| CAP-001 | ledger | v3 | 25.1 | thousand-tps | current |
| CAP-002 | queue | v3 | 26.2 | thousand-tps | current |
| CAP-003 | fraud | v3 | 24.4 | thousand-tps | current |
| CAP-004 | api | v3 | 25.5 | thousand-tps | current |
| CAP-005 | ledger | v3 | 26.6 | thousand-tps | current |
| CAP-006 | queue | v3 | 24.8 | thousand-tps | current |
| CAP-007 | fraud | v3 | 25.9 | thousand-tps | current |
| CAP-008 | api | v3 | 24.1 | thousand-tps | current |
| CAP-009 | ledger | v3 | 25.2 | thousand-tps | current |
| CAP-010 | queue | v3 | 26.3 | thousand-tps | current |
| CAP-011 | fraud | v3 | 24.5 | thousand-tps | current |
| CAP-012 | api | v3 | 25.6 | thousand-tps | current |
| CAP-013 | ledger | v3 | 26.7 | thousand-tps | current |
| CAP-014 | queue | v4 | 24.9 | thousand-tps | current |
| CAP-015 | fraud | v4 | 26.0 | thousand-tps | current |
| CAP-016 | api | v4 | 24.2 | thousand-tps | current |
| CAP-017 | ledger | v4 | 25.3 | thousand-tps | superseded |
| CAP-018 | queue | v4 | 26.4 | thousand-tps | current |
| CAP-019 | fraud | v4 | 24.6 | thousand-tps | current |
| CAP-020 | api | v4 | 25.7 | thousand-tps | current |
| CAP-021 | ledger | v4 | 26.8 | thousand-tps | current |
| CAP-022 | queue | v4 | 25.0 | thousand-tps | current |
| CAP-023 | fraud | v4 | 26.1 | thousand-tps | current |
| CAP-024 | api | v4 | 24.3 | thousand-tps | current |
| CAP-025 | ledger | v4 | 25.4 | thousand-tps | current |
| CAP-026 | queue | v4 | 26.5 | thousand-tps | current |
| CAP-027 | fraud | v4 | 24.7 | thousand-tps | current |
| CAP-028 | api | v5 | 25.8 | thousand-tps | current |
| CAP-029 | ledger | v5 | 24.0 | thousand-tps | current |
| CAP-030 | queue | v5 | 25.1 | thousand-tps | current |
| CAP-031 | fraud | v5 | 26.2 | thousand-tps | current |
| CAP-032 | api | v5 | 24.4 | thousand-tps | current |
| CAP-033 | ledger | v5 | 25.5 | thousand-tps | current |
| CAP-034 | queue | v5 | 26.6 | thousand-tps | superseded |
| CAP-035 | fraud | v5 | 24.8 | thousand-tps | current |
| CAP-036 | api | v5 | 25.9 | thousand-tps | current |
| CAP-037 | ledger | v5 | 24.1 | thousand-tps | current |
| CAP-038 | queue | v5 | 25.2 | thousand-tps | current |
| CAP-039 | fraud | v5 | 26.3 | thousand-tps | current |
| CAP-040 | api | v5 | 24.5 | thousand-tps | current |
| CAP-041 | ledger | v5 | 25.6 | thousand-tps | current |

## Decision constraints

Preserve shared capacity, observed sustainable rate, stage sequence, windows, and stale conditions.
Do not convert nominal component ratings into usable system capacity.
