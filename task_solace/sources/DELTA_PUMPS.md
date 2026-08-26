# Pump capacity, sequencing, and cavitation constraints

## Frozen findings

The treatment works can supply 18 million gallons per day, but the shared transmission main is capped at 14.5 MGD. Pump nameplate capacities cannot be summed into usable system flow.
The latest inspected configuration sustained 12.8 MGD after fire-flow and hospital reserve. A higher stage requires a current candidate-bound pump and pressure test.
Restoration may advance through 10, 30, 60, and 100 percent demand stages only after two thirty-minute windows meet pressure, turbidity, power, and storage gates.

## Governing relationships

BASTION supplies pressure limits, ECHO supplies feeder headroom, and FALCON supplies treatment output. All three constrain DELTA sequencing.
A pump, valve, main allocation, generator, or treatment-train change makes prior capacity evidence stale.

## Operational evidence

| record | asset/zone | version | measure | unit | status |
|---|---|---|---:|---|---|
| PMP-000 | pump-1 | v2 | 18.0 | million-gallons-day | superseded |
| PMP-001 | pump-2 | v2 | 19.3 | million-gallons-day | current |
| PMP-002 | booster-east | v2 | 20.6 | million-gallons-day | current |
| PMP-003 | booster-west | v2 | 18.8 | million-gallons-day | current |
| PMP-004 | pump-1 | v2 | 20.1 | million-gallons-day | current |
| PMP-005 | pump-2 | v2 | 18.3 | million-gallons-day | current |
| PMP-006 | booster-east | v2 | 19.6 | million-gallons-day | current |
| PMP-007 | booster-west | v2 | 20.9 | million-gallons-day | current |
| PMP-008 | pump-1 | v2 | 19.1 | million-gallons-day | current |
| PMP-009 | pump-2 | v2 | 20.4 | million-gallons-day | current |
| PMP-010 | booster-east | v2 | 18.6 | million-gallons-day | current |
| PMP-011 | booster-west | v2 | 19.9 | million-gallons-day | current |
| PMP-012 | pump-1 | v2 | 18.1 | million-gallons-day | current |
| PMP-013 | pump-2 | v2 | 19.4 | million-gallons-day | current |
| PMP-014 | booster-east | v3 | 20.7 | million-gallons-day | current |
| PMP-015 | booster-west | v3 | 18.9 | million-gallons-day | current |
| PMP-016 | pump-1 | v3 | 20.2 | million-gallons-day | current |
| PMP-017 | pump-2 | v3 | 18.4 | million-gallons-day | current |
| PMP-018 | booster-east | v3 | 19.7 | million-gallons-day | current |
| PMP-019 | booster-west | v3 | 21.0 | million-gallons-day | superseded |
| PMP-020 | pump-1 | v3 | 19.2 | million-gallons-day | current |
| PMP-021 | pump-2 | v3 | 20.5 | million-gallons-day | current |
| PMP-022 | booster-east | v3 | 18.7 | million-gallons-day | current |
| PMP-023 | booster-west | v3 | 20.0 | million-gallons-day | current |
| PMP-024 | pump-1 | v3 | 18.2 | million-gallons-day | current |
| PMP-025 | pump-2 | v3 | 19.5 | million-gallons-day | current |
| PMP-026 | booster-east | v3 | 20.8 | million-gallons-day | current |
| PMP-027 | booster-west | v3 | 19.0 | million-gallons-day | current |
| PMP-028 | pump-1 | v4 | 20.3 | million-gallons-day | current |
| PMP-029 | pump-2 | v4 | 18.5 | million-gallons-day | current |
| PMP-030 | booster-east | v4 | 19.8 | million-gallons-day | current |
| PMP-031 | booster-west | v4 | 18.0 | million-gallons-day | current |
| PMP-032 | pump-1 | v4 | 19.3 | million-gallons-day | current |
| PMP-033 | pump-2 | v4 | 20.6 | million-gallons-day | current |
| PMP-034 | booster-east | v4 | 18.8 | million-gallons-day | current |
| PMP-035 | booster-west | v4 | 20.1 | million-gallons-day | current |
| PMP-036 | pump-1 | v4 | 18.3 | million-gallons-day | current |
| PMP-037 | pump-2 | v4 | 19.6 | million-gallons-day | current |
| PMP-038 | booster-east | v4 | 20.9 | million-gallons-day | superseded |
| PMP-039 | booster-west | v4 | 19.1 | million-gallons-day | current |
| PMP-040 | pump-1 | v4 | 20.4 | million-gallons-day | current |
| PMP-041 | pump-2 | v4 | 18.6 | million-gallons-day | current |

## Decision constraints

Preserve shared capacity, observed flow, stage sequence, windows, and stale conditions.
Do not infer public-health clearance from hydraulic capacity.
