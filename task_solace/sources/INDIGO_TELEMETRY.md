# Telemetry coverage, alerts, and observation quality

## Frozen findings

Current critical-signal coverage is 96 percent; four percent remains unobserved. Coverage is not confidence and does not prove healthy uninstrumented zones.
The warning threshold for pressure is 38 psi and the isolation trigger is 30 psi. Warning and action thresholds must remain distinct.
Telemetry delay is 700 milliseconds at p95 and 1,200 milliseconds at p99. Both are observations, not control deadlines.

## Governing relationships

BASTION, DELTA, ECHO, and FALCON rely on INDIGO observations, but each domain retains its own decision gate.
LUMEN communications may report measured service only where INDIGO coverage and source currency are adequate.

## Operational evidence

| record | asset/zone | version | measure | unit | status |
|---|---|---|---:|---|---|
| OBS-000 | pressure | v2 | 96.0 | percent-coverage | superseded |
| OBS-001 | turbidity | v2 | 97.3 | percent-coverage | current |
| OBS-002 | power | v2 | 98.6 | percent-coverage | current |
| OBS-003 | chlorine | v2 | 96.8 | percent-coverage | current |
| OBS-004 | pressure | v2 | 98.1 | percent-coverage | current |
| OBS-005 | turbidity | v2 | 96.3 | percent-coverage | current |
| OBS-006 | power | v2 | 97.6 | percent-coverage | current |
| OBS-007 | chlorine | v2 | 98.9 | percent-coverage | current |
| OBS-008 | pressure | v2 | 97.1 | percent-coverage | current |
| OBS-009 | turbidity | v2 | 98.4 | percent-coverage | current |
| OBS-010 | power | v2 | 96.6 | percent-coverage | current |
| OBS-011 | chlorine | v2 | 97.9 | percent-coverage | current |
| OBS-012 | pressure | v2 | 96.1 | percent-coverage | current |
| OBS-013 | turbidity | v2 | 97.4 | percent-coverage | current |
| OBS-014 | power | v3 | 98.7 | percent-coverage | current |
| OBS-015 | chlorine | v3 | 96.9 | percent-coverage | current |
| OBS-016 | pressure | v3 | 98.2 | percent-coverage | current |
| OBS-017 | turbidity | v3 | 96.4 | percent-coverage | current |
| OBS-018 | power | v3 | 97.7 | percent-coverage | current |
| OBS-019 | chlorine | v3 | 99.0 | percent-coverage | superseded |
| OBS-020 | pressure | v3 | 97.2 | percent-coverage | current |
| OBS-021 | turbidity | v3 | 98.5 | percent-coverage | current |
| OBS-022 | power | v3 | 96.7 | percent-coverage | current |
| OBS-023 | chlorine | v3 | 98.0 | percent-coverage | current |
| OBS-024 | pressure | v3 | 96.2 | percent-coverage | current |
| OBS-025 | turbidity | v3 | 97.5 | percent-coverage | current |
| OBS-026 | power | v3 | 98.8 | percent-coverage | current |
| OBS-027 | chlorine | v3 | 97.0 | percent-coverage | current |
| OBS-028 | pressure | v4 | 98.3 | percent-coverage | current |
| OBS-029 | turbidity | v4 | 96.5 | percent-coverage | current |
| OBS-030 | power | v4 | 97.8 | percent-coverage | current |
| OBS-031 | chlorine | v4 | 96.0 | percent-coverage | current |
| OBS-032 | pressure | v4 | 97.3 | percent-coverage | current |
| OBS-033 | turbidity | v4 | 98.6 | percent-coverage | current |
| OBS-034 | power | v4 | 96.8 | percent-coverage | current |
| OBS-035 | chlorine | v4 | 98.1 | percent-coverage | current |
| OBS-036 | pressure | v4 | 96.3 | percent-coverage | current |
| OBS-037 | turbidity | v4 | 97.6 | percent-coverage | current |
| OBS-038 | power | v4 | 98.9 | percent-coverage | superseded |
| OBS-039 | chlorine | v4 | 97.1 | percent-coverage | current |
| OBS-040 | pressure | v4 | 98.4 | percent-coverage | current |
| OBS-041 | turbidity | v4 | 96.6 | percent-coverage | current |

## Decision constraints

Preserve coverage, uncertainty, threshold purpose, percentiles, and units.
Define alternate observation routes and evidence for retiring manual watches.
