# Telemetry coverage, alert thresholds, and observation quality

## Frozen findings

Telemetry covers 97 percent of production transactions. The missing three percent requires an uncertainty allowance and is not evidence of zero errors.
The latency alert is 900 milliseconds p95 and the traffic hold is 1,400 milliseconds p95 for two consecutive five-minute windows. Alert and hold thresholds differ.
Ordering error above 0.02 percent pauses queue replay. The latest current observation is 0.006 percent over fifteen minutes.

## Governing relationships

DUSK supplies queue ordering and GROVE supplies fraud-score distributions. EMBER load tests are usable only when LATTICE coverage and version binding are current.
IRIS governs audit-event integrity; LATTICE dashboards alone do not establish security or readiness.

## Operational evidence

| record | object/region | version | measure | unit | status |
|---|---|---|---:|---|---|
| OBS-000 | latency | v3 | 97.0 | percent-coverage | superseded |
| OBS-001 | errors | v3 | 98.1 | percent-coverage | current |
| OBS-002 | ordering | v3 | 99.2 | percent-coverage | current |
| OBS-003 | fraud-score | v3 | 97.4 | percent-coverage | current |
| OBS-004 | latency | v3 | 98.5 | percent-coverage | current |
| OBS-005 | errors | v3 | 99.6 | percent-coverage | current |
| OBS-006 | ordering | v3 | 97.8 | percent-coverage | current |
| OBS-007 | fraud-score | v3 | 98.9 | percent-coverage | current |
| OBS-008 | latency | v3 | 97.1 | percent-coverage | current |
| OBS-009 | errors | v3 | 98.2 | percent-coverage | current |
| OBS-010 | ordering | v3 | 99.3 | percent-coverage | current |
| OBS-011 | fraud-score | v3 | 97.5 | percent-coverage | current |
| OBS-012 | latency | v3 | 98.6 | percent-coverage | current |
| OBS-013 | errors | v3 | 99.7 | percent-coverage | current |
| OBS-014 | ordering | v4 | 97.9 | percent-coverage | current |
| OBS-015 | fraud-score | v4 | 99.0 | percent-coverage | current |
| OBS-016 | latency | v4 | 97.2 | percent-coverage | current |
| OBS-017 | errors | v4 | 98.3 | percent-coverage | superseded |
| OBS-018 | ordering | v4 | 99.4 | percent-coverage | current |
| OBS-019 | fraud-score | v4 | 97.6 | percent-coverage | current |
| OBS-020 | latency | v4 | 98.7 | percent-coverage | current |
| OBS-021 | errors | v4 | 99.8 | percent-coverage | current |
| OBS-022 | ordering | v4 | 98.0 | percent-coverage | current |
| OBS-023 | fraud-score | v4 | 99.1 | percent-coverage | current |
| OBS-024 | latency | v4 | 97.3 | percent-coverage | current |
| OBS-025 | errors | v4 | 98.4 | percent-coverage | current |
| OBS-026 | ordering | v4 | 99.5 | percent-coverage | current |
| OBS-027 | fraud-score | v4 | 97.7 | percent-coverage | current |
| OBS-028 | latency | v5 | 98.8 | percent-coverage | current |
| OBS-029 | errors | v5 | 97.0 | percent-coverage | current |
| OBS-030 | ordering | v5 | 98.1 | percent-coverage | current |
| OBS-031 | fraud-score | v5 | 99.2 | percent-coverage | current |
| OBS-032 | latency | v5 | 97.4 | percent-coverage | current |
| OBS-033 | errors | v5 | 98.5 | percent-coverage | current |
| OBS-034 | ordering | v5 | 99.6 | percent-coverage | superseded |
| OBS-035 | fraud-score | v5 | 97.8 | percent-coverage | current |
| OBS-036 | latency | v5 | 98.9 | percent-coverage | current |
| OBS-037 | errors | v5 | 97.1 | percent-coverage | current |
| OBS-038 | ordering | v5 | 98.2 | percent-coverage | current |
| OBS-039 | fraud-score | v5 | 99.3 | percent-coverage | current |
| OBS-040 | latency | v5 | 97.5 | percent-coverage | current |
| OBS-041 | errors | v5 | 98.6 | percent-coverage | current |

## Decision constraints

Preserve coverage uncertainty, milliseconds, consecutive windows, ordering percentages, and observation horizon.
Name missing telemetry, fallback observation, pause, resume, and falsifier evidence.
