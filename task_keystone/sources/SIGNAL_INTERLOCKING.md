# Interlocking, route proving, and crossing logic

## Frozen findings

The current interlocking suite passed 99.2 percent of test vectors. The service gate requires 100 percent of safety-critical vectors and two consecutive route-proving trains; 99.2 percent is not a probability of safety.
Crossing 12 warning time is 27 seconds against a minimum of 25 seconds. The observed 27 seconds does not replace the two-train route-proving requirement.
A logic build, route table, crossing controller, axle-counter reset, or dispatcher-link change makes prior signal evidence stale.

## Governing relationships

TRACK supplies route topology, CYBER supplies signed build custody, and TELEMETRY supplies current event delivery; none authorizes service alone.
MANDATE assigns movement authority and LINEAGE binds the exact interlocking build to the candidate.

## Operational evidence

| record | asset/zone | version | measure | unit | status |
|---|---|---|---:|---|---|
| SIG-000 | interlocking-7 | v4 | 99.0 | percent-tests | superseded |
| SIG-001 | crossing-12 | v4 | 100.9 | percent-tests | current |
| SIG-002 | block-4 | v4 | 99.7 | percent-tests | current |
| SIG-003 | dispatcher-link | v4 | 101.6 | percent-tests | current |
| SIG-004 | interlocking-7 | v4 | 100.4 | percent-tests | current |
| SIG-005 | crossing-12 | v4 | 99.2 | percent-tests | current |
| SIG-006 | block-4 | v4 | 101.1 | percent-tests | current |
| SIG-007 | dispatcher-link | v4 | 99.9 | percent-tests | current |
| SIG-008 | interlocking-7 | v4 | 101.8 | percent-tests | current |
| SIG-009 | crossing-12 | v4 | 100.6 | percent-tests | current |
| SIG-010 | block-4 | v4 | 99.4 | percent-tests | current |
| SIG-011 | dispatcher-link | v5 | 101.3 | percent-tests | current |
| SIG-012 | interlocking-7 | v5 | 100.1 | percent-tests | current |
| SIG-013 | crossing-12 | v5 | 102.0 | percent-tests | current |
| SIG-014 | block-4 | v5 | 100.8 | percent-tests | current |
| SIG-015 | dispatcher-link | v5 | 99.6 | percent-tests | current |
| SIG-016 | interlocking-7 | v5 | 101.5 | percent-tests | current |
| SIG-017 | crossing-12 | v5 | 100.3 | percent-tests | current |
| SIG-018 | block-4 | v5 | 99.1 | percent-tests | current |
| SIG-019 | dispatcher-link | v5 | 101.0 | percent-tests | superseded |
| SIG-020 | interlocking-7 | v5 | 99.8 | percent-tests | current |
| SIG-021 | crossing-12 | v5 | 101.7 | percent-tests | current |
| SIG-022 | block-4 | v6 | 100.5 | percent-tests | current |
| SIG-023 | dispatcher-link | v6 | 99.3 | percent-tests | current |
| SIG-024 | interlocking-7 | v6 | 101.2 | percent-tests | current |
| SIG-025 | crossing-12 | v6 | 100.0 | percent-tests | current |
| SIG-026 | block-4 | v6 | 101.9 | percent-tests | current |
| SIG-027 | dispatcher-link | v6 | 100.7 | percent-tests | current |
| SIG-028 | interlocking-7 | v6 | 99.5 | percent-tests | current |
| SIG-029 | crossing-12 | v6 | 101.4 | percent-tests | current |
| SIG-030 | block-4 | v6 | 100.2 | percent-tests | current |
| SIG-031 | dispatcher-link | v6 | 99.0 | percent-tests | current |
| SIG-032 | interlocking-7 | v6 | 100.9 | percent-tests | current |
| SIG-033 | crossing-12 | v7 | 99.7 | percent-tests | current |
| SIG-034 | block-4 | v7 | 101.6 | percent-tests | current |
| SIG-035 | dispatcher-link | v7 | 100.4 | percent-tests | current |
| SIG-036 | interlocking-7 | v7 | 99.2 | percent-tests | current |
| SIG-037 | crossing-12 | v7 | 101.1 | percent-tests | current |
| SIG-038 | block-4 | v7 | 99.9 | percent-tests | superseded |
| SIG-039 | dispatcher-link | v7 | 101.8 | percent-tests | current |
| SIG-040 | interlocking-7 | v7 | 100.6 | percent-tests | current |
| SIG-041 | crossing-12 | v7 | 99.4 | percent-tests | current |
| SIG-042 | block-4 | v7 | 101.3 | percent-tests | current |
| SIG-043 | dispatcher-link | v7 | 100.1 | percent-tests | current |
| SIG-044 | interlocking-7 | v8 | 102.0 | percent-tests | current |
| SIG-045 | crossing-12 | v8 | 100.8 | percent-tests | current |
| SIG-046 | block-4 | v8 | 99.6 | percent-tests | current |
| SIG-047 | dispatcher-link | v8 | 101.5 | percent-tests | current |
| SIG-048 | interlocking-7 | v8 | 100.3 | percent-tests | current |
| SIG-049 | crossing-12 | v8 | 99.1 | percent-tests | current |
| SIG-050 | block-4 | v8 | 101.0 | percent-tests | current |
| SIG-051 | dispatcher-link | v8 | 99.8 | percent-tests | current |
| SIG-052 | interlocking-7 | v8 | 101.7 | percent-tests | current |
| SIG-053 | crossing-12 | v8 | 100.5 | percent-tests | current |
| SIG-054 | block-4 | v8 | 99.3 | percent-tests | current |
| SIG-055 | dispatcher-link | v9 | 101.2 | percent-tests | current |
| SIG-056 | interlocking-7 | v9 | 100.0 | percent-tests | current |
| SIG-057 | crossing-12 | v9 | 101.9 | percent-tests | superseded |
| SIG-058 | block-4 | v9 | 100.7 | percent-tests | current |
| SIG-059 | dispatcher-link | v9 | 99.5 | percent-tests | current |
| SIG-060 | interlocking-7 | v9 | 101.4 | percent-tests | current |
| SIG-061 | crossing-12 | v9 | 100.2 | percent-tests | current |
| SIG-062 | block-4 | v9 | 99.0 | percent-tests | current |
| SIG-063 | dispatcher-link | v9 | 100.9 | percent-tests | current |

## Decision constraints

Preserve percent versus probability, critical-vector completeness, train count, seconds, and staleness.
State the fail-safe route and evidence required before removing manual protection.
