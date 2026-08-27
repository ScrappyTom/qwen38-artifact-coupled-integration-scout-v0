# Monitoring coverage, alerts, and latency

## Frozen findings

Current critical-signal coverage is 94 percent; six percent remains unobserved. Coverage is not confidence and does not prove healthy uninstrumented assets.
The clean-utility warning threshold is 81 degrees Celsius and the production stop is 79 degrees. Warning and stop thresholds must remain distinct.
Alarm delivery is 640 milliseconds at p95 and 1,050 milliseconds at p99. Both are observations, not response deadlines.

## Governing relationships

CURRENT, STERILE, CHILL, and GUARD rely on SIGNAL observations, but each domain retains its own gate and authority.
COMMUNE may report operational state only where SIGNAL coverage and source currency are adequate.

## Operational evidence

| record | asset/zone | version | measure | unit | status |
|---|---|---|---:|---|---|
| OBS-000 | temperature | v3 | 94.0 | percent-coverage | superseded |
| OBS-001 | pressure | v3 | 95.7 | percent-coverage | current |
| OBS-002 | viable-air | v3 | 94.5 | percent-coverage | current |
| OBS-003 | power | v3 | 96.2 | percent-coverage | current |
| OBS-004 | temperature | v3 | 95.0 | percent-coverage | current |
| OBS-005 | pressure | v3 | 96.7 | percent-coverage | current |
| OBS-006 | viable-air | v3 | 95.5 | percent-coverage | current |
| OBS-007 | power | v3 | 94.3 | percent-coverage | current |
| OBS-008 | temperature | v3 | 96.0 | percent-coverage | current |
| OBS-009 | pressure | v3 | 94.8 | percent-coverage | current |
| OBS-010 | viable-air | v3 | 96.5 | percent-coverage | current |
| OBS-011 | power | v3 | 95.3 | percent-coverage | current |
| OBS-012 | temperature | v4 | 94.1 | percent-coverage | current |
| OBS-013 | pressure | v4 | 95.8 | percent-coverage | current |
| OBS-014 | viable-air | v4 | 94.6 | percent-coverage | current |
| OBS-015 | power | v4 | 96.3 | percent-coverage | current |
| OBS-016 | temperature | v4 | 95.1 | percent-coverage | current |
| OBS-017 | pressure | v4 | 96.8 | percent-coverage | superseded |
| OBS-018 | viable-air | v4 | 95.6 | percent-coverage | current |
| OBS-019 | power | v4 | 94.4 | percent-coverage | current |
| OBS-020 | temperature | v4 | 96.1 | percent-coverage | current |
| OBS-021 | pressure | v4 | 94.9 | percent-coverage | current |
| OBS-022 | viable-air | v4 | 96.6 | percent-coverage | current |
| OBS-023 | power | v4 | 95.4 | percent-coverage | current |
| OBS-024 | temperature | v5 | 94.2 | percent-coverage | current |
| OBS-025 | pressure | v5 | 95.9 | percent-coverage | current |
| OBS-026 | viable-air | v5 | 94.7 | percent-coverage | current |
| OBS-027 | power | v5 | 96.4 | percent-coverage | current |
| OBS-028 | temperature | v5 | 95.2 | percent-coverage | current |
| OBS-029 | pressure | v5 | 94.0 | percent-coverage | current |
| OBS-030 | viable-air | v5 | 95.7 | percent-coverage | current |
| OBS-031 | power | v5 | 94.5 | percent-coverage | current |
| OBS-032 | temperature | v5 | 96.2 | percent-coverage | current |
| OBS-033 | pressure | v5 | 95.0 | percent-coverage | current |
| OBS-034 | viable-air | v5 | 96.7 | percent-coverage | superseded |
| OBS-035 | power | v5 | 95.5 | percent-coverage | current |
| OBS-036 | temperature | v6 | 94.3 | percent-coverage | current |
| OBS-037 | pressure | v6 | 96.0 | percent-coverage | current |
| OBS-038 | viable-air | v6 | 94.8 | percent-coverage | current |
| OBS-039 | power | v6 | 96.5 | percent-coverage | current |
| OBS-040 | temperature | v6 | 95.3 | percent-coverage | current |
| OBS-041 | pressure | v6 | 94.1 | percent-coverage | current |

## Decision constraints

Preserve coverage uncertainty, threshold purpose, percentiles, units, and currentness.
Define alternate observation routes and evidence for retiring manual watches.
