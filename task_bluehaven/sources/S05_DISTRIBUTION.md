# Distribution hydraulics, pressure zones, and isolation effects

## Frozen findings

Zones A and B share the East trunk. Closing valve V-17 isolates the suspected plume but lowers Zone B hospital pressure below the 28 psi operational floor unless booster P-4 is running.
Zone C can backfeed B at 3.1 megaliters per day, but only after two cross-connection samples pass. Zone D cannot backfeed without reversing an unprotected industrial connection.
Pressure below 20 psi creates an intrusion risk and independently sustains the boil-water order even if treatment samples are clean.

## Governing relationships

The contamination isolation in S02, plant output in S04, hospital demand in S07, and generator state in S06 form one hydraulic decision.
A valve or pump mutation makes any prior pressure and sampling check stale for the new candidate.

## Operational evidence

| record | asset/zone | revision | measure | unit | status |
|---|---|---|---:|---|---|
| HYD-000 | Zone-A | r2 | 27.0 | psi | hold |
| HYD-001 | Zone-B | r2 | 27.7 | psi | current |
| HYD-002 | Zone-C | r2 | 28.4 | psi | current |
| HYD-003 | Zone-D | r2 | 29.1 | psi | current |
| HYD-004 | East-trunk | r2 | 29.8 | psi | current |
| HYD-005 | Zone-A | r2 | 27.4 | psi | current |
| HYD-006 | Zone-B | r2 | 28.1 | psi | current |
| HYD-007 | Zone-C | r2 | 28.8 | psi | current |
| HYD-008 | Zone-D | r2 | 29.5 | psi | current |
| HYD-009 | East-trunk | r2 | 27.1 | psi | current |
| HYD-010 | Zone-A | r2 | 27.8 | psi | current |
| HYD-011 | Zone-B | r2 | 28.5 | psi | current |
| HYD-012 | Zone-C | r2 | 29.2 | psi | current |
| HYD-013 | Zone-D | r2 | 29.9 | psi | hold |
| HYD-014 | East-trunk | r2 | 27.5 | psi | current |
| HYD-015 | Zone-A | r2 | 28.2 | psi | current |
| HYD-016 | Zone-B | r3 | 28.9 | psi | current |
| HYD-017 | Zone-C | r3 | 29.6 | psi | current |
| HYD-018 | Zone-D | r3 | 27.2 | psi | current |
| HYD-019 | East-trunk | r3 | 27.9 | psi | current |
| HYD-020 | Zone-A | r3 | 28.6 | psi | current |
| HYD-021 | Zone-B | r3 | 29.3 | psi | current |
| HYD-022 | Zone-C | r3 | 30.0 | psi | current |
| HYD-023 | Zone-D | r3 | 27.6 | psi | current |
| HYD-024 | East-trunk | r3 | 28.3 | psi | current |
| HYD-025 | Zone-A | r3 | 29.0 | psi | current |
| HYD-026 | Zone-B | r3 | 29.7 | psi | hold |
| HYD-027 | Zone-C | r3 | 27.3 | psi | current |
| HYD-028 | Zone-D | r3 | 28.0 | psi | current |
| HYD-029 | East-trunk | r3 | 28.7 | psi | current |
| HYD-030 | Zone-A | r3 | 29.4 | psi | current |
| HYD-031 | Zone-B | r3 | 27.0 | psi | current |
| HYD-032 | Zone-C | r4 | 27.7 | psi | current |
| HYD-033 | Zone-D | r4 | 28.4 | psi | current |
| HYD-034 | East-trunk | r4 | 29.1 | psi | current |
| HYD-035 | Zone-A | r4 | 29.8 | psi | current |
| HYD-036 | Zone-B | r4 | 27.4 | psi | current |
| HYD-037 | Zone-C | r4 | 28.1 | psi | current |
| HYD-038 | Zone-D | r4 | 28.8 | psi | current |
| HYD-039 | East-trunk | r4 | 29.5 | psi | hold |
| HYD-040 | Zone-A | r4 | 27.1 | psi | current |
| HYD-041 | Zone-B | r4 | 27.8 | psi | current |
| HYD-042 | Zone-C | r4 | 28.5 | psi | current |
| HYD-043 | Zone-D | r4 | 29.2 | psi | current |
| HYD-044 | East-trunk | r4 | 29.9 | psi | current |
| HYD-045 | Zone-A | r4 | 27.5 | psi | current |
| HYD-046 | Zone-B | r4 | 28.2 | psi | current |
| HYD-047 | Zone-C | r4 | 28.9 | psi | current |

## Decision constraints

Name valve, pump, pressure, sampling, and backfeed observations for every switch.
Do not assume treatment output reaches customers without a current hydraulic check.
