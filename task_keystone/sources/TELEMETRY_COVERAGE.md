# Monitoring coverage, alarms, and delivery latency

## Frozen findings

Current critical-signal coverage is 93 percent; seven percent remains unobserved. Coverage is not confidence and does not prove uninstrumented assets healthy.
Route-state delivery is 720 milliseconds at p95 and 1,180 milliseconds at p99. These are observations, not response deadlines.
The power warning threshold is 24.2 kilovolts and the operating stop is 23.8 kilovolts. Warning and stop semantics must remain distinct.

## Governing relationships

TRACK, SIGNAL, POWER, ROLLING, and WEATHER rely on TELEMETRY observations while retaining their own gates and authorities.
COMMS may report state only where coverage and source currency are adequate.

## Operational evidence

| record | asset/zone | version | measure | unit | status |
|---|---|---|---:|---|---|
| TEL-000 | track-circuits | v4 | 93.0 | percent-coverage | superseded |
| TEL-001 | voltage | v4 | 94.9 | percent-coverage | current |
| TEL-002 | wind | v4 | 93.7 | percent-coverage | current |
| TEL-003 | brakes | v4 | 95.6 | percent-coverage | current |
| TEL-004 | track-circuits | v4 | 94.4 | percent-coverage | current |
| TEL-005 | voltage | v4 | 93.2 | percent-coverage | current |
| TEL-006 | wind | v4 | 95.1 | percent-coverage | current |
| TEL-007 | brakes | v4 | 93.9 | percent-coverage | current |
| TEL-008 | track-circuits | v4 | 95.8 | percent-coverage | current |
| TEL-009 | voltage | v4 | 94.6 | percent-coverage | current |
| TEL-010 | wind | v4 | 93.4 | percent-coverage | current |
| TEL-011 | brakes | v5 | 95.3 | percent-coverage | current |
| TEL-012 | track-circuits | v5 | 94.1 | percent-coverage | current |
| TEL-013 | voltage | v5 | 96.0 | percent-coverage | current |
| TEL-014 | wind | v5 | 94.8 | percent-coverage | current |
| TEL-015 | brakes | v5 | 93.6 | percent-coverage | current |
| TEL-016 | track-circuits | v5 | 95.5 | percent-coverage | current |
| TEL-017 | voltage | v5 | 94.3 | percent-coverage | current |
| TEL-018 | wind | v5 | 93.1 | percent-coverage | current |
| TEL-019 | brakes | v5 | 95.0 | percent-coverage | superseded |
| TEL-020 | track-circuits | v5 | 93.8 | percent-coverage | current |
| TEL-021 | voltage | v5 | 95.7 | percent-coverage | current |
| TEL-022 | wind | v6 | 94.5 | percent-coverage | current |
| TEL-023 | brakes | v6 | 93.3 | percent-coverage | current |
| TEL-024 | track-circuits | v6 | 95.2 | percent-coverage | current |
| TEL-025 | voltage | v6 | 94.0 | percent-coverage | current |
| TEL-026 | wind | v6 | 95.9 | percent-coverage | current |
| TEL-027 | brakes | v6 | 94.7 | percent-coverage | current |
| TEL-028 | track-circuits | v6 | 93.5 | percent-coverage | current |
| TEL-029 | voltage | v6 | 95.4 | percent-coverage | current |
| TEL-030 | wind | v6 | 94.2 | percent-coverage | current |
| TEL-031 | brakes | v6 | 93.0 | percent-coverage | current |
| TEL-032 | track-circuits | v6 | 94.9 | percent-coverage | current |
| TEL-033 | voltage | v7 | 93.7 | percent-coverage | current |
| TEL-034 | wind | v7 | 95.6 | percent-coverage | current |
| TEL-035 | brakes | v7 | 94.4 | percent-coverage | current |
| TEL-036 | track-circuits | v7 | 93.2 | percent-coverage | current |
| TEL-037 | voltage | v7 | 95.1 | percent-coverage | current |
| TEL-038 | wind | v7 | 93.9 | percent-coverage | superseded |
| TEL-039 | brakes | v7 | 95.8 | percent-coverage | current |
| TEL-040 | track-circuits | v7 | 94.6 | percent-coverage | current |
| TEL-041 | voltage | v7 | 93.4 | percent-coverage | current |
| TEL-042 | wind | v7 | 95.3 | percent-coverage | current |
| TEL-043 | brakes | v7 | 94.1 | percent-coverage | current |
| TEL-044 | track-circuits | v8 | 96.0 | percent-coverage | current |
| TEL-045 | voltage | v8 | 94.8 | percent-coverage | current |
| TEL-046 | wind | v8 | 93.6 | percent-coverage | current |
| TEL-047 | brakes | v8 | 95.5 | percent-coverage | current |
| TEL-048 | track-circuits | v8 | 94.3 | percent-coverage | current |
| TEL-049 | voltage | v8 | 93.1 | percent-coverage | current |
| TEL-050 | wind | v8 | 95.0 | percent-coverage | current |
| TEL-051 | brakes | v8 | 93.8 | percent-coverage | current |
| TEL-052 | track-circuits | v8 | 95.7 | percent-coverage | current |
| TEL-053 | voltage | v8 | 94.5 | percent-coverage | current |
| TEL-054 | wind | v8 | 93.3 | percent-coverage | current |
| TEL-055 | brakes | v9 | 95.2 | percent-coverage | current |
| TEL-056 | track-circuits | v9 | 94.0 | percent-coverage | current |
| TEL-057 | voltage | v9 | 95.9 | percent-coverage | superseded |
| TEL-058 | wind | v9 | 94.7 | percent-coverage | current |
| TEL-059 | brakes | v9 | 93.5 | percent-coverage | current |
| TEL-060 | track-circuits | v9 | 95.4 | percent-coverage | current |
| TEL-061 | voltage | v9 | 94.2 | percent-coverage | current |
| TEL-062 | wind | v9 | 93.0 | percent-coverage | current |
| TEL-063 | brakes | v9 | 94.9 | percent-coverage | current |

## Decision constraints

Preserve coverage uncertainty, percentile latency, voltage, purpose, and currentness.
Define alternate observation routes and evidence for retiring manual watches.
